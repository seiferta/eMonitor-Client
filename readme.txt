
http://www.datenreise.de/raspberry-pi-stabiler-24-7-dauerbetrieb/

ssh pi@192.168.1.104 'DISPLAY=:0 python /home/pi/client/mclient.py'
===============
http://strobelstefan.org
===============
=mauszeiger entfernen=

	sudo apt-get install unclutter
	unclutter -display 0:0 -noevents -grab
====================================

=nagios=

sudo apt-get install nagios3

> username: nagiosadmin
> password: nagios

http://client1/nagios3
===================================

=bildschirm schwarz=

Ich musste Datei /etc/lightdm/lightdm.conf editiert und dort einen Eintrag in der Kategorie [SeatDefaults] eingetragen.

xserver-command=X -s 0 -dpms
===================================

=mailserver=

apt-get install ssmtp heirloom-mailx

/etc/ssmtp/ssmtp.conf

# The person who gets all mail for userids &lt; 1000
 # Make this empty to disable rewriting.
 root=postmaster

 # The place where the mail goes. The actual machine name is required no 
 # MX records are consulted. Commonly mailhosts are named mail.domain.com
 mailhub=MyMailServerName

 # Where will the mail seem to come from?
 rewriteDomain=MyMailServerDomain
 # The full hostname
 hostname=raspberry

 # Are users allowed to set their own From: address?
 # YES - Allow the user to specify their own From: address
 # NO - Use the system generated From: address
 #FromLineOverride=YES

 # Use SSL/TLS before starting negotiation 
 UseTLS=Yes
 UseSTARTTLS=Yes

 # Username/Password
 AuthUser=MyMailUsername
 AuthPass=SecretPassword

echo "mail from your raspberry" | mail -s "Testmail" emonitor@mnet-online.de
echo "Test" | sendmail -v emonitor@mnet-online.de
