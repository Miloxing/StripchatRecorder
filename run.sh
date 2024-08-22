#!/bin/bash

# 无限循环
while true
do
	    # 执行 Python 脚本
	        python3 StripchatRecorder.py &

		    # 获取 Python 脚本的进程ID
		        PID=$!

			    # 等待两小时（7200秒）
			        sleep 7200

				    # 杀掉 Python 脚本的进程
				        kill $PID

					    # 再次循环，重新执行 Python 脚本
				    done

