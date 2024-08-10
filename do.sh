#!/bin/bash
source /root/u/milo.conf
num=${#milolist[@]}
((num--))
runtime=0
while [ true ]
do
  while [ -d "up" ]
  do
      temp=${milolist[0]}
      echo "$temp"
      echo "保存ts到${temp}:milo/strip"
      rclone move "up" "${temp}:milo/strip" --buffer-size 32M --transfers 4 -P --tpslimit 2 --low-level-retries 2 --retries 2
      rclone rmdirs "up"
      if [ -d "up" ]
      then
          milolist=("${milolist[@]:1:$num}" $temp)
      else
        echo "up上传成功"
        let runtime++
        if [ $runtime -ge 25 ]
        then
            source /root/u/milo.conf
            runtime=0
        fi
      fi
      sleep 60
  done
sleep 10
done
