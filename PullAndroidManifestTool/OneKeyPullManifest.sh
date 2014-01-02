#!/bin/sh
#Author:jinshi.song
#Email:jinshi.song@jrdcom.com
#Updated-1:2013-12-23,12:26,support for multiple device's directory of adb pull
#Updated-1:2013-12-27,17:56,disable automatic open nautilus


function decodeApk(){
	tempapk=$1/tempapk
	tempout=$1/tempout
	manifestList=$1/manifestList

	for filelist in $(ls $tempapk)
		do
		./apktool d -f $tempapk/$filelist  $tempout/$filelist 
                filename=$(echo $filelist | awk -F"." '{print $1}')
                #echo $filename
                #echo $filename
                cp $tempout/$filelist/AndroidManifest.xml $manifestList/$filename.AndroidManifest.xml
		done
}

function cpApk(){
	local curdir tempdir
	curdir=$1
	tempdir=$2
	if [ $1 != $2 ]
	then
	cp -f $curdir/*.apk $tempdir
	fi

	for dirlist in $(ls ${curdir})
	do
		if test -d $curdir/${dirlist}
		then
		echo $curdir/$dirlist
		#echo $tempdir
		cpApk $curdir/$dirlist $tempdir
		else
		:
		#echo $dirlist
		fi
	done	
}

if [ $# -lt 1 ]
then
echo "The paramter can't be empty."
exit 1
elif [ $# -lt 2 ]
then
echo "The second paramter can not be empty."
#echo "Please specify a temporary directory on your PC."
exit 2
fi

#if [ "$1" = "" ]
#then
#echo "The first paramter can not be empty."
#echo "Please specify the directory or file need to get on the android device."
#exit 1
#fi

#if [ "$2" = "" ]
#then
#echo "The second paramter can not be empty."
#echo "Please specify a temporary directory on your PC."
#exit 2
#fi

tempdirIndex=$#
tempdir=$(eval echo \${${tempdirIndex}})

mkdir -p $tempdir/temp
mkdir -p $tempdir/manifestList
mkdir -p $tempdir/tempapk
mkdir -p $tempdir/tempout

echo "adb pull is beginning."
for((i=1;i<$#;i++));do
echo $(eval echo \${${i}})
adb pull $(eval echo \${${i}}) $tempdir/temp
done
echo "adb pull completed."

echo "copy file is beginning."
cpApk $tempdir/temp $tempdir/tempapk
echo "copy file completed."

echo "decode is beginning."
decodeApk $tempdir
echo "decode completed."

echo "clean temp is beginning."
#echo $2
#chmod 777 $2
#chmod 777 $2/*
#sudo rm -irf $2
rm -irf $tempdir/temp
#rm -irf /local/tempapk
rm -irf $tempdir/tempapk
rm -irf $tempdir/tempout
echo "clean temp completed."

#if test -d $tempdir/manifestList
#then
#nautilus $tempdir/manifestList
#fi



