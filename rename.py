#!/usr/bin/python
# -*-coding:utf-8-*-
# 通过apktool 重命名 应用名字
import glob
import io
import json
import os
import platform
import sys

sys.path.append('./config')
import config


# 获取脚本文件的当前路径
def curFileDir():
    # 获取脚本路径
    path = sys.path[0]
    # 判断为脚本文件还是py2exe编译后的文件，
    # 如果是脚本文件，则返回的是脚本的目录，
    # 如果是编译后的文件，则返回的是编译后的文件路径
    if os.path.isdir(path):
        return path
    elif os.path.isfile(path):
        return os.path.dirname(path)


# 判断当前系统
def isWindows():
    sysstr = platform.system()
    if "Windows" in sysstr:
        return 1
    else:
        return 0


# 兼容不同系统的路径分隔符
def getBackslash():
    if (isWindows() == 1):
        return "\\"
    else:
        return "/"


# 修改AndroidMenifest 应用名
def alter(path, old_str, new_str):
    file_data = ""
    with io.open(path, "r", encoding="utf-8") as f:
        for line in f:
            if old_str in line:
                line = line.replace(old_str, new_str)
            file_data += line
    with io.open(path, "w", encoding="utf-8") as f:
        f.write(file_data)


file = open(r"{}".format(config.channelAppNameMapFilePath), "rb")
channelInfos = json.load(file)
parentPath = curFileDir() + getBackslash()
# config
libPath = parentPath + "lib" + getBackslash()
buildToolsPath = config.sdkBuildToolPath + getBackslash()
checkAndroidV2SignaturePath = libPath + "CheckAndroidV2Signature.jar"
walleChannelWritterPath = libPath + "walle-cli-all.jar"
apkToolPath = libPath + "apktool.jar"
keystorePath = config.keystorePath
keyAlias = config.keyAlias
keystorePassword = config.keystorePassword
keyPassword = config.keyPassword
channelsOutputFilePath = config.channelsOutputFilePath
channelFilePath = parentPath + "channel"
protectedSourceApkPath = parentPath + config.protectedSourceApkName
for item in channelInfos["channelInfoList"]:
    if 'extraInfo' in item:
        apklist = glob.glob(r'./build/channels/{}/*{}.apk'.format(config.versionName, item['channel']))
        print('./build/channel/{}/*{}.apk'.format(config.versionName, item['channel']))
        for apk in apklist:
            dShell = "java -jar " + apkToolPath + " d -f " + apk + " -o " + apk.replace('.apk', '')
            print(dShell)
            print(apk)
            os.system(dShell)
            apkResPath = apk.replace('.apk', '') + '/AndroidManifest.xml'
            print(apkResPath)
            old_str = "android:label=\"@string/app_name\""
            new_str = "android:label=\"{}\"".format(item['extraInfo']['name'])
            alter(apkResPath, old_str, new_str)
            bShell = "java -jar " + apkToolPath + " b " + apk.replace('.apk', '')
            os.system(bShell)
            print(apk)
            apkPath = apk.replace('.apk', '') + '/dist/' + os.path.basename(apk)
            zipalignedApkPath = apkPath.replace('.apk', 'ggg.apk')
            # 对齐
            zipalignShell = buildToolsPath + "zipalign -v 4 " + apkPath + " " + zipalignedApkPath
            os.system(zipalignShell)

            signedApkPath = zipalignedApkPath.replace('ggg.apk', 'hhh.apk')

            # 签名
            signShell = buildToolsPath + "apksigner sign --ks " + keystorePath + " --ks-key-alias " + keyAlias + " --ks-pass pass:" + keystorePassword + " --key-pass pass:" + keyPassword + " --out " + signedApkPath + " " + zipalignedApkPath
            os.system(signShell)
            # print(signShell)

            # 检查V2签名是否正确
            checkV2Shell = "java -jar " + checkAndroidV2SignaturePath + " " + signedApkPath
            os.system(checkV2Shell)

            # 写入渠道
            writeChannelShell = "java -jar " + walleChannelWritterPath + " put -c " + item[
                'channel'] + ' ' + signedApkPath
            print(writeChannelShell)
            os.system(writeChannelShell)

            lastApkFilePath = signedApkPath.replace(
                '.apk', '') + '_' + item[
                                  'channel'] + '.apk'
            # 读取渠道
            readChannelShell = "java -jar " + walleChannelWritterPath + " show " + ' ' + lastApkFilePath
            os.system(readChannelShell)

            # 还原apk文件名
            clearShell = "mv " + " -f " + lastApkFilePath  + ' '+apk
            os.system(clearShell)

            # 删除多余文件夹
            rmShell = "rm -rf " + apk.replace('.apk','')
            os.system(rmShell)
