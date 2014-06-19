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

outXls = P.outdir + "/SystemService.xls"

SystemSerivceList=[]
SystemSerivceDict={}


def initWorkbook(style, style_title,list, Dict,wb=0):
    if wb==0:
        _wb = Workbook()
    else:
        _wb=wb
    _ws1 = _wb.add_sheet(u'5.6 SystemServices')

    _ws1.write(0, 0, u'System Service', style_title) 
    _ws1.write(0, 1, u'Type', style_title)
    _ws1.write(0, 2, u'Sensitive Custom OEM Service', style_title) 
    _ws1.write(0, 3, u'Description', style_title) 

    i=0

    for key in list:
		i=i+1
		if Dict.has_key(key.lower()):
			_ws1.write(i, 0, key, style)
			_ws1.write(i, 1, Dict[key.lower()][1], style)
			_ws1.write(i, 2, Dict[key.lower()][2], style)
			_ws1.write(i, 3, Dict[key.lower()][3], style)
		else:
			_ws1.write(i, 0, key, style)
			_ws1.write(i, 1, 'OEM supplied', style)
			_ws1.write(i, 2, 'yes', style)
			_ws1.write(i, 3, '', style)
    
    _ws1.col(0).width = 8000
    _ws1.col(1).width = 6000
    _ws1.col(2).width = 7000
    _ws1.col(3).width = 12000

    if wb==0:
        _wb.save(outXls)
        print "Generate xls table successed!! --> %s" % outXls 

def Output(_wb):
    #P.prepareFilesFromPhone()
    os.system("adb shell service list > %s" % (P.SystemServiceTxt))
    f = open(P.SystemServiceTxt, 'r')
    f.readline()
    while True:
    	line=f.readline()
    	if not line:
    		break
    	if line.find(':') > -1:
    		#print line
    		idx1 = line.find(':')
    		key=line[:idx1]
    		idx1=key.index('	')
    		key=key[idx1:]
    		key=key.strip()
    		SystemSerivceList.append(key)
    		#print key

    if not os.path.exists(P.EmuListPath):
        print "Please copy emu android manifest running this script! Directory path is:\n" +     EmuListPath
        return
    else:
        #protectedBroadcastDict = getProtectedBroadcastDict(P.ProtectedBroadcastTxt,P.emuProtectedBroadcastTxt)
		DictExcel = xlrd.open_workbook(P.DictXls)
		#print DictExcel.sheet_names()

		SystemServiceSheet = DictExcel.sheet_by_name(u'systemservice')

		for rownum in range(SystemServiceSheet.nrows):
	    	#print SystemServiceSheet.row_values(rownum)
			key=SystemServiceSheet.row(rownum)[0].value.lower()
			#print key
			if not SystemSerivceDict.has_key(key):
				SystemSerivceDict[key]=SystemServiceSheet.row_values(rownum)
		
		style = P.setStyles(False)
		style_title = P.setStyles(True)
		initWorkbook(style, style_title, SystemSerivceList,SystemSerivceDict,_wb)

def main():
    P.prepareFilesFromPhone()
    os.system("adb shell service list > %s" % (P.SystemServiceTxt))
    f = open(P.SystemServiceTxt, 'r')
    f.readline()
    while True:
    	line=f.readline()
    	if not line:
    		break
    	if line.find(':') > -1:
    		#print line
    		idx1 = line.find(':')
    		key=line[:idx1]
    		idx1=key.index('	')
    		key=key[idx1:]
    		key=key.strip()
    		SystemSerivceList.append(key)
    		#print key

    if not os.path.exists(P.EmuListPath):
        print "Please copy emu android manifest running this script! Directory path is:\n" +     EmuListPath
        return
    else:
        #protectedBroadcastDict = getProtectedBroadcastDict(P.ProtectedBroadcastTxt,P.emuProtectedBroadcastTxt)
		DictExcel = xlrd.open_workbook(P.DictXls)
		#print DictExcel.sheet_names()

		SystemServiceSheet = DictExcel.sheet_by_name(u'systemservice')

		for rownum in range(SystemServiceSheet.nrows):
	    	#print SystemServiceSheet.row_values(rownum)
			key=SystemServiceSheet.row(rownum)[0].value
			#print key
			if not SystemSerivceDict.has_key(key):
				SystemSerivceDict[key]=SystemServiceSheet.row_values(rownum)
		
		style = P.setStyles(False)
		style_title = P.setStyles(True)
		initWorkbook(style, style_title, SystemSerivceList,SystemSerivceDict)

if __name__ == '__main__':
    main()
