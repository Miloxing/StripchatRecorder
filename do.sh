#!/bin/bash
source /root/u/milo.conf
num=${#milolist[@]}
((num--))
runtime=0

# 定义小文件的大小阈值(单位:字节)，默认为5MB
MIN_FILE_SIZE=$((5 * 1024 * 1024))
LOG_FILE="rclone_upload.log"
CLEAN_LOG="file_cleanup.log"

# 函数: 清理过小的文件
function cleanup_small_files() {
    local directory="$1"
    local current_time=$(date "+%Y-%m-%d %H:%M:%S")
    
    echo "[${current_time}] 开始清理目录 ${directory} 中的小文件 (小于 ${MIN_FILE_SIZE} 字节)" >> $CLEAN_LOG
    
    find "$directory" -type f -name "*.mp4" -size -${MIN_FILE_SIZE}c | while read -r file; do
        # 根据操作系统类型使用不同的stat命令
        if [[ "$OSTYPE" == "darwin"* ]]; then
            # macOS
            file_size=$(stat -f "%z" "$file")
        else
            # Linux及其他系统
            file_size=$(stat -c "%s" "$file")
        fi
        echo "[${current_time}] 删除小文件: $file (大小: ${file_size} 字节)" >> $CLEAN_LOG
        rm -f "$file"
    done
    
    # 清理空目录
    find "$directory" -type d -empty -delete
    
    echo "[${current_time}] 清理完成" >> $CLEAN_LOG
}

while [ true ]
do
  # 检查和清理过小的录制文件 (每次循环都执行)
  if [ -d "videos" ]; then
    cleanup_small_files "videos"
  fi
  
  # 处理上传队列
  while [ -d "up" ]
  do
      temp=${milolist[0]}
      echo "$temp"
      echo "保存ts到${temp}:milo/strip"
      
      # 清理上传目录中的小文件
      cleanup_small_files "up"
      
      # 定义变量
      source_dir="up"
      dest_dir="${temp}:milo/strip"

      # 执行 rclone move 命令并记录日志
      rclone move "$source_dir" "$dest_dir" --buffer-size 32M --transfers 4 -P --tpslimit 2 --low-level-retries 2 --retries 2 --log-file="$LOG_FILE" --log-level=ERROR

      # 检查日志中是否有上传失败的文件
      failed_files=$(grep "Failed to copy" "$LOG_FILE" | awk -F ' : ' '{print $2}' | awk -F': ' '{print $1}')
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
      rm -f "$LOG_FILE"

      # 执行 rclone rmdirs 清理空目录
      rclone rmdirs "$source_dir"
      
      # 检查up目录是否存在且为空
      if [ ! -d "$source_dir" ] || [ -z "$(ls -A $source_dir 2>/dev/null)" ]; then
          echo "up上传成功，目录已清空"
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
