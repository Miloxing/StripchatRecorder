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
        # 定义变量
        log_file="rclone_upload.log"
        source_dir="up"
        dest_dir="${temp}:milo/strip"

        # 执行 rclone move 命令并记录日志
        rclone move "$source_dir" "$dest_dir" --buffer-size 32M --transfers 4 -P --tpslimit 2 --low-level-retries 2 --retries 2 --log-file="$log_file" --log-level=ERROR

        # 检查日志中是否有上传失败的文件
        failed_files=$(grep "Failed to copy" "$log_file" | awk -F ' : ' '{print $2}' | awk -F': ' '{print $1}')
        if [ -n "$failed_files" ]; then
        echo "以下文件上传失败，将删除这些文件："
        echo "$failed_files"

        # 删除上传失败的文件
        while IFS= read -r file; do
        if [ -f "$source_dir/$file" ]; then
            rm -f "$source_dir/$file"
            echo "已删除文件：$source_dir/$file"
        fi
        done <<< "$failed_files"
        fi

        # 清理日志文件
        rm -f "$log_file"

        # 执行 rclone rmdirs 清理空目录
        rclone rmdirs "$source_dir"
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
