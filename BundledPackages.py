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
import xlrd

outXls = P.outdir + "/BundledPackages.xls"
usesProtectionLevelTxt = P.tempdir + "/usesProtectionLevel.txt"
protectionLevelTxt = P.tempdir + "/protectionLevel.txt"

#add by jinshi.song 
BundlePackageDict={}

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

def genBundledPkgInfo(pkgPermissionDict, pkgUsesPermissionDict, pkgSourceDict, pkgProtectionLevelDict):
    outList = []

    #print pkgSourceDict
    #print P.protectionLevelDict
    #print P.pathDict
    #print pkgPermissionDict
    #print pkgUsesPermissionDict
    #print pkgProtectionLevelDict
    #pkgPermissionDict = sorted(pkgPermissionDict.items(), key=lambda e:e[0], reverse=False)

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

            if pkgSourceDict.has_key(name):
                pkg.source = pkgSourceDict[name]

            if pkgPermissionDict.has_key(filespath):
                for per in pkgPermissionDict[filespath]:
                    permission = Permission()
                    permission.name = per
                    if pkgProtectionLevelDict[filespath].has_key(per):
                        permission.protectionLevel = checkProtectionLevelValue(pkgProtectionLevelDict[filespath][per])
                    else:
                        permission.protectionLevel = 'Not Found'
                    pkg.permission.append(permission)
 
            if pkgUsesPermissionDict.has_key(filespath):
                for per in pkgUsesPermissionDict[filespath]:
                    permission = Permission()
                    permission.name = per
                    tmpProtectionLevel = ''
                    if pkgProtectionLevelDict.has_key(filespath):
                        if pkgProtectionLevelDict[filespath].has_key(per):
                            #permission.protectionLevel = checkProtectionLevelValue()
                            tmpProtectionLevel = pkgProtectionLevelDict[filespath][per]
                        elif P.protectionLevelDict.has_key(per):
                            #permission.protectionLevel = checkProtectionLevelValue(P.protectionLevelDict[per])
                            tmpProtectionLevel = P.protectionLevelDict[per]
                            #print '@@@  ' + tmpProtectionLevel
                        else:
                            tmpProtectionLevel = 'Not Found'                       
                    elif P.protectionLevelDict.has_key(per):
                        #permission.protectionLevel = checkProtectionLevelValue(P.protectionLevelDict[per])
                        tmpProtectionLevel = P.protectionLevelDict[per]
                        #print '@@@  ' + tmpProtectionLevel
                    else:
                        tmpProtectionLevel = 'Not Found'
                    permission.protectionLevel = checkProtectionLevelValue(tmpProtectionLevel)
                    pkg.usesPermission.append(permission)

            outList.append(pkg)
    return outList

def checkProtectionLevelValue(string):
    string = string.lower()
    result = ''
    if string.find('normal') > -1:
        result = '0 - normal'
    elif string.find('dangerous') > -1:
        result = '1 - dangerous'
    elif string.find('signatureorsystem') > -1:
        result = '3 - signatureOrSystem'
    elif string.find('signature') > -1:
        result = '2 - signature'
    else:
        result = 'Not Found'
    return result

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

def genPkgPermissionProtectionLevelDict(fIn):
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
            permissionName = P.getAttrValueByAttrTitle('android:name', line)
            protectionLevel = P.getAttrValueByAttrTitle('android:protectionLevel', line)
            if not protectionLevel:
                protectionLevel = 'Not Found'             
            if not outdict.has_key(key):
                outdict[key] = {}
            outdict[key][permissionName] = protectionLevel
    return outdict

def initWorkbook(style, style_title, style_pkg, list,Dict,wb=0):
    if wb==0:
        _wb = Workbook()
    else:
        _wb=wb
    _ws1 = _wb.add_sheet(u'5.8 BundledPackages')

    _ws1.write(0, 0, u'Package No.', style_title) 
    _ws1.write(0, 1, u'Package, Permission or uses-permission', style_title)
    _ws1.write(0, 2, u'Package Name or Permission Name', style_title) 
    _ws1.write(0, 3, u'Package Purpose or Permission Purpose', style_title) 
    _ws1.write(0, 4, u'Protection Level of Permission', style_title) 
    _ws1.write(0, 5, u'Justification for this permission in this package', style_title) 
    _ws1.write(0, 6, u'Package Location', style_title) 
    _ws1.write(0, 7, u'apk file name', style_title) 
    _ws1.write(0, 8, u'Package UID', style_title) 
    _ws1.write(0, 9, u'Package Source', style_title)

    count = 0
    for pkg in list:
        i = list.index(pkg) + 1 + count

        _ws1.write(i, 0, list.index(pkg)+1, style_pkg)
        _ws1.write(i, 1, 'package', style_pkg)
        _ws1.write(i, 2, pkg.name, style_pkg)
        if Dict.has_key(pkg.name):
            _ws1.write(i, 3, Dict[pkg.name][2], style_pkg)
        else:
            _ws1.write(i, 3, '#N/A', style_pkg)
        _ws1.write(i, 4, 'n/a (package)', style_pkg)
        if Dict.has_key(pkg.name):
            _ws1.write(i, 5, Dict[pkg.name][3], style_pkg)
        else:
            _ws1.write(i, 5, '#N/A', style_pkg)
        _ws1.write(i, 6, pkg.location, style_pkg)
        _ws1.write(i, 7, pkg.apkname, style_pkg)
        _ws1.write(i, 8, pkg.packageUID, style_pkg)
        _ws1.write(i, 9, pkg.source, style_pkg)

        #print pkg.permission
        
        if pkg.permission:
            for p in pkg.permission:
                j = pkg.permission.index(p) + 1

                _ws1.write(i+j, 0, list.index(pkg)+1, style)
                _ws1.write(i+j, 1, 'permission', style)
                _ws1.write(i+j, 2, p.name, style)
                if Dict.has_key(p.name):
                    _ws1.write(i+j, 3, Dict[p.name][2], style)
                else:
                    _ws1.write(i+j, 3, '#N/A', style)
                
                _ws1.write(i+j, 4, p.protectionLevel, style)
                if Dict.has_key(p.name):
                    _ws1.write(i+j, 5, Dict[p.name][3], style)
                else:
                    _ws1.write(i+j, 5, '#N/A', style)
                _ws1.write(i+j, 6, pkg.location, style)
                _ws1.write(i+j, 7, pkg.apkname, style)
                _ws1.write(i+j, 8, pkg.packageUID, style)
                _ws1.write(i+j, 9, pkg.source, style)

            count += len(pkg.permission)

        if pkg.usesPermission:
            for up in pkg.usesPermission:
                k = pkg.usesPermission.index(up) + len(pkg.permission) + 1

                _ws1.write(i+k, 0, list.index(pkg)+1, style)
                _ws1.write(i+k, 1, 'uses-permission', style)
                _ws1.write(i+k, 2, up.name, style)
                if Dict.has_key(up.name):
                    _ws1.write(i+k, 3, Dict[up.name][2], style)
                else:
                    _ws1.write(i+k, 3, '#N/A', style)
                _ws1.write(i+k, 4, up.protectionLevel, style)
                if Dict.has_key(up.name):
                    _ws1.write(i+k, 5, Dict[up.name][3], style)
                else:
                    _ws1.write(i+k, 5, '#N/A', style)
                _ws1.write(i+k, 6, pkg.location, style)
                _ws1.write(i+k, 7, pkg.apkname, style)
                _ws1.write(i+k, 8, pkg.packageUID, style)
                _ws1.write(i+k, 9, pkg.source, style)

            count += len(pkg.usesPermission)

    
    for i in range(4, 9):
        _ws1.col(i).width = 8000 

    _ws1.col(2).width = 15000
    _ws1.col(3).width = 12000
    _ws1.col(6).width = 10000

    if wb==0:
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

    #print protectionLevelDict
    return protectionLevelDict

def Output(_wb):
    #P.prepareFilesFromPhone()
    P.getProtectLevelFromManifest('permission ', P.protectionLevelTxt)
    P.getProtectLevelFromManifest('uses-permission', usesProtectionLevelTxt)
    if not os.path.exists(P.EmuListPath):
        print "Please copy emu android manifest running this script! Directory path is:\n" +     EmuListPath
        return
    else:

        #add by jinshi.song 
        DictExcel = xlrd.open_workbook(P.DictXls)
        #print DictExcel.sheet_names()
        BundlePackageSheet = DictExcel.sheet_by_name(u'bundlepackage')

        for rownum in range(BundlePackageSheet.nrows):
            #print BundlePackageSheet.row_values(rownum)
            key=BundlePackageSheet.row(rownum)[1].value
            #print key
            if not BundlePackageDict.has_key(key):
                BundlePackageDict[key]=BundlePackageSheet.row_values(rownum)
        #P.prepareDirsAndDicts()
        #P.getProtectLevelFromManifest('permission ', protectionLevelTxt)
        P.generatePackageInstallationToPathDict()
        P.generateProtectionLevelToProtectionLevelDict()

        pkgProtectionLevelDict = genPkgPermissionProtectionLevelDict(P.protectionLevelTxt)
        pkgPermissionDict = genPkgAndPermssionDict(P.protectionLevelTxt)
        pkgUsesPermissionDict = genPkgAndPermssionDict(usesProtectionLevelTxt)

        P.filterCustomOEM()
        pkgSourceDict = P.genPkgSourceDict(P.outList)
        #print pkgSourceDict

        outList = genBundledPkgInfo(pkgPermissionDict, pkgUsesPermissionDict, pkgSourceDict, pkgProtectionLevelDict)
        style = P.setStyles(False)
        style_title = P.setStyles(True)
        style_pkg = setPkgStyle()
        initWorkbook(style, style_title, style_pkg, outList,BundlePackageDict,_wb)

def main():
    P.prepareFilesFromPhone()
    P.getProtectLevelFromManifest('permission ', P.protectionLevelTxt)
    P.getProtectLevelFromManifest('uses-permission', usesProtectionLevelTxt)
    if not os.path.exists(P.EmuListPath):
        print "Please copy emu android manifest running this script! Directory path is:\n" +     EmuListPath
        return
    else:

        #add by jinshi.song 
        DictExcel = xlrd.open_workbook(P.DictXls)
        #print DictExcel.sheet_names()
        BundlePackageSheet = DictExcel.sheet_by_name(u'bundlepackage')

        for rownum in range(BundlePackageSheet.nrows):
            #print BundlePackageSheet.row_values(rownum)
            key=BundlePackageSheet.row(rownum)[1].value
            #print key
            if not BundlePackageDict.has_key(key):
                BundlePackageDict[key]=BundlePackageSheet.row_values(rownum)
        #P.prepareDirsAndDicts()
        #P.getProtectLevelFromManifest('permission ', protectionLevelTxt)
        P.generatePackageInstallationToPathDict()
        P.generateProtectionLevelToProtectionLevelDict()

        pkgProtectionLevelDict = genPkgPermissionProtectionLevelDict(P.protectionLevelTxt)
        pkgPermissionDict = genPkgAndPermssionDict(P.protectionLevelTxt)
        pkgUsesPermissionDict = genPkgAndPermssionDict(usesProtectionLevelTxt)

        P.filterCustomOEM()
        pkgSourceDict = P.genPkgSourceDict(P.outList)
        #print pkgSourceDict

        outList = genBundledPkgInfo(pkgPermissionDict, pkgUsesPermissionDict, pkgSourceDict, pkgProtectionLevelDict)
        style = P.setStyles(False)
        style_title = P.setStyles(True)
        style_pkg = setPkgStyle()
        initWorkbook(style, style_title, style_pkg, outList,BundlePackageDict)

if __name__ == '__main__':
    main()