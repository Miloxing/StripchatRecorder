#!/bin/bash
if [ -d "captures" ]
then
    echo "captures目录存在，移动至up"
    if [ ! -d "up" ]
    then
      mkdir "up"
    fi
    for d in captures/*
    do
        if [ -d "$d" ]
        then
            echo "移动$d"
	    d=${d##*/}
            if [ -d "up/$d" ]
            then
		    mv "captures/$d"/* "up/$d"
            else
                mv "captures/$d" "up"
            fi
        fi
    done
    rclone rmdirs "captures"
fi
