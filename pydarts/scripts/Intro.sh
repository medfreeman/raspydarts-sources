#!/bin/sh


PYDARTS_CFG=pydarts.cfg
PYDARTS_HOME=/home/pi/.pydarts
PYDARTS_VIDEOS=/pydarts/videos
PYDARTS_THEME="`grep 'colorset:' $PYDARTS_HOME/$PYDARTS_CFG  | cut -d':' -f 2`"
PYDARTS_THEME_VIDEOS=$PYDARTS_HOME/themes/$PYDARTS_THEME/videos

if [ -s $PYDARTS_HOME/$PYDARTS_CFG ]; then
	if [ -d $PYDARTS_THEME_VIDEOS -a `find $PYDARTS_THEME_VIDEOS -maxdepth 1 -type f -name "intro.mp4" -o -name "intro.mkv" | wc -l` -ge 1 ]; then
		echo "Find in $PYDARTS_THEME_VIDEOS"
		video=`find $PYDARTS_THEME_VIDEOS -maxdepth 1 -type f -name "intro.mp4" -o -name "intro.mkv" | shuf -n 1`
	elif [ -d $PYDARTS_THEME_VIDEOS/intro -a `find $PYDARTS_THEME_VIDEOS/intro -maxdepth 1 -type f -name "*.mp4" -o -name "*.mkv" | wc -l` -ge 1 ]; then
		echo "Find in $PYDARTS_THEME_VIDEOS/intro"
		video=`find $PYDARTS_THEME_VIDEOS/intro -maxdepth 1 -type f -name "*.mkv" -o -name "*.mp4" | shuf -n 1`
	fi
fi

if [ "$video" = "" ]; then
	if [ -d $PYDARTS_HOME/videos -a `find $PYDARTS_HOME/videos -maxdepth 1 -type f -name "intro.mp4" -o -name "intro.mkv" | wc -l` -ge 1 ]; then
		echo "Find in $PYDARTS_HOME/videos"
		video=`find $PYDARTS_HOME/videos -maxdepth 1 -type f -name "intro.mp4" -o -name "intro.mkv" | shuf -n 1`
	elif [ -d $PYDARTS_HOME/videos/intro -a `find $PYDARTS_HOME/videos/intro -maxdepth 1 -type f -name "*.mp4" -o -name "*.mkv" | wc -l` -ge 1 ] ;then
		echo "Find in $PYDARTS_HOME/videos/intro"
		video=`find $PYDARTS_HOME/videos/intro -maxdepth 1 -type f -name "*.mp4" -o -name "*.mkv" | shuf -n 1`
	elif [ -d $PYDARTS_VIDEOS -a `find $PYDARTS_VIDEOS -maxdepth 1 -type f -name "intro.mp4" -o -name "intro.mkv" | wc -l` -ge 1 ]; then
		echo "Find in $PYDARTS_VIDEOS"
		video=`find $PYDARTS_VIDEOS -maxdepth 1 -type f -name "intro.mp4" -o -name "intro.mkv" | shuf -n 1`
	elif [ -d $PYDARTS_VIDEOS/intro -a `find $PYDARTS_VIDEOS/intro -maxdepth 1 -type f -name "*.mp4" -o -name "*.mkv" | wc -l`-ge 1 ]; then
		echo "Find in $PYDARTS_VIDEOS/intro"
		video=`find $PYDARTS_VIDEOS/intro -maxdepth 1 -type f -name "*.mp4" -o -name "*.mkv" | shuf -n 1`
	else
		exit 0
	fi
fi

omxplayer --vol -1500 -o hdmi "$video"
