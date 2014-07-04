#!/usr/bin/python
#Output ProtectedBroadcast Excel Table
#jinshi.song

import os
import sys
import re
import time
import shutil
import codecs
from PyExcelerator import *
import FilterSensitiveContentProvider as P
import xlrd
import ProtectedBroadcast as PB
import SystemService as SS
import BundledPackages as BP

outXls = P.outdir + "/AndroidSecurity_"+sys.argv[1]+time.strftime('_%Y%m%d%H%M%S')+".xls"


def main():
    P.prepareFilesFromPhone()
    if not os.path.exists(P.EmuListPath):
        print "Please copy emu android manifest running this script! Directory path is:\n" +     P.EmuListPath
        return
    else:
        P.prepareDirsAndDicts()
        _wb = Workbook()
        PB.Output(_wb)

        P.Output(_wb)
        SS.Output(_wb)
        BP.Output(_wb)
        _wb.save(outXls)
        print "Generate xls table successed!! --> %s" % outXls

if __name__ == '__main__':
    main()
