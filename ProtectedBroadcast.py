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

outXls = P.outdir + "/ProtectedBroadcast.xls"


def getProtectedBroadcastDict(fIn,fInEmu):
    outdict = {}
    emuDict={}
    f = open(fIn, 'r')
    fEmu = open(fInEmu, 'r')
    while True:
    	line=fEmu.readline()
    	if not line:
    		break
    	if line.find('.xml:') > -1:
            #idx1 = line.find('/') + 1
            #idx2 = line.find(':')
            #key = line[idx1:idx2]
            key = P.getAttrValueByAttrTitle('android:name', line)
            if not emuDict.has_key(key):
                emuDict[key] = 'YES'


    while True:
        line = f.readline()
        if not line:
            break
        if line.find('.xml:') > -1:
            #idx1 = line.find('/') + 1
            #idx2 = line.find(':')
            #key = line[idx1:idx2]
            key = P.getAttrValueByAttrTitle('android:name', line)
            if not outdict.has_key(key):
            	outdict[key]='NO'
                if emuDict.has_key(key):
                	outdict[key] = emuDict[key]
    return outdict

def initWorkbook(style, style_title, Dict):
    _wb = Workbook()
    _ws1 = _wb.add_sheet(u'5.1 ProtectedBroadcasts')

    _ws1.write(0, 0, u'Protected Broadcast', style_title) 
    _ws1.write(0, 1, u'AOSP?', style_title)
    _ws1.write(0, 2, u'Purpose', style_title) 
    _ws1.write(0, 3, u'Protected Broadcast Receivers', style_title) 

    i=0
    for key in Dict:
        i=i+1

        _ws1.write(i, 0, key, style)
        _ws1.write(i, 1, Dict[key], style)
        _ws1.write(i, 2, '', style)
        _ws1.write(i, 3, '', style)


    _ws1.col(0).width = 15000
    _ws1.col(3).width = 12000

    _wb.save(outXls)
    print "Generate xls table successed!! --> %s" % outXls

def main():
    P.prepareFilesFromPhone()
    #get ProtectedBroadcast From EmuManifestListPath --> emuProtectedBroadcastTxt
    P.grepTagToOutputByPath(P.EmuListPath,'protected-broadcast', P.emuProtectedBroadcastTxt)
    #get ProtectedBroadcast From ManifestListPath --> protectedBroadcastTxt
    P.grepTagToOutputByPath(P.ManifestListPath,'protected-broadcast', P.ProtectedBroadcastTxt)

    if not os.path.exists(P.EmuListPath):
        print "Please copy emu android manifest running this script! Directory path is:\n" +     EmuListPath
        return
    else:
        protectedBroadcastDict = getProtectedBroadcastDict(P.ProtectedBroadcastTxt,P.emuProtectedBroadcastTxt)

        style = P.setStyles(False)
        style_title = P.setStyles(True)
        initWorkbook(style, style_title, protectedBroadcastDict)

if __name__ == '__main__':
    main()

