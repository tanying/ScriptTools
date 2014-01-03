#!/usr/bin/python
#Filter Sensitive Content Providers
#ying.tan@tcl.com


import os
import sys
import re
import time
import shutil
import codecs
from pyXls import *

result = "Pass"
EnvPath = sys.path[0]

PullAndroidManifestToolPath = EnvPath + "/PullAndroidManifestTool"
EmuListPath = EnvPath + "/manifestList_emu"
tempdir = EnvPath + "/temp"
outdir = EnvPath + "/out"
ManifestListPath = tempdir + "/manifestList"
inAospDir = tempdir + "/inAosp/"
outAospDir = tempdir + "/outAosp/"
customDir = outdir + "/custom/"
diffTxt = outdir + "/diff.txt"
customTxt = outdir + "/custom.txt"
withoutPermissionTxt = outdir + "/withoutPermission.txt"

outXls = outdir + "/out.xls"

showDiff = True
outList = []

def setStyles():
    fnt = Font()
    fnt.name = 'Times New Roman'
    al = Alignment()
    al.horz = Alignment.HORZ_LEFT
    al.vert = Alignment.VERT_CENTER
    style = XFStyle()
    style.font = fnt
    style.alignment = al
    return style

def initWorkbook(style, list):
    _wb = Workbook()
    _ws0 = _wb.add_sheet(u'customContentProvider')
    # initial title of workbook
    _ws0.write(0, 0, u'PackageName', style)
    _ws0.write(0, 1, u'ProviderName', style)
    _ws0.write(0, 2, u'ContentProvider', style)
    if showDiff :
        _ws0.write(0, 3, u'Difference', style)

    for itemDict in list:
        i = list.index(itemDict) + 1
        _ws0.write(i, 0, itemDict['packagename'], style)
        _ws0.write(i, 1, itemDict['providername'], style)
        _ws0.write(i, 2, itemDict['contentprovider'], style)
        if showDiff and itemDict.get('diff'):
            _ws0.write(i, 3, itemDict['diff'], style)

    _wb.save(outXls) 
    print "Generate xls table successed!! --> %s" % outXls       

def getPackageName(path):
    lastIdx = path.find(".")
    name = path[:lastIdx] + ".apk"
    return name

#Pull Android Manifests From Phone, path1, path2, path3 represent three different phone path.
def pullAndroidManifestsFromPhone(path1, path2, path3):
    command = "source " + PullAndroidManifestToolPath + "/OneKeyPullManifest.sh"

    os.chdir("PullAndroidManifestTool")
    os.system("pwd")
    os.system("%s %s %s" % (command, path1, tempdir))
    os.system("%s %s %s" % (command, path2, tempdir))
    os.system("%s %s %s" % (command, path3, tempdir))
    os.chdir("%s" % EnvPath)

#Find Content Provider in android manifest, return a contentProvider String.
def filterContentProvider(path):
    f = open(path,'r')

    contentProviderStr = ""
    while True:
        line = f.readline()
        if not line:
            break
        if line.find('<provider') > -1:
            contentProviderStr += line
            # For the condition ended with "/>"
            if line[-3:].find("/>") > -1 :
                pass
            # For the condition ended with "</provider>"
            else:
                while True: 
                    line = f.readline()
                    contentProviderStr += line
                    if line.find("</provider>") > -1:
                        break    
    f.close()
    return contentProviderStr

#Get the content provider attribute value
def getAttrValueByAttrTitle(attrTitle, str):
    attrStr = 'android:' + attrTitle + '="'
    if str.find(attrStr) > -1:
        pos1 = str.find(attrStr) + len(attrStr)
        attrValue = str[pos1:]
        pos2 = attrValue.find('"')
        attrValue = attrValue[:pos2]
    else:
        attrValue = ''
    return attrValue

#Get the Content Provider Node by name
def getContentProviderNode(name, emuStr):
    pos1 = emuStr.find(name)
    tempStr1 = emuStr[:pos1]
    tempStr2 = emuStr[pos1:]
    pos2 = tempStr1.rfind('<provider')
    tempStr1 = tempStr1[pos2:pos1]
    pos3 = tempStr2.find('>') +1
    tempStr3 = tempStr2[:pos3]
    tempStr = tempStr1 + tempStr3
    if tempStr.find(' />') > -1:
        emuProvider = tempStr
    else:
        pos4 = tempStr2.find('</provider>') + len('</provider>')
        tempStr3 = tempStr2[:pos4]
        tempStr = tempStr1 + tempStr3
        emuProvider = tempStr
    return emuProvider

# Analyse difference between inAosp and emulator.
def analyseDiff(jrdStr, emuStr, path):
    jrdStr = jrdStr.strip(' ')
    tempArr = jrdStr.split('<provider ')

    diffStr = ''
    customStr = ''

    pos = -1
    diffDict = {}

    for provider in tempArr:
        if provider != '':
            jrdProvider = ('<provider ' + provider).strip(' ')

            if emuStr.find(jrdProvider) > -1:
                #print ":::::same\n"
                pass
            else:
                name = getAttrValueByAttrTitle('name', jrdProvider)
                if emuStr.find(name) > -1:
                    diffStr += 'Different Package: '
                    diffStr += getPackageName(path)
                    diffStr += '\n'
                    diffStr += '    Jrd Content Provider:\n'
                    diffStr += '        '
                    diffStr += jrdProvider
                    diffStr += '    Emu Content Provider:\n'
                    emuProvider = getContentProviderNode(name, emuStr)
                    diffStr += '        '
                    diffStr += emuProvider
                    diffStr += '\n\n'
                    customStr +=jrdProvider

                else:
                    customStr += jrdProvider

                diffDict['customStr'] = customStr
                diffDict['diffStr'] = diffStr
                return diffDict

def filterCustomOEM():
    diffStr = ''
    customStr = ''
    withoutPermissionStr = ''
    itemNo = 0
    diffNo = 0
    withoutPermissionNo = 0

    for root,dirs,files in os.walk(ManifestListPath):
        for filespath in files:
            jrdfilepath = os.path.join(root,filespath)
            emufilepath = os.path.join(EmuListPath,filespath)
            if os.path.isfile(emufilepath):
                inAospFile = inAospDir + filespath
                #print "Copy file:" + inAospFile
                shutil.copy(jrdfilepath, inAospDir)
                jrdProviderStr = filterContentProvider(inAospFile)
                emuProviderStr = filterContentProvider(emufilepath)
                if jrdProviderStr == emuProviderStr:
                    #print "++++++++++same+++++++++++"
                    pass
                else:
                    shutil.copy(jrdfilepath, customDir)

                    #print "++++++++++not same+++++++++++"
                    #print filespath
                    itemNo += 1
                    diff = analyseDiff(jrdProviderStr, emuProviderStr, filespath)
                    
                    if diff['diffStr']:
                        diffNo += 1 
                        diffStr += str(diffNo) + '. ' + diff['diffStr'] 

                    customStr += str(itemNo) + '. PackageName: '
                    customStr += getPackageName(filespath)
                    customStr += '\n'
                    customStr += '        '
                    customStr += diff['customStr']
                    customStr += '\n'

                    tempStr = filterWithoutPermissionContentProvider(diff['customStr'], filespath)
                    len(tempStr)
                    if len(tempStr) > 1:
                        withoutPermissionNo += 1 
                        filename = getPackageName(filespath)
                        tempStr = str(withoutPermissionNo) + '. Without Permission Package: ' + filename + tempStr
                        withoutPermissionStr += tempStr

                    outDict = {}            
                    outDict['packagename'] = getPackageName(filespath)
                    outDict['contentprovider'] = diff['customStr']
                    outDict['providername'] = getAttrValueByAttrTitle('name', diff['customStr'])
                    outDict['diff'] = diff['diffStr'] 
                    outList.append(outDict)
            else:
                outAospFile = outAospDir + filespath
                #print "Copy file:" + outAospDir+filespath
                shutil.copy(jrdfilepath, outAospDir)
                jrdProviderStr = filterContentProvider(outAospFile)
                if jrdProviderStr != '':
                    itemNo += 1

                    shutil.copy(jrdfilepath, customDir)
                    customStr += str(itemNo) + '. PackageName: '
                    customStr += getPackageName(filespath)
                    customStr += '\n'
                    customStr += jrdProviderStr
                    customStr += '\n'

                    tempStr = filterWithoutPermissionContentProvider(jrdProviderStr, filespath)
                    #print len(tempStr)
                    if len(tempStr) > 1:
                        withoutPermissionNo += 1 
                        filename = getPackageName(filespath)
                        tempStr = str(withoutPermissionNo) + '. Without Permission Package: ' + filename + tempStr
                        withoutPermissionStr += tempStr

                    outDict = {}
                    outDict['packagename'] = getPackageName(filespath)
                    outDict['providername'] = getAttrValueByAttrTitle('name', jrdProviderStr)
                    outDict['contentprovider'] = jrdProviderStr
                    outList.append(outDict)

            fDiff = open(diffTxt, 'w')
            fCustom = open(customTxt, 'w')
            fWithoutPermission = open(withoutPermissionTxt, 'w')
            fDiff.write(diffStr)
            fCustom.write(customStr)
            fWithoutPermission.write(withoutPermissionStr)
            fDiff.close()
            fCustom.close()
            fWithoutPermission.close()

def filterSensitiveContentProvider(path):
    packagefile = open(path, 'r')
    
    while True:
        line = packagefile.readline()
        if not line:
            break
        if line.find('minSdkVersion') > -1:
            index = line.find('"')
            index2 = line[index+1:].find('"') + index + 1
            version = int(line[index+1:index2])
            if version < 17:
                default = "true"
            else:
                default = "false"
        if line.find('<provider') > -1:
            tempcontent = line
            flag = 0
            while True:
                line = packagefile.readline()
                tempcontent = tempcontent + line
                if line.find("</provider>") > -1:
                    break
            if tempcontent.find('exported="true"') > -1 \
               or (default == "true" and tempcontent.find('exported="false"') < 0):
                if tempcontent.find("permission=") > -1:
                    flag = 3
                if tempcontent.find('readPermission=') > -1:
                    flag = flag + 1
                if tempcontent.find('writePermission=') > -1:
                    flag = flag + 2
            else:
                flag = 4
            if flag == 2:
                result = "Fail"
                print line1,
                print tempcontent
            if flag == 0:
                result = "Fail"
                print line1,
                print "Fail",temppath + packagename + ".txt"
                print "Can not find permission declare in file."
    packagefile.close()

def splitProvider(provider):
    provider = provider.strip(' ')
    templist = provider.split('<provider')
    providerlist = []
    #print templist
    for item in templist:

        if item != '':
            string = '<provider' + item
            providerlist.append(string.strip(' '))
    #print providerlist
    return providerlist


def filterWithoutPermissionContentProvider(providers, filename):
    string = ''
    providerlist = splitProvider(providers)
    
    for provider in providerlist:
        exported = getAttrValueByAttrTitle('exported', provider)
        if exported == 'true':
            readPermission = getAttrValueByAttrTitle('readPermission', provider)
            writePermission = getAttrValueByAttrTitle('writePermission', provider)
            if readPermission or writePermission:
                pass
            else:
                string += '\n'
                string += '        '
                string += provider

        elif exported == '':
            filepath = customDir + filename
            checkSdkVersion(filepath)
            string += '\n'
            string += '        '
            string += provider

    string += '\n'
    
    return string

def checkSdkVersion(path):
    file = open(path, 'r')
    
    while True:
        line = file.readline()
        if not line:
            break
        if line.find('minSdkVersion') > -1:
            minSdkVersion = getAttrValueByAttrTitle('minSdkVersion', lines)
            print 'minSdkVersion ' + minSdkVersion
            break 
        elif line.find('targetSdkVersion') > -1:
            targetSdkVersion = getAttrValueByAttrTitle('targetSdkVersion', lines)
            print 'targetSdkVersion ' + targetSdkVersion
            break

def main():
    #if never excute pull Android manifest, get android.manifest from phone.
    #if need to pull again, should manually remove jrd_ManifestList directory first.
    if not os.path.exists(ManifestListPath):
        print "Begin to pull android.manifest from phone..."
        pullAndroidManifestsFromPhone("/system/app/", "/system/framework/", "/custpack/app/")
    else:
        print "You have already pulled android.manifest from phone, if need to pull again, you should manually remove manifestList_jrd directory first."
    #Create inAospDir, outAospDir, customDir.
    if os.path.exists(outdir):
        shutil.rmtree(outdir)
    if os.path.exists(inAospDir):
        shutil.rmtree(inAospDir)
    if os.path.exists(outAospDir):
        shutil.rmtree(outAospDir)
    if os.path.exists(customDir):
        shutil.rmtree(customDir)    
    os.mkdir(outdir)
    os.mkdir(inAospDir)
    os.mkdir(outAospDir)
    os.mkdir(customDir)

    if not os.path.exists(EmuListPath):
        print "Please copy emu android manifest running this script! Directory path is:\n" +     EmuListPath
    else:
        #work through the Jrd_ManifestList to filter Custom and OEM Content Provider.
        filterCustomOEM()
        print "Filter CustomOEM content provider successed!!!\n"

        style = setStyles()
        initWorkbook(style, outList)

        # #Filter Sensitive Content Provider.
        # for root,dirs,files in os.walk(customDir):
        #     for filename in files:
        #         filepath = os.path.join(root ,filename)
        #         print filepath
        #         #filterSensitiveContentProvider(filepath)
        #         filterWithoutPermissionContentProvider(filepath)
        # #print "Filter Sensitive content provider successed!!!\n"
        # print "Filter without permission content provider successed!!!\n"
    
if __name__ == '__main__':
    main()
