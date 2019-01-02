import sys
import re
import os
import subprocess
import socket
import time
import getopt
import logging

from PyQt5.QtCore import Qt
from PyQt5 import QtCore, QtGui, QtWebKit, QtNetwork, QtWebKitWidgets, QtWidgets

try:
    opts, extraparams = getopt.getopt(sys.argv[1:], 'i:h:p:w')
except getopt.GetoptError as err:
    sys.exit(2)

ID = 1
ANY = "0.0.0.0"
MCAST_ADDR = "224.168.2.9"
MCAST_PORT = 1600
FULLWINDOW = 1
LOGLEVEL = 10  # debug, 40=error
web = None
VERSION = '0.4.1'
STARTPAGE = '<html>' \
            '<body style="background-color:#000;color:#fff">' \
            '<p style="text-align:center;color:silver;padding-top:50%;font-size:100%;font-family:Arial">eMonitor-Client<br/>ver. {}</p>' \
            '</body>' \
            '</html>'.format(VERSION)
BLANKPAGE = '<html><body style="background-color:#000;color:#fff"></body></html>'

for item in opts:
    if item[0] == '-i':
        ID = item[1]
    if item[0] == '-h':
        MCAST_ADDR = item[1]
    if item[0] == '-p':
        MCAST_PORT = item[1]
    if item[0] == '-w':
        FULLWINDOW = 0
    if item[0] == '-l':
        LOGLEVEL = item[1]

logging.basicConfig(filename='mclient.log', level=LOGLEVEL)
logger = logging.getLogger()


def getLastLoad():
    """
    analyse logfile for last called server
    :return: ip-address of server
    """
    if os.path.isfile('mclient.log'):
        for line in reversed(open('mclient.log', 'r').readlines()):
            if 'load' in line.rstrip() or 'reset' in line.rstrip():
                ip = re.findall(r'[0-9]+(?:\.[0-9]+){3}:[0-9]+', line.rstrip().split()[-1])
                if len(ip) == 0:
                    ip = re.findall(r'[0-9]+(?:\.[0-9]+){3}', line.rstrip().split()[-1])
                if len(ip) > 0:
                    return ip[0]
    return None


class AD_Listener(QtCore.QObject):
    message = QtCore.pyqtSignal(str)

    def __init__(self):
        QtCore.QObject.__init__(self)

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((ANY, MCAST_PORT))
        self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 255)

        self.sock.setsockopt(socket.IPPROTO_IP,
                                      socket.IP_ADD_MEMBERSHIP,
                                      socket.inet_aton(MCAST_ADDR) + socket.inet_aton(ANY))

        self.sock.setblocking(0)
        self.running = True
        logger.debug('mclient started')

    def loop(self):
        global ID, web
        logip = getLastLoad()
        logger.debug("mclient v {} for eMonitor started with id {}, waiting for events...".format(VERSION, ID))

        # init startpage
        if logip:
            self.sock.sendto('initneed', (MCAST_ADDR, MCAST_PORT))
            logger.debug("reload last source {}".format(logip))
            self.message.emit('http://{}/monitor/{}'.format(logip, ID))
        else:
            self.message.emit('http://{}/monitor/{}'.format(logip, ID))
            logger.debug("no source ip found.")

        while self.running:
            try:
                data, addr = self.sock.recvfrom(1024)
                ts = time.gmtime()
            except socket.error, e:
                pass
            else:
                logger.debug("%s:%s - %s: --> %s" % (addr[0], addr[1], time.strftime('%Y.%m.%d - %H:%M:%S', ts), data))
                data = data.split("|")
                print "addr", addr
                if len(data) > 1:
                    if data[0] in ['0', ID]:
                        if data[1] == "load":
                            self.sock.sendto('%s|load done' % ID, (addr[0], addr[1]))
                            if "{}" in data[2]:
                                self.message.emit(data[2].format(ID))
                            elif "%s" in data[2]:  # compatibility to old versions
                                self.message.emit(data[2] % ID)
                            else:
                                self.message.emit(data[2])
                            logger.debug('LOAD: {}'.format(data[2]))
                        if data[1] == "execute":
                            try:
                                subprocess.check_output('/home/pi/{}'.format(data[2]), stderr=subprocess.STDOUT, shell=True)
                                logger.debug('EXECUTE: {}'.format(data[2]))
                            except:
                                logger.error('EXECUTE: {}'.format(data[2]))

                        if data[1] == "reset":
                            self.message.emit('reset')
                            self.sock.sendto('{}|reset done'.format(ID), (addr[0], addr[1]))
                            self.message.emit(data[2].format(ID))
                            logger.debug('RESET')

                        if data[1] == "ping":
                            if not logip:
                                self.sock.sendto('{}|initneed'.format(ID), (addr[0], addr[1]))
                            else:
                                self.sock.sendto('{}|alive|{}'.format(ID, VERSION), (addr[0], addr[1]))
                            logger.debug('PING')

                        if data[1] == "changeid":
                            ID = int(data[2])
                            self.sock.sendto('{}|changedone'.format(ID), (addr[0], addr[1]))
                            web.setWindowTitle("eMonitor-Client id ({} - {})".format(ID), VERSION)
                            logger.debug('CHANGEID')

                        if data[1] == "getscripts":
                            scripts = [f for f in os.listdir('scripts') if os.path.isfile(os.path.join('scripts', f))]
                            self.sock.sendto('{}|scripts={}'.format(ID, '__'.join(scripts)), (addr[0], addr[1]))
            time.sleep(2)


class WebPage(QtWebKitWidgets.QWebPage):
    def __init__(self):
        QtWebKitWidgets.QWebPage.__init__(self)

    def userAgentForUrl(self, url):
        return "mClient/{} (X11; raspberry arm; {}) mClient/2016 mClient/{}".format(VERSION, VERSION, VERSION)


class AD_Window(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        QtWidgets.QMainWindow.__init__(self, parent)

        self.request = None
        self.startpage = STARTPAGE
        self.blankpage = BLANKPAGE
        self.webView = QtWebKitWidgets.QWebView()
        self.webView.setPage(WebPage())

        self.webView.setAttribute(Qt.WA_TranslucentBackground, True)
        self.webView.setAttribute(Qt.WA_OpaquePaintEvent, True)

        # self.webView.setTextSizeMultiplier(2.0)
        settings = self.webView.settings()
        settings.setAttribute(QtWebKit.QWebSettings.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(QtWebKit.QWebSettings.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(QtWebKit.QWebSettings.LocalContentCanAccessFileUrls, True)
        settings.setAttribute(QtWebKit.QWebSettings.LocalStorageEnabled, True)
        settings.setAttribute(QtWebKit.QWebSettings.AutoLoadImages, True)

        self.setCentralWidget(self.webView)
        palette = self.centralWidget().palette()
        palette.setBrush(QtGui.QPalette.Base, Qt.black)
        self.centralWidget().setPalette(palette)

        self.webView.setHtml(self.startpage)
        self.setWindowTitle("eMonitor-Client id ({}) - {}".format(ID, VERSION))

        self.thread = QtCore.QThread()
        self.ad_listener = AD_Listener()
        self.ad_listener.moveToThread(self.thread)

        self.thread.started.connect(self.ad_listener.loop)
        self.ad_listener.message.connect(self.signal_received)
        QtCore.QTimer.singleShot(0, self.thread.start)

    def signal_received(self, message):
        logger.debug(QtCore.qVersion())
        try:
            if message == "reset":
                self.webView.setHtml(self.blankpage)
            else:
                self.request = QtNetwork.QNetworkRequest()
                self.request.setRawHeader("Content-Type", QtCore.QByteArray('application/octet-stream'))
                self.request.setRawHeader("Accept-Language", QtCore.QByteArray("de, *"))
                self.request.setUrl(QtCore.QUrl(message))
                self.webView.load(self.request)

                # old version without user-agent
                # self.webView.load(QtCore.QUrl(message))
        except:
            self.webView.setHtml(self.startpage)
            logger.error('receive: {}'.format(message))

    def closeEvent(self, event):
        logger.debug('close')
        self.ad_listener.running = False
        self.thread.quit()
        self.thread.wait()


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    web = AD_Window()

    if not os.path.exists('scripts'):
        os.makedirs('scripts')

    if FULLWINDOW == 1:
        web.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        web.showFullScreen()
    else:

        web.show()
    sys.exit(app.exec_())
