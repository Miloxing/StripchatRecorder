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

object_directory="up/$4"
echo "将{$2}移动至$object_directory"
if [ -f "$object_directory" ]
then
  echo "目录存在同名文件，错误"
  exit 0
fi
if [ ! -d "$object_directory" ]
then
  mkdir -p "$object_directory"
fi
if [ -d "$object_directory" ]
then
  mv "$1" "$object_directory"
  echo "{$2}移动成功"
else
  echo "{$2}移动失败"
fi
