#!/usr/bin/python
#Output Bundled Packages Excel Table
#ying.tan@tcl.com

import os
import sys
import re
import time
import shutil
import codecs

pmlistPath='./pmlist.txt'

def main():
	if len(sys.argv) < 2:
		print "The tempapk directory can not be empty.\n"
	else:
		lineCount=0
		file = open(pmlistPath, 'r')
		while True:
			line = file.readline()
			if not line:
				print 'Total' + str(lineCount) + 'APK.'
				break
			
			lineCount += 1

			slashIndex = line.find('/')
			if slashIndex > -1:
				equalIndex = line.rfind('=')
				if equalIndex > -1:
					fullPath = line[slashIndex:equalIndex]
					print fullPath
					packageName = line[equalIndex+1:-2]
					print packageName
					print sys.argv[1] + '/' + packageName+ '.apk'
					os.system('adb pull %s %s' % (fullPath , sys.argv[1] + '/' + packageName+ '.apk' ))

if __name__ == '__main__':
    main()