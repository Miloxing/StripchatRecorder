#!/bin/bash

# 1 = full file path (ie: /Users/Joe/cam4/hannah/2017.07.26_19.34.47_hannah.mp4)
# 2 = filename (ie : 2017.07.26_19.34.47_hannah.mp4)
# 3 = directory (ie : /Users/Joe/cam4/hannah/)
# 4 = models name (ie: hannah)
# 5 = filename without the extension (ie: 2017.07.26_19.34.47_hannah)
# 6 = 'cam4' - thats it, just 'cam4' to identify the site.
# to call a bash script called "MoveToGoogleDrive.sh" and located in the user Joes home directory, you would use:
# postProcessingCommand = "bash /Users/Joe/home/MoveToGoogleDrive.sh"
# this script will be ran on the files "download location" prior to it being moved to its "completed location".
# The moving of the file will not take place if a post processing script is ran, so if you want to move it once it is completed, do so through commands in the post processing script.

# --- 配置 ---
# 将日志文件路径改为你希望存放 move.sh 脚本自身日志的地方
LOG_FILE="move_sh.log" # 请确保这个路径存在且脚本有写入权限！

# --- 函数：记录日志 ---
log_message() {
    echo "$(date '+%Y/%m/%d %H:%M:%S') - $1" >> "$LOG_FILE"
}

# --- 主逻辑 ---
full_path="$1"
filename="$2"
model_name="$4"
object_directory="up/$model_name" # 使用绝对路径或确保 up 目录在脚本执行的当前目录下

log_message "开始处理文件: $filename (来自: $full_path)"

# 检查输入参数是否完整
if [ -z "$full_path" ] || [ -z "$filename" ] || [ -z "$model_name" ]; then
    log_message "错误：输入参数不完整。 FullPath='$full_path', Filename='$filename', Model='$model_name'"
    exit 1 # 退出，表示处理失败
fi

# 检查原始文件是否存在且可读
if [ ! -f "$full_path" ] || [ ! -r "$full_path" ]; then
    log_message "错误：原始文件不存在或不可读: $full_path"
    exit 1 # 退出
fi

# 检查目标目录下是否已存在同名文件 (正确的检查方式)
target_file_path="$object_directory/$filename"
if [ -f "$target_file_path" ]; then
  log_message "警告：目标目录 '$object_directory' 已存在同名文件 '$filename'。跳过移动。"
  # 决定是退出还是尝试覆盖或其他逻辑，这里选择退出避免覆盖
  exit 0 # 认为处理完成（虽然未移动）
fi

# 检查并创建目标目录
if [ ! -d "$object_directory" ]; then
  log_message "目标目录不存在，尝试创建: $object_directory"
  mkdir -p "$object_directory"
  if [ $? -ne 0 ]; then
      log_message "错误：创建目标目录失败: $object_directory"
      exit 1 # 创建目录失败，退出
  fi
  log_message "目标目录创建成功: $object_directory"
fi

# 再次确认目标目录现在存在且可写
if [ ! -d "$object_directory" ] || [ ! -w "$object_directory" ]; then
    log_message "错误：目标目录不存在或不可写: $object_directory"
    exit 1
fi

# --- 执行移动操作 ---
log_message "尝试移动: '$full_path' -> '$object_directory/'"
mv "$full_path" "$object_directory/"
exit_status=$? # 获取 mv 命令的退出状态码

# --- 判断并记录结果 ---
if [ $exit_status -eq 0 ]; then
  log_message "成功：文件 '$filename' 已移动到 '$object_directory'"
  exit 0 # 成功退出
else
  log_message "错误：移动文件 '$filename' 失败 (mv 命令退出码: $exit_status)。来源: '$full_path', 目标: '$object_directory/'"
  # 可以在这里尝试获取更详细的错误信息，但这比较复杂
  exit 1 # 失败退出
fi
