import os
import sys

flags = "--clean -F -c"
hidden = "--hidden-import wx.adv --hidden-import wx.html --hidden-import wx.xml"
icon = "--icon=Resources\\Cecilia5.ico"

if sys.version_info < (3, 9):
    raise RuntimeError("Python 3.9 or newer is required to build Cecilia5.")

cmd = f'"{sys.executable}" -m PyInstaller {flags} {hidden} {icon} "Cecilia5.py"'
os.system(cmd)

os.system("git checkout-index -a -f --prefix=Cecilia5_Win/")
os.system("copy dist\\Cecilia5.exe Cecilia5_Win /Y")
os.system("rmdir /Q /S Cecilia5_Win\\scripts")
os.system("rmdir /Q /S Cecilia5_Win\\doc-en")
os.system("rmdir /Q /S Cecilia5_Win\\images")
os.system("rmdir /Q /S Cecilia5_Win\\release_notes")
os.remove("Cecilia5_Win/Cecilia5.py")
os.remove("Cecilia5_Win/.gitignore")
os.remove("Cecilia5_Win/setup.py")
os.remove("Cecilia5_Win/Resources/Cecilia5.icns")
os.remove("Cecilia5_Win/Resources/CeciliaFileIcon5.icns")
os.remove("Cecilia5.spec")
os.system("rmdir /Q /S build")
os.system("rmdir /Q /S dist")
for f in os.listdir(os.getcwd()):
    if f.startswith("warn") or f.startswith("logdict"):
        os.remove(f)
