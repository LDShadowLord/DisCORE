#!C:\Users\ldsha\source\repos\DisCORE\DisCORE\DisCORE-FattyEnvironment\Scripts\python.exe
# EASY-INSTALL-ENTRY-SCRIPT: 'FanFicFare==3.25.0','console_scripts','fanficfare'
__requires__ = 'FanFicFare==3.25.0'
import re
import sys
from pkg_resources import load_entry_point

if __name__ == '__main__':
    sys.argv[0] = re.sub(r'(-script\.pyw?|\.exe)?$', '', sys.argv[0])
    sys.exit(
        load_entry_point('FanFicFare==3.25.0', 'console_scripts', 'fanficfare')()
    )