#/bin/sh
source /root/u/milo.conf
num=${#milolist[@]}
((num--))
runtime=0
while [ true ]
do
  while [ -d "captures" ]
  do
      temp=${milolist[0]}
      echo "$temp"
      echo "保存ts到${temp}:milo/b/strip"
      rclone move "captures" "${temp}:milo/b/strip" --buffer-size 32M --transfers 8 -P --low-level-retries 1
      rclone rmdirs "captures"
      if [ -d "captures" ]
      then
          milolist=("${milolist[@]:1:$num}" $temp)
      else
        echo "${f}上传成功"
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
