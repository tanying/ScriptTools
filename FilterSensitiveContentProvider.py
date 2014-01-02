#!/usr/bin/python
#Filter Sensitive Content Providers
#ying.tan@tcl.com


import os
import sys
import re
import time
import shutil
import codecs

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

#Get the content provider name
def getContentProviderName(str):
    pos1 = str.find('android:name="') + len('android:name="')
    name = str[pos1:]
    pos2 = name.find('"')
    name = name[:pos2]
    return name

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
                print ":::::same\n"
                pass
            else:
                name = getContentProviderName(jrdProvider)
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
                    print filespath
                    diff = analyseDiff(jrdProviderStr, emuProviderStr, filespath)
                    diffStr += diff['diffStr'] 

                    customStr += 'PackageName: '
                    customStr += getPackageName(filespath)
                    customStr += '\n'
                    customStr += '        '
                    customStr += diff['customStr']
                    customStr += '\n'
            else:
                outAospFile = outAospDir + filespath
                #print "Copy file:" + outAospDir+filespath
                shutil.copy(jrdfilepath, outAospDir)
                jrdProviderStr = filterContentProvider(outAospFile)
                if jrdProviderStr!='':
                    shutil.copy(jrdfilepath, customDir)
                    customStr += 'PackageName: '
                    customStr += getPackageName(filespath)
                    customStr += '\n'
                    customStr += jrdProviderStr
                    customStr += '\n'

            fDiff = open(diffTxt, 'w')
            fCustom = open(customTxt, 'w')
            fDiff.write(diffStr)
            fCustom.write(customStr)
            fDiff.close()
            fCustom.close()

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
        #Filter Sensitive Content Provider.
        # for root,dirs,files in os.walk(customDir):
        #     for filename in files:
        #         filepath = os.path.join(root ,filename)
        #         print filepath
        #         #filterSensitiveContentProvider(filepath)
        # print "Filter Sensitive content provider successed!!!\n"

    
if __name__ == '__main__':
    main()
