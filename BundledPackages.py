#!/usr/bin/python
#Output Bundled Packages Excel Table
#ying.tan@tcl.com

import os
import sys
import re
import time
import shutil
import codecs
from PyExcelerator import *
import FilterSensitiveContentProvider as P

outXls = P.outdir + "/out2.xls"
usesProtectionLevelTxt = P.tempdir + "/usesProtectionLevel.txt"
protectionLevelTxt = P.tempdir + "/protectionLevel.txt"
# pkgPermissionDict = {}
# pkgUsesPermissionDict = {}

class Package:
    def __init__(self):
        self.name = ''
        self.location = ''
        self.apkname = ''
        self.source = ''
        self.packageUID = ''
        self.permission = []
        self.usesPermission = []

class Permission:
    def __init__(self):
        self.name = ''
        self.protectionLevel = ''

def setPkgStyle():
    pattern = Pattern()
    pattern.pattern = 4
    # pattern.pattern_fore_colour = 20
    # pattern.pattern_back_colour = 10
    al = Alignment()
    al.horz = Alignment.HORZ_LEFT
    al.vert = Alignment.VERT_CENTER
    style = XFStyle()
    style.pattern = pattern
    style.alignment = al
    return style

def genBundledPkgInfo(pkgPermissionDict, pkgUsesPermissionDict):
    outList = []

    print P.protectionLevelDict
    # print P.pathDict
    # print pkgPermissionDict
    # print pkgUsesPermissionDict
    for root,dirs,files in os.walk(P.ManifestListPath):
        for filespath in files:
            jrdfilepath = os.path.join(root,filespath)
            pkg = Package()
            manifestStr = P.getNodeByTag('manifest', jrdfilepath)
            name = P.getAttrValueByAttrTitle('package', manifestStr)
            shareUserId = P.getAttrValueByAttrTitle('android:sharedUserId', manifestStr).strip(' ')

            pkg.name = name
            if shareUserId == '':
                pkg.packageUID = 'system assigned'
            else:
                pkg.packageUID = shareUserId
            
            if P.pathDict.has_key(name):
                tmpStr = P.pathDict[name]
                idx = tmpStr.rfind('/')
                pkg.location = tmpStr[:idx]
                pkg.apkname = tmpStr[idx+1:]

            if pkgPermissionDict.has_key(filespath):
                for per in pkgPermissionDict[filespath]:
                    permission = Permission()
                    permission.name = per
                    print per
                    if P.protectionLevelDict.has_key(per):
                        permission.protectionLevel = P.protectionLevelDict[per]
                        print permission.protectionLevel
                    pkg.permission.append(permission)
 
            if pkgUsesPermissionDict.has_key(filespath):
                for per in pkgUsesPermissionDict[filespath]:
                    permission = Permission()
                    permission.name = per
                    if P.protectionLevelDict.has_key(per):
                        permission.protectionLevel = P.protectionLevelDict[per]
                    pkg.usesPermission.append(permission)

            outList.append(pkg)
    return outList

def genPkgAndPermssionDict(fIn):
    outdict = {}
    f = open(fIn, 'r')
    while True:
        line = f.readline()
        if not line:
            break
        if line.find('.xml:') > -1:
            idx1 = line.find('/') + 1
            idx2 = line.find(':')
            key = line[idx1:idx2]
            value = P.getAttrValueByAttrTitle('android:name', line)
            if not outdict.has_key(key):
                outdict[key] = []
            outdict[key].append(value)
    return outdict

def initWorkbook(style, style_title, style_pkg, list):
    _wb = Workbook()
    _ws1 = _wb.add_sheet(u'5.8 BundledPackages')

    _ws1.write(5, 0, u'Package No.', style_title) 
    _ws1.write(5, 1, u'Package, Permission or uses-permission', style_title)
    _ws1.write(5, 2, u'Package Name or Permission Name', style_title) 
    _ws1.write(5, 3, u'Package Purpose or Permission Purpose', style_title) 
    _ws1.write(5, 4, u'Protection Level of Permission', style_title) 
    _ws1.write(5, 5, u'Justification for this permission in this package', style_title) 
    _ws1.write(5, 6, u'Package Location', style_title) 
    _ws1.write(5, 7, u'apk file name', style_title) 
    _ws1.write(5, 8, u'Package UID', style_title) 
    _ws1.write(5, 9, u'Package Source', style_title)

    count = 0
    for pkg in list:
        i = list.index(pkg) + 6 + count

        _ws1.write(i, 0, list.index(pkg)+1, style_pkg)
        _ws1.write(i, 1, 'package', style_pkg)
        _ws1.write(i, 2, pkg.name, style_pkg)
        _ws1.write(i, 3, '', style_pkg)
        _ws1.write(i, 4, 'n/a (package)', style_pkg)
        _ws1.write(i, 5, '', style_pkg)
        _ws1.write(i, 6, pkg.location, style_pkg)
        _ws1.write(i, 7, pkg.apkname, style_pkg)
        _ws1.write(i, 8, pkg.packageUID, style_pkg)
        _ws1.write(i, 9, '', style_pkg)

        #print pkg.permission
        
        if pkg.permission:
            for p in pkg.permission:
                j = pkg.permission.index(p) + 1

                _ws1.write(i+j, 0, list.index(pkg)+1, style)
                _ws1.write(i+j, 1, 'permission', style)
                _ws1.write(i+j, 2, p.name, style)
                _ws1.write(i+j, 3, '', style)
                _ws1.write(i+j, 4, p.protectionLevel, style)
                _ws1.write(i+j, 5, '', style)
                _ws1.write(i+j, 6, pkg.location, style)
                _ws1.write(i+j, 7, pkg.apkname, style)
                _ws1.write(i+j, 8, pkg.packageUID, style)
                _ws1.write(i+j, 9, '', style)

            count += len(pkg.permission)

        if pkg.usesPermission:
            for up in pkg.usesPermission:
                k = pkg.usesPermission.index(up) + len(pkg.permission) + 1

                _ws1.write(i+k, 0, list.index(pkg)+1, style)
                _ws1.write(i+k, 1, 'uses-permission', style)
                _ws1.write(i+k, 2, up.name, style)
                _ws1.write(i+k, 3, '', style)
                _ws1.write(i+k, 4, up.protectionLevel, style)
                _ws1.write(i+k, 5, '', style)
                _ws1.write(i+k, 6, pkg.location, style)
                _ws1.write(i+k, 7, pkg.apkname, style)
                _ws1.write(i+k, 8, pkg.packageUID, style)
                _ws1.write(i+k, 9, '', style)

            count += len(pkg.usesPermission)

    
    for i in range(4, 9):
        _ws1.col(i).width = 8000 

    _ws1.col(2).width = 15000
    _ws1.col(3).width = 12000
    _ws1.col(6).width = 10000

    _wb.save(outXls)
    print "Generate xls table successed!! --> %s" % outXls

def generateProtectionLevelToProtectionLevelDict():
    protectionLevelDict = {}
    f = open(protectionLevelTxt, 'r')
    while True:
        line = f.readline()
        if not line:
            break
        if line.find('android:protectionLevel') > -1:
            value = P.getAttrValueByAttrTitle('android:protectionLevel', line)
            key = P.getAttrValueByAttrTitle('android:name', line)
            protectionLevelDict[key] = value 

    print protectionLevelDict
    return protectionLevelDict

def main():
    P.prepareFilesFromPhone()
    P.getProtectLevelFromManifest('permission', P.protectionLevelTxt)
    P.getProtectLevelFromManifest('uses-permission', usesProtectionLevelTxt)
    if not os.path.exists(P.EmuListPath):
        print "Please copy emu android manifest running this script! Directory path is:\n" +     EmuListPath
        return
    else:
        #P.prepareDirsAndDicts()
        P.getProtectLevelFromManifest('permission', protectionLevelTxt)
        P.generatePackageInstallationToPathDict()
        P.generateProtectionLevelToProtectionLevelDict()
        #print  generateProtectionLevelToProtectionLevelDict()

        pkgPermissionDict = genPkgAndPermssionDict(P.protectionLevelTxt)
        pkgUsesPermissionDict = genPkgAndPermssionDict(usesProtectionLevelTxt)

        outList = genBundledPkgInfo(pkgPermissionDict, pkgUsesPermissionDict)
        style = P.setStyles(False)
        style_title = P.setStyles(True)
        style_pkg = setPkgStyle()
        initWorkbook(style, style_title, style_pkg, outList)

if __name__ == '__main__':
    main()