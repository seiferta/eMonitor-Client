import os
currentDir = "d:/data/python/ffh/client/"
a = Analysis(
    [#os.path.join(HOMEPATH,'support\\_mountzlib.py'),
        # os.path.join(HOMEPATH,'support\\useUnicode.py'),
         os.path.normpath(os.path.join(currentDir, 'mclient.py')),
        # os.path.normpath(os.path.join(currentDir, 'importantLib.py')),
        # add the files you want PyInstaller to analyse the "import" statements
        # to detect the libraries to include
    ],
     pathex=['D:\\data\\python\\pyinstaller-2.0']
)
pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=1,
          name=os.path.join('build\\pyi.win32\\build_output', 'mclient.exe'),
          debug=False,
          strip=False,
          upx=True,
          console=False,
          icon = 'd:/data/python/ffh/client/computer.ico',)
coll = COLLECT( exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               name=os.path.join('dist', 'dist_output'))
