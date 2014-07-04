#!/usr/bin/python
#Filter Sensitive Content Providers
#ying.tan@tcl.com

import os
import sys
import re
import time
import shutil
import codecs
from PyExcelerator import *

result = "Pass"
#Get current path
EnvPath = sys.path[0]

PullAndroidManifestToolPath = EnvPath + "/PullAndroidManifestTool"
EmuListPath = EnvPath + "/../input/manifestList_emu"
tempdir = EnvPath + "/../temp"
outdir = EnvPath + "/../output"
ManifestListPath = tempdir + "/manifestList"
manifestPathTxt = tempdir + "/manifestPath.txt"
protectionLevelTxt = tempdir + "/protectionLevel.txt"
inAospDir = tempdir + "/inAosp/"
outAospDir = tempdir + "/outAosp/"
ymlDir = tempdir + "/ymlDir/"
customDir = outdir + "/custom/"
diffTxt = outdir + "/diff.txt"
customTxt = outdir + "/custom.txt"
withoutPermissionTxt = outdir + "/withoutPermission.txt"
withPermissionTxt = outdir + "/withPermission.txt"
shareUserIdPkgTxt = outdir + "/shareUserIdPkg.txt"
outXls = outdir + "/contentProvider.xls"

#add by jinshi.song
ProtectedBroadcastTxt=tempdir + "/ProtectedBroadcast.txt"
emuProtectedBroadcastTxt=tempdir + "/emuProtectedBroadcast.txt"
SystemServiceTxt=tempdir+"/SystemServiceList.txt"
DictXls=EnvPath+"/../input/SystemServiceAndBundlePackageDict.xls"

outList = []
pathDict = {}
ApkDict = {}
verDict = {}
protectionLevelDict = {}
sourceDict={}
renamePkgDict={}

# define data structure of packageInfo
class PackageInfo:
    def __init__(self):
        self.ContentProvider = [] #A
        self.Package = '' #B
        self.PackageInstallationPath = '' #C
        self.PackageSharedUID = '' #D
        self.Source = '' #E
        self.PackageMinSdkVersion = '' #V
        self.PackageTargetSdkVersion = '' #W

class ContentProvider:
    def __init__(self):
        self.name = ''
        self.Permission = '' #F
        self.PathPermission = []
        self.GrantURIPermission = '' #S
        self.ProviderIsexported = '' #T
        self.ProviderExportValue = '' #U

class Permission:
    def __init__(self):
        self.Path = '' #L
        self.Permission = None #M
        self.PermissionProtectionLevel = '' #N
        self.ReadPermission = '' #O
        self.ReadPermissionProtectionLevel = '' #P
        self.WritePermission = '' #Q
        self.WritePermissionProtectionLevel = '' #R

def splitPathPermission(string):
    templist = string.split('<path-permission')
    pathPermissionList = []
    for item in templist:
        if item != '':
            string = '<path-permission' + item
            pathPermissionList.append(string.strip(' '))
    #print providerlist
    return pathPermissionList

def checkProtectionLevelValue(string):
    string = string.lower()
    if string.find('|') > -1:
        if string.find('normal') > -1:
            result = 'normal'
        elif string.find('dangerous') > -1:
            result = 'dangerous'
        elif string.find('signatureorsystem') > -1:
            result = 'signatureOrSystem'
        elif string.find('signature') > -1:
            result = 'signature'
    else:
        result = string
    return result

def setPermissionValue(string, isPathPermission):
    #print string
    permissionValue = getAttrValueByAttrTitle('android:permission', string).strip(' ')
    readPermissionValue = getAttrValueByAttrTitle('android:readPermission', string).strip(' ')
    writePermissionValue = getAttrValueByAttrTitle('android:writePermission', string).strip(' ')
        
    permission = Permission()
    permission.Permission = permissionValue
    permission.ReadPermission = readPermissionValue
    permission.WritePermission = writePermissionValue
        
    if protectionLevelDict.has_key(permissionValue):
        permission.PermissionProtectionLevel = checkProtectionLevelValue(protectionLevelDict[permissionValue])
    if protectionLevelDict.has_key(readPermissionValue):
        permission.ReadPermissionProtectionLevel = checkProtectionLevelValue(protectionLevelDict[readPermissionValue])
    if protectionLevelDict.has_key(writePermissionValue):
        permission.WritePermissionProtectionLevel = checkProtectionLevelValue(protectionLevelDict[writePermissionValue])
    # print permissionValue+'---'+permission.PermissionProtectionLevel
    # print readPermissionValue+'---'+permission.ReadPermissionProtectionLevel
    # print writePermissionValue+'---'+permission.WritePermissionProtectionLevel
    # print '-----------------'
    if isPathPermission:
        path = getAttrValueByAttrTitle('android:path', string).strip(' ')
        pathPrefix = getAttrValueByAttrTitle('android:pathPrefix', string).strip(' ')
        pathPattern = getAttrValueByAttrTitle('android:pathPattern', string).strip(' ')
        if path:
            permission.Path = path
        elif pathPrefix:
            permission.Path = 'pathPrefix:' + pathPrefix
        elif pathPattern:
            permission.Path = 'pathPattern:' + pathPattern
    return permission

def generatePermissionInfo(provider):
    cp = ContentProvider()
    if provider.find('<path-permission') > -1:
        idx1 = provider.find('<path-permission')
        idx2 = provider.find('</provider>')
        providerStr = provider[:idx1]
        pathPermissionStr = provider[idx1:idx2]
        pathPermissionList = splitPathPermission(pathPermissionStr)
        permission = setPermissionValue(providerStr, False)
        #print permission
        if permission:
            cp.Permission = permission
            #print cp.Permission.Permission+'-'+ cp.Permission.ReadPermission+ '-'+cp.Permission.WritePermission
            for item in pathPermissionList:
                pathPermission = Permission()
                pathPermission = setPermissionValue(item, True)
                cp.PathPermission.append(pathPermission)
    else:
        permission = setPermissionValue(provider, False)
        if permission:
            cp.Permission = permission
    return cp

def getPackageName(path):
    lastIdx = path.find(".")
    name = path[:lastIdx] + ".apk"
    return name

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

def separateOEMsourcedGoogleAnd3rdparty(pkg):
    if pkg.find('google') > -1:
        return 'Google'
    elif pkg.find('jrdcom') > -1 or pkg.find('tcl') > -1 or pkg.find('mediatek') > -1 or pkg.find('com.android') > -1:
        return 'OEM-sourced'
    else:
        return '3rd party'

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

def pullAndroidManifestsFromPhone(path1, path2, path3):
    command = "source " + PullAndroidManifestToolPath + "/OneKeyPullManifest.sh"
    os.chdir("PullAndroidManifestTool")
    os.system("pwd")
    os.system("%s %s %s %s %s" % (command, path1, path2, path3, tempdir))
    os.chdir("%s" % EnvPath)

def pullAndroidManifestsFromPhoneKK(path1, path2, path3,path4):
    command = "source " + PullAndroidManifestToolPath + "/OneKeyPullManifest.sh"
    os.chdir("PullAndroidManifestTool")
    os.system("pwd")
    os.system("%s %s %s %s %s %s" % (command, path1, path2, path3, path4, tempdir))
    os.chdir("%s" % EnvPath)

def splitXmlAndYml():
    if os.path.exists(ymlDir):   
        shutil.rmtree(ymlDir)
    os.mkdir(ymlDir)
    for root,dirs,files in os.walk(ManifestListPath):
        for filespath in files:
            if filespath.rfind('.yml') > 0:
                ymlPath = os.path.join(root,filespath)
                shutil.copy(ymlPath, ymlDir)
                os.remove(ymlPath) 

def getManifestPathFromPhone():
    command = "adb shell pm list packages -f "
    os.system("%s > %s" % (command, manifestPathTxt)) 

def getProtectLevelFromManifest(tag, output):
    os.chdir(ManifestListPath)
    # command =  "grep -ri '<permission' ."
    # os.system("%s > %s" % (command, protectionLevelTxt))
    os.system("grep -ri '<%s' . > %s" % (tag, output))

def grepTagToOutputByPath(path,tag, output):
    os.chdir(path)
    # command =  "grep -ri '<permission' ."
    # os.system("%s > %s" % (command, protectionLevelTxt))
    os.system("grep -ri '<%s' . > %s" % (tag, output))

def generatePackageInstallationToPathDict():
    f = open(manifestPathTxt, 'r')
    while True:
        line = f.readline()
        if not line:
            break
        if line.find('package:') > -1:
            list = line.split('=')
            idx1 = list[1].find('\r\n')
            package = list[1][:idx1]
            idx2 = list[0].find(':') + 1
            path = list[0][idx2:]
            idx3=list[0].rfind('/') + 1
            apkname=list[0][idx3:]
            ApkDict[apkname]=package
            pathDict[package] = path

def generateVersionToVerDict():
    for root,dirs,files in os.walk(ymlDir):
        for fileName in files:
            filePath = os.path.join(root,fileName)
            f = open(filePath, 'r')
            minSdkVersion='1'
            targetSdkVersion=minSdkVersion
            key=''
            renamePkg=''
            while True:
                line = f.readline()
                if not line:
                    break
                if line.find('apkFileName') > -1:
		            idx1 = line.find(':') + 1
		            idx2 = line.find('\n')
		            key = line[idx1:idx2].strip(' ')
                if line.find('minSdkVersion') > -1:
                    idx1 = line.rfind(':') + 1
                    idx2 = line.rfind('\n')
                    minSdkVersion = line[idx1:idx2].strip(' ').strip("'")
                    targetSdkVersion=minSdkVersion
                if line.find('targetSdkVersion') > -1:
                    idx1 = line.rfind(':') + 1
                    idx2 = line.rfind('\n')
                    targetSdkVersion = line[idx1:idx2].strip(' ').strip("'")
                if line.find('rename-manifest-package') > -1:
		            idx1 = line.find(':') + 1
		            idx2 = line.find('\n')
		            renamePkg = line[idx1:idx2].strip(' ')
			
            if renamePkg!='':
		    	if ApkDict.has_key(key):
		    		renamePkgDict[key]=renamePkg
            if ApkDict.has_key(key):
            	verDict[ApkDict[key]] = [minSdkVersion, targetSdkVersion]


def generateProtectionLevelToProtectionLevelDict():
    f = open(protectionLevelTxt, 'r')
    while True:
        line = f.readline()
        if not line:
            break
        if line.find('android:protectionLevel') > -1:
            value = getAttrValueByAttrTitle('android:protectionLevel', line)
            key = getAttrValueByAttrTitle('android:name', line)
            protectionLevelDict[key] = value           

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

            apkNameFromFileName=filespath[:filespath.find('.',filespath.find('.')+1)]
            #print apkNameFromFileName
            #generate package info
            info = PackageInfo()
            manifestStr = getNodeByTag('manifest', jrdfilepath)
            if renamePkgDict.has_key(apkNameFromFileName):
            	pkg=renamePkgDict[apkNameFromFileName]
            else:
            	pkg=getAttrValueByAttrTitle('package', manifestStr)
            #pkg = renamePkgDict.has_key(apkNameFromFileName)?renamePkgDict[apkNameFromFileName]:getAttrValueByAttrTitle('package', manifestStr)
            shareUserId = getAttrValueByAttrTitle('android:sharedUserId', manifestStr)
            
            info.Package = pkg
            info.PackageSharedUID = shareUserId.strip(' ')
            splitedPkg=''
            #print pkg + "$$$$$$"

            if pathDict.has_key(pkg):
                info.PackageInstallationPath = pathDict[pkg]
            else:
            	print "FilterSensitiveContentProvider error:"+pkg+" not found,retry once after split the package name."
            	#modify for googleDrive.apk
            	splitedPkg=pkg[:pkg.rfind('.')]
            	if pathDict.has_key(splitedPkg):
            		info.PackageInstallationPath=pathDict[splitedPkg]
            		info.Package = splitedPkg
            		print "FilterSensitiveContentProvider info:"+pkg+" has been repaired->"+splitedPkg
            	else:
            		print "FilterSensitiveContentProvider fatal error:"+pkg+" still not found,skip."
            		continue
                #print info.PackageInstallationPath
            if verDict.has_key(pkg):
                info.PackageMinSdkVersion = verDict[pkg][0]
                info.PackageTargetSdkVersion = verDict[pkg][1]
            else:
            	if verDict.has_key(splitedPkg):
            		info.PackageMinSdkVersion = verDict[splitedPkg][0]
            		info.PackageTargetSdkVersion = verDict[splitedPkg][1]
            	else:
	            	print "FilterSensitiveContentProvider error:"+pkg+" sdk version not found,yml file maybe not exists."
            #print ' <' + info.Package + ' output successed>'

            #Filter All Content Provider
            providerStr = filterContentProvider(jrdfilepath)
            for provider in splitProvider(providerStr):
                cp = generatePermissionInfo(provider)
                cp.name = getAttrValueByAttrTitle('android:name', provider)
                cp.GrantURIPermission = getAttrValueByAttrTitle('android:grantUriPermissions', provider)
                cp.ProviderExportValue = getAttrValueByAttrTitle('android:exported', provider)
                if cp.ProviderExportValue:
                    cp.ProviderIsexported = cp.ProviderExportValue + '-explicit'
                elif info.PackageMinSdkVersion and info.PackageTargetSdkVersion:
                    if int(info.PackageMinSdkVersion) < 17 or int(info.PackageTargetSdkVersion) < 17:
                        cp.ProviderIsexported = 'true-default'
                    else:
                        cp.ProviderIsexported = 'false-default'
                
                info.ContentProvider.append(cp)
            # Filter SharedUserIdPkg
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
                    info.Source = 'AOSP-unmodified'
                else:
                    shutil.copy(jrdfilepath, customDir)
                    info.Source = 'OEM-modified AOSP'
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

                    # outDict = {}          
                    # outDict['packagename'] = getPackageName(filespath)
                    # outDict['contentprovider'] = diff['customStr']
                    # outDict['providername'] = getAttrValueByAttrTitle('android:name', diff['customStr'])
                    # outDict['diff'] = diff['diffStr'] 
                    # outList.append(outDict)
            else:
                outAospFile = outAospDir + filespath
                #print "Copy file:" + outAospDir+filespath
                shutil.copy(jrdfilepath, outAospDir)
                info.Source = separateOEMsourcedGoogleAnd3rdparty(info.Package.lower())
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

                    # outDict = {}
                    # outDict['packagename'] = getPackageName(filespath)
                    # outDict['contentprovider'] = jrdProviderStr
                    # outDict['providername'] = getAttrValueByAttrTitle('android:name', jrdProviderStr)
                    # outList.append(outDict)
            outList.append(info)
            if info.Source.find('OEM') > -1:
            	sourceValue = 'OEM'
            elif info.Source.find('Google') > -1:
            	sourceValue = 'Google'
            elif info.Source.find('AOSP') > -1:
            	sourceValue = 'AOSP'
            elif info.Source.find('3rd') > -1:
            	sourceValue = '3rd party'
            sourceDict[info.Package]=sourceValue
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

def setStyles(bool):
    fnt = Font()
    #fnt.name = 'Times New Roman'
    fnt.bold = bool
    # pt = Pattern()
    # pt.pattern_back_colour = 0x7F
    al = Alignment()
    al.horz = Alignment.HORZ_LEFT
    al.vert = Alignment.VERT_CENTER
    style = XFStyle()
    style.font = fnt
    style.alignment = al
    # style.pattern = pt
    return style

def initWorkbook(style, style_title, list,wb=0):
    #_wb = Workbook()
    if wb==0:
        _wb = Workbook()
    else:
        _wb=wb
    _ws0 = _wb.add_sheet(u'5.5 Providers')
    # initial title of workbook , Merge Cells
    _ws0.write_merge(0, 1, 0, 4, u'General Package Information',style_title)
    _ws0.write_merge(0, 1, 5, 10, u'Global Provider Permission Information',style_title)
    _ws0.write_merge(0, 1, 11, 18, u'Path-Permission Information',style_title)
    _ws0.write_merge(0, 1, 19, 22, u'Provider Export Information',style_title)
   
    _ws0.write(2, 0, u'Content Provider', style_title) #A
    _ws0.write(2, 1, u'Package', style_title) #B
    _ws0.write(2, 2, u'Package Installation Path', style_title) #C
    _ws0.write(2, 3, u'Package Shared UID', style_title) #D
    _ws0.write(2, 4, u'Source', style_title) #E
    _ws0.write(2, 5, u'Permission', style_title) #F
    _ws0.write(2, 6, u'Permission Protection Level', style_title) #G
    _ws0.write(2, 7, u'Read Permission', style_title) #H
    _ws0.write(2, 8, u'Read Permission Protection Level', style_title) #I
    _ws0.write(2, 9, u'Write Permission', style_title) #J
    _ws0.write(2, 10, u'Write Permission Protection Level', style_title) #K
    _ws0.write(2, 11, u'Path-Permission Path', style_title) #L
    _ws0.write(2, 12, u'Path-Permission Permission', style_title) #M
    _ws0.write(2, 13, u'Path-Permission Permission Protection Level', style_title) #N
    _ws0.write(2, 14, u'Path-Permissions Read Permission', style_title) #O
    _ws0.write(2, 15, u'Path-Permissions Read Permission Protection Level', style_title) #P
    _ws0.write(2, 16, u'Path-Permissions Write Permission', style_title) #Q
    _ws0.write(2, 17, u'Path-Permissions Write Permission Protection Level', style_title) #R
    _ws0.write(2, 18, u'Grant URI Permission', style_title) #S
    _ws0.write(2, 19, u'Provider is exported?', style_title) #T
    _ws0.write(2, 20, u'Provider Export Value', style_title) #U
    _ws0.write(2, 21, u'Package min Sdk Version', style_title) #V
    _ws0.write(2, 22, u'Package target Sdk Version', style_title) #W

    count = 0
    ppcount = 0
    for info in list:
        i = list.index(info) + 3 + count 
        #print info.Package + ' ------'+str(i)
        
        if info.ContentProvider:
            for cp in info.ContentProvider:
                j = info.ContentProvider.index(cp) + ppcount
                if cp.PathPermission:
                    for pp in cp.PathPermission:
                        k = cp.PathPermission.index(pp)
                        #print '       '+str(i+j+k)

                        _ws0.write(i+j+k, 0, cp.name, style)
                        _ws0.write(i+j+k, 1, info.Package, style)
                        _ws0.write(i+j+k, 2, info.PackageInstallationPath, style)
                        _ws0.write(i+j+k, 3, info.PackageSharedUID, style)
                        _ws0.write(i+j+k, 4, info.Source, style)
                        _ws0.write(i+j+k, 5, cp.Permission.Permission, style)
                        _ws0.write(i+j+k, 6, cp.Permission.PermissionProtectionLevel, style) 
                        _ws0.write(i+j+k, 7, cp.Permission.ReadPermission, style)
                        _ws0.write(i+j+k, 8, cp.Permission.ReadPermissionProtectionLevel, style) 
                        _ws0.write(i+j+k, 9, cp.Permission.WritePermission, style)
                        _ws0.write(i+j+k, 10, cp.Permission.WritePermissionProtectionLevel, style) 
                        _ws0.write(i+j+k, 11, pp.Path, style)
                        _ws0.write(i+j+k, 12, pp.Permission, style)
                        _ws0.write(i+j+k, 13, pp.PermissionProtectionLevel, style)
                        _ws0.write(i+j+k, 14, pp.ReadPermission, style)
                        _ws0.write(i+j+k, 15, pp.ReadPermissionProtectionLevel, style) 
                        _ws0.write(i+j+k, 16, pp.WritePermission, style)
                        _ws0.write(i+j+k, 17, pp.WritePermissionProtectionLevel, style) 
                        _ws0.write(i+j+k, 18, cp.GrantURIPermission, style)
                        _ws0.write(i+j+k, 19, cp.ProviderIsexported, style)
                        _ws0.write(i+j+k, 20, cp.ProviderExportValue, style)
                        _ws0.write(i+j+k, 21, info.PackageMinSdkVersion, style)
                        _ws0.write(i+j+k, 22, info.PackageTargetSdkVersion, style)

                    ppcount += len(cp.PathPermission) - 1 
                    #print '       '+str(j)+'-'+str(len(cp.PathPermission))+'-'+str(ppcount)
                    #print '       ' + str(len(cp.PathPermission))+'-'+str(ppcount)

                #print '  ' + cp.name + '-'+str(i+j)
                _ws0.write(i+j, 0, cp.name, style)
                _ws0.write(i+j, 1, info.Package, style)
                _ws0.write(i+j, 2, info.PackageInstallationPath, style)
                _ws0.write(i+j, 3, info.PackageSharedUID, style)
                _ws0.write(i+j, 4, info.Source, style)

                if cp.Permission:
                    _ws0.write(i+j, 5, cp.Permission.Permission, style)
                    _ws0.write(i+j, 6, cp.Permission.PermissionProtectionLevel, style) 
                    _ws0.write(i+j, 7, cp.Permission.ReadPermission, style)
                    _ws0.write(i+j, 8, cp.Permission.ReadPermissionProtectionLevel, style) 
                    _ws0.write(i+j, 9, cp.Permission.WritePermission, style)
                    _ws0.write(i+j, 10, cp.Permission.WritePermissionProtectionLevel, style) 
                    _ws0.write(i+j, 18, cp.GrantURIPermission, style)

                _ws0.write(i+j, 19, cp.ProviderIsexported, style)
                _ws0.write(i+j, 20, cp.ProviderExportValue, style)
                _ws0.write(i+j, 21, info.PackageMinSdkVersion, style)
                _ws0.write(i+j, 22, info.PackageTargetSdkVersion, style)
                
            count += len(info.ContentProvider) - 1
        else:
            i = list.index(info) + 3 + count + ppcount
            _ws0.write(i, 0, '...No Providers', style)
            _ws0.write(i, 1, info.Package, style)
            _ws0.write(i, 2, info.PackageInstallationPath, style)
            _ws0.write(i, 3, info.PackageSharedUID, style)
            _ws0.write(i, 4, info.Source, style)
            #_ws0.write(i, 19, cp.ProviderIsexported, style)
            #_ws0.write(i, 20, cp.ProviderExportValue, style)
            _ws0.write(i, 21, info.PackageMinSdkVersion, style)
            _ws0.write(i, 22, info.PackageTargetSdkVersion, style)

        #print str(i)+'|'+str(count)+"|"+str(ppcount)
    
    #Set column width
    for i in range(1, 18):
        _ws0.col(i).width = 8000 

    _ws0.col(0).width = 10000
    _ws0.col(2).width = 15000
    _ws0.col(3).width = 5000
    _ws0.col(4).width = 5000
    _ws0.col(6).width = 4000  
    _ws0.col(8).width = 4000
    _ws0.col(10).width = 4000  
    _ws0.col(13).width = 4000
    _ws0.col(15).width = 4000
    _ws0.col(17).width = 4000 

    if wb==0:
        _wb.save(outXls)
        print "Generate xls table successed!! --> %s" % outXls      

def prepareFilesFromPhone():
    #if never excute pull Android manifest, get android.manifest from phone.
    #if need to pull again, should manually remove jrd_ManifestList directory first.
    if not os.path.exists(ManifestListPath):
        print "Please connect your Phone By USB!\n Begin to pull android.manifest from phone..."
        #Pull Android Manifests From Phone, path1, path2, path3 represent three different phone path.
        #pullAndroidManifestsFromPhone("/system/app/", "/system/framework/", "/custpack/app/")
        #modify for Androir4.4KK
        pullAndroidManifestsFromPhoneKK("/system/app/", "/system/priv-app/", "/system/framework/", "/custpack/app/")
        #The Original ManifestListPath contains manifest files and yml files. Seperate them first
        splitXmlAndYml()
        #get Manfest Path From Phone --> OutPut file: manifestPathTxt
        getManifestPathFromPhone()
        #get Protection Level From ManifestListPath --> protectionLevelTxt
        getProtectLevelFromManifest('permission', protectionLevelTxt)
    else:
        print "You have already pulled android.manifest from phone, if need to pull again, you should manually remove temp directory first."

def prepareDirsAndDicts():
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
    
    #work through the Jrd_ManifestList to filter Custom and OEM Content Provider.
    #manifestPath.txt to PathDict
    generatePackageInstallationToPathDict()
    #ymlDir to VerDict
    generateVersionToVerDict()
    #protectionLevel.txt to ProtectionLevelDict
    generateProtectionLevelToProtectionLevelDict()

def Output(_wb):
        filterCustomOEM()
        #print "Filter CustomOEM content provider successed!!!\n"

        style = setStyles(False)
        style_title = setStyles(True)
        initWorkbook(style, style_title, outList,_wb)

def main():
    prepareFilesFromPhone()
    if not os.path.exists(EmuListPath):
        print "Please copy emu android manifest running this script! Directory path is:\n" +     EmuListPath
        return
    else:
        prepareDirsAndDicts()
        
        filterCustomOEM()
        print "Filter CustomOEM content provider successed!!!\n"

        style = setStyles(False)
        style_title = setStyles(True)
        initWorkbook(style, style_title, outList)

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