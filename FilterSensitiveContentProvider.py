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
withPermissionTxt = outdir + "/withPermission.txt"
shareUserIdPkgTxt = outdir + "/shareUserIdPkg.txt"
outXls = outdir + "/out.xls"

showDiff = True
outList = []

# define data structure of packageInfo
class packageInfo:
    def __init__(self):
        self.ContentProvider = ''
        self.Package = ''
        self. 
        self.
        self.
        self.
        self.
        self.
        self.
        self.
        self.
        self.
        self. 
        self.
        self.
        self.
        self.
        self.
        self.
        self.
        self.
        self.

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
    _ws0 = _wb.add_sheet(u'5.5 Providers')
    # initial title of workbook
    _ws0.write(0, 0, u'General Package Information', style)
    _ws0.write(0, 5, u'Global Provider Permission Information', style)
    _ws0.write(0, 11, u'Path-Permission Information', style)
    _ws0.write(0, 19, u'Provider Export Information', style)
   
    _ws0.write(2, 0, u'Content Provider', style) #A
    _ws0.write(2, 1, u'Package', style) #B
    _ws0.write(2, 2, u'Package Installation Path', style) #C
    _ws0.write(2, 3, u'Package Shared UID', style) #D
    _ws0.write(2, 4, u'Source', style) #E
    _ws0.write(2, 5, u'Permission', style) #F
    _ws0.write(2, 6, u'Permission Protection Level', style) #G
    _ws0.write(2, 7, u'Read Permission', style) #H
    _ws0.write(2, 8, u'Read Permission Protection Level', style) #I
    _ws0.write(2, 9, u'Write Permission', style) #J
    _ws0.write(2, 10, u'Write Permission Protection Level', style) #K
    _ws0.write(2, 11, u'Path-Permission Path', style) #L
    _ws0.write(2, 12, u'Path-Permission Permission', style) #M
    _ws0.write(2, 13, u'Path-Permission Permission Protection Level', style) #N
    _ws0.write(2, 14, u'Path-Permissions Read Permission', style) #O
    _ws0.write(2, 15, u'Path-Permissions Read Permission Protection Level', style) #P
    _ws0.write(2, 16, u'Path-Permissions Write Permission', style) #Q
    _ws0.write(2, 17, u'Path-Permissions Write Permission Protection Level', style) #R
    _ws0.write(2, 18, u'Grant URI Permission', style) #S
    _ws0.write(2, 19, u'Provider is exported?', style) #T
    _ws0.write(2, 20, u'Provider Export Value', style) #U
    _ws0.write(2, 21, u'Package min Sdk Version', style) #V
    _ws0.write(2, 22, u'Package target Sdk Version', style) #W

    for itemDict in list:
        i = list.index(itemDict) + 3
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
    os.system("%s %s %s %s %s" % (command, path1, path2, path3, tempdir))
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
    attrStr = attrTitle + '="'
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
            #print jrdProvider

            if emuStr.find(jrdProvider) < 0:
                name = getAttrValueByAttrTitle('android:name', jrdProvider)
                if emuStr.find(name) > -1:
                    diffStr += '    Jrd Content Provider:\n'
                    diffStr += '        '
                    diffStr += jrdProvider
                    diffStr += '    Emu Content Provider:\n'
                    emuProvider = getContentProviderNode(name, emuStr)
                    diffStr += '        '
                    diffStr += emuProvider
                    diffStr += '\n\n'
                customStr += jrdProvider
                customStr += '        '

    diffDict['customStr'] = customStr
    diffDict['diffStr'] = diffStr
    return diffDict

# Filter SharedUserIdPkg.
def filterSharedUserIdPkg(path):
    manifestStr = getNodeByTag('manifest', path)
    shareUserId = getAttrValueByAttrTitle('android:sharedUserId', manifestStr)
    pkg = getAttrValueByAttrTitle('package', manifestStr)
    sharedUserIdPkgStr = '' 
    if shareUserId.strip(' '):
        sharedUserIdPkgStr = 'android:sharedUserId="'+shareUserId + '  ' + 'package="'+pkg+'"\n'
    return sharedUserIdPkgStr

# get xml node by tag name of each manifest file
def getNodeByTag(tag, path):
    file = open(path, 'r')
    nodeStr = ''
    inTag = False
    while True:
        line = file.readline()
        if line.find('<' + tag) > -1 and not (inTag):
            nodeStr += line
            inTag = True
        if line.find('>') > -1 and inTag:
            nodeStr += line
            break
        if line.find('<' + tag) <0 and line.find('>') < 0 and inTag:
            nodeStr += line
    return nodeStr 


def filterCustomOEM():
    diffStr = ''
    customStr = ''
    withoutPermissionStr = ''
    withPermissionStr = ''
    shareUserIdPkgStr = ''
    itemNo = 0
    diffNo = 0
    withoutPermissionNo = 0
    withPermissionNo = 0
    shareUserIdNo = 0

    for root,dirs,files in os.walk(ManifestListPath):
        for filespath in files:
            jrdfilepath = os.path.join(root,filespath)
            emufilepath = os.path.join(EmuListPath,filespath)
            # Filter SharedUserIdPkg
            print filespath
            
            shareUserIdStr = filterSharedUserIdPkg(jrdfilepath) 
            if shareUserIdStr:
                shareUserIdNo +=1
                shareUserIdPkgStr += str(shareUserIdNo) + '. ' + shareUserIdStr
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
                        diffStr += str(diffNo) + '. ' 
                        diffStr += 'Different Package: '
                        diffStr += getPackageName(filespath)
                        diffStr += '\n'
                        diffStr += diff['diffStr']
                        #print diffStr

                    customStr += str(itemNo) + '. PackageName: '
                    customStr += getPackageName(filespath)
                    customStr += '\n'
                    customStr += '        '
                    customStr += diff['customStr']
                    customStr += '\n'

                    pdict = filterPermissionContentProvider(diff['customStr'], filespath)
                    tempStr1 = pdict['without']
                    tempStr2 = pdict['within']
                    len(tempStr1)
                    if len(tempStr1) > 1:
                        withoutPermissionNo += 1 
                        filename = getPackageName(filespath)
                        tempStr1 = str(withoutPermissionNo) + '. Without Permission Package: ' + filename + tempStr1
                        withoutPermissionStr += tempStr1
                    if len(tempStr2) > 1:
                        withPermissionNo += 1 
                        filename = getPackageName(filespath)
                        tempStr2 = str(withoutPermissionNo) + '. With Permission Package: ' + filename + tempStr2
                        withPermissionStr += tempStr2

                    outDict = {}          
                    generateOutPutDict(outDict, filespath, diff['customStr'])
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

                    pdict = filterPermissionContentProvider(jrdProviderStr, filespath)
                    tempStr1 = pdict['without']
                    tempStr2 = pdict['within']
                    #print len(tempStr)
                    if len(tempStr1) > 1:
                        withoutPermissionNo += 1 
                        filename = getPackageName(filespath)
                        tempStr1 = str(withoutPermissionNo) + '. Without Permission Package: ' + filename + tempStr1
                        withoutPermissionStr += tempStr1
                    if len(tempStr2) > 1:
                        withPermissionNo += 1 
                        filename = getPackageName(filespath)
                        tempStr2 = str(withPermissionNo) + '. With Permission Package: ' + filename + tempStr2
                        withPermissionStr += tempStr2

                    outDict = {}
                    generateOutPutDict(outDict, filespath, jrdProviderStr)
                    outList.append(outDict)

            fDiff = open(diffTxt, 'w')
            fCustom = open(customTxt, 'w')
            fWithoutPermission = open(withoutPermissionTxt, 'w')
            fWithPermission = open(withPermissionTxt, 'w')
            fDiff.write(diffStr)
            fCustom.write(customStr)
            fWithoutPermission.write(withoutPermissionStr)
            fWithPermission.write(withPermissionStr)
            fDiff.close()
            fCustom.close()
            fWithoutPermission.close()
        fShaedUserIdPkg = open(shareUserIdPkgTxt, 'w')
        fShaedUserIdPkg.write(shareUserIdPkgStr)
        fShaedUserIdPkg.close()

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

def generateOutPutDict(outDict, filespath, string):  
    outDict['packagename'] = getPackageName(filespath)
    outDict['contentprovider'] = string
    outDict['providername'] = getAttrValueByAttrTitle('android:name', string)

def filterPermissionContentProvider(providers, filename):
    withPermissionStr = ''
    withoutPermissionStr = ''
    providerlist = splitProvider(providers)
    permissionDict = {}
    
    for provider in providerlist:
        exported = getAttrValueByAttrTitle('android:exported', provider)
        if exported == 'true':
            if checkPermissionAttr(provider):
                withPermissionStr += '\n'
                withPermissionStr += '        '
                withPermissionStr += provider
            else:
                withoutPermissionStr += '\n'
                withoutPermissionStr += '        '
                withoutPermissionStr += provider
        elif exported == '':
            #filepath = customDir + filename
            #checkSdkVersion(filepath)
            if checkPermissionAttr(provider):
                withPermissionStr += '\n'
                withPermissionStr += '        '
                withPermissionStr += provider
            else:
                withoutPermissionStr += '\n'
                withoutPermissionStr += '        '
                withoutPermissionStr += provider

    withPermissionStr += '\n'
    withoutPermissionStr += '\n'

    permissionDict['within'] = withPermissionStr
    permissionDict['without'] = withoutPermissionStr
    
    return permissionDict

def checkPermissionAttr(provider):
    readPermission = getAttrValueByAttrTitle('android:readPermission', provider)
    writePermission = getAttrValueByAttrTitle('android:writePermission', provider)
    permission = getAttrValueByAttrTitle('android:permission', provider)
    if (readPermission and writePermission) or permission:
        return True
    else:
         return False 

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
        #         filterPermissionContentProvider(filepath)
        # #print "Filter Sensitive content provider successed!!!\n"
        # print "Filter without permission content provider successed!!!\n"
    
if __name__ == '__main__':
    main()