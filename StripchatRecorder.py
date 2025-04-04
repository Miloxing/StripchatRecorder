import time
import datetime
import os
import threading
import sys
import configparser
import subprocess
import queue
import requests
import streamlink
import shutil
from flask import Flask, render_template, request, redirect, url_for

if os.name == 'nt':
    import ctypes

    kernel32 = ctypes.windll.kernel32
    kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)

mainDir = sys.path[0]
Config = configparser.ConfigParser()
setting = {}

recording = []

hilos = []

# 创建Flask应用
app = Flask(__name__)

# 添加共享状态
app_state = {
    "repeatedModels": [],
    "counterModel": 0,
    "port": 8080,  # 添加端口状态
    "web_status": "初始化中...",  # 添加web状态信息
    "storage_info": {}  # 添加存储空间信息
}

# 获取存储空间信息
def get_storage_info():
    """获取存储空间使用情况"""
    storage_info = {}
    
    # 获取当前目录存储空间
    total, used, free = shutil.disk_usage("/")
    storage_info["local"] = {
        "total": total // (2**30),  # 转换为GB
        "used": used // (2**30),
        "free": free // (2**30),
        "percent_used": used * 100 // total
    }
    
    # 如果有配置远程存储，也可以添加
    # 这里需要根据实际情况调整
    
    return storage_info

# Flask路由
@app.route('/')
def index():
    """主页，显示当前状态"""
    # 更新存储空间信息
    app_state["storage_info"] = get_storage_info()
    
    return render_template('index.html', 
                           hilos=hilos, 
                           recording=recording, 
                           repeatedModels=app_state["repeatedModels"], 
                           counterModel=app_state["counterModel"],
                           port=app_state["port"],
                           storage_info=app_state["storage_info"])  # 传递存储信息到模板

@app.route('/edit_wanted', methods=['GET', 'POST'])
def edit_wanted():
    """查看和编辑wanted.txt文件"""
    if request.method == 'POST':
        # 保存更新后的内容到wanted.txt
        with open(setting['wishlist'], 'w') as f:
            f.write(request.form['content'])
        return redirect(url_for('index'))
    
    # 读取wanted.txt内容
    with open(setting['wishlist'], 'r') as f:
        content = f.read()
    
    return render_template('edit_wanted.html', content=content)

# 添加停止录制路由
@app.route('/stop_recording/<model_name>', methods=['POST'])
def stop_recording(model_name):
    """停止特定模特的录制"""
    for modelo in recording[:]:  # 使用副本遍历，避免在遍历过程中修改
        if modelo.modelo == model_name:
            modelo.stop()
            # 记录停止事件
            with open('log.log', 'a+') as f:
                f.write(f'\n{datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")} 通过Web界面停止录制: {model_name}\n')
            break
    return redirect(url_for('index'))

# 添加启动web服务器的函数
def start_web_server():
    """在单独的线程中启动Flask应用"""
    # 创建templates目录
    os.makedirs(os.path.join(mainDir, 'templates'), exist_ok=True)
    
    # 创建模板文件
    create_templates()
    
    # 尝试不同端口启动网页服务器
    port = 8080
    max_port = 8090  # 最大尝试端口
    
    while port <= max_port:
        try:
            app_state["port"] = port  # 更新当前使用的端口
            # 更新web状态信息
            app_state["web_status"] = f"Web服务器正在启动，端口: {port}..."
            print(f"\n[Web服务] 正在端口 {port} 上启动Web界面...")
            
            # 先检查端口是否被占用
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('127.0.0.1', port))
            sock.close()
            
            if result == 0:  # 端口已被占用
                raise OSError(f"端口 {port} 已被占用")
            
            # 尝试启动服务器
            app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False, threaded=True)
            break  # 成功启动，退出循环
        except Exception as e:
            # 捕获所有异常，不仅仅是OSError
            error_type = type(e).__name__
            error_msg = str(e)
            print(f"[Web服务] 端口 {port} 启动失败: {error_type} - {error_msg}")
            print(f"[Web服务] 尝试端口 {port+1}")
            
            # 记录到日志文件
            with open('log.log', 'a+') as f:
                f.write(f'\n{datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")} Web服务启动错误: 端口={port}, 错误类型={error_type}, 错误信息={error_msg}\n')
            
            port += 1
            if port > max_port:
                final_error_msg = f"[Web服务] 无法找到可用端口（{8080}-{max_port}），Web界面未启动"
                print(final_error_msg)
                app_state["web_status"] = final_error_msg
                
                # 记录到日志文件
                with open('log.log', 'a+') as f:
                    f.write(f'\n{datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")} {final_error_msg}\n')
                break
    
    # 如果成功启动
    if port <= max_port:
        success_msg = f"[Web服务] Web界面成功启动在 http://localhost:{port} 或 http://服务器IP:{port}"
        print(success_msg)
        app_state["web_status"] = success_msg
        
        # 记录到日志文件
        with open('log.log', 'a+') as f:
            f.write(f'\n{datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")} {success_msg}\n')

def create_templates():
    """创建HTML模板"""
    index_html = """<!DOCTYPE html>
<html>
<head>
    <title>StripchatRecorder 状态</title>
    <meta charset="UTF-8">
    <meta http-equiv="refresh" content="10">
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .container { max-width: 900px; margin: 0 auto; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background-color: #f2f2f2; }
        .button { display: inline-block; padding: 10px 15px; background-color: #4CAF50; 
                 color: white; text-decoration: none; border-radius: 4px; margin-top: 20px; }
        .btn-stop { background-color: #f44336; color: white; padding: 5px 10px; 
                  border: none; cursor: pointer; border-radius: 3px; }
        .info { background-color: #e7f3fe; border-left: 6px solid #2196F3; padding: 10px; margin: 10px 0; }
        .progress-bar { height: 20px; background-color: #f2f2f2; border-radius: 4px; overflow: hidden; }
        .progress { height: 100%; background-color: #4CAF50; }
        .progress.warning { background-color: #ff9800; }
        .progress.danger { background-color: #f44336; }
    </style>
</head>
<body>
    <div class="container">
        <h1>StripchatRecorder 状态监控</h1>
        
        <div class="info">
            <p>Web界面运行于端口: {{ port }}</p>
        </div>

        <!-- 存储空间信息 -->
        <h2>存储空间信息</h2>
        <table>
            <tr>
                <th>位置</th>
                <th>总容量</th>
                <th>已使用</th>
                <th>剩余</th>
                <th>使用率</th>
            </tr>
            <tr>
                <td>本地磁盘</td>
                <td>{{ storage_info.local.total }} GB</td>
                <td>{{ storage_info.local.used }} GB</td>
                <td>{{ storage_info.local.free }} GB</td>
                <td>
                    <div class="progress-bar">
                        <div class="progress {% if storage_info.local.percent_used > 90 %}danger{% elif storage_info.local.percent_used > 70 %}warning{% endif %}" 
                             style="width: {{ storage_info.local.percent_used }}%"></div>
                    </div>
                    {{ storage_info.local.percent_used }}%
                </td>
            </tr>
        </table>
        
        {% if repeatedModels %}
        <div class="warning">
            <p>以下模特在wanted列表中重复出现: {{ repeatedModels|join(', ') }}</p>
        </div>
        {% endif %}
        
        <div class="stats">
            <p>活跃线程数: {{ hilos|length }} (每个非录制模特一个线程)</p>
            <p>正在录制的模特数: {{ recording|length }}</p>
            <p>wanted列表中的模特总数: {{ counterModel }}</p>
        </div>
        
        {% if recording %}
        <h2>当前正在录制的模特:</h2>
        <table>
            <tr>
                <th>模特名</th>
                <th>文件名</th>
                <th>操作</th>
            </tr>
            {% for model in recording %}
            <tr>
                <td>{{ model.modelo }}</td>
                <td>{{ model.file.split('/')[-1] }}</td>
                <td>
                    <form action="/stop_recording/{{ model.modelo }}" method="post" style="display: inline;">
                        <button type="submit" class="btn-stop">停止录制</button>
                    </form>
                </td>
            </tr>
            {% endfor %}
        </table>
        {% else %}
        <p>当前没有模特正在录制</p>
        {% endif %}
        
        <a href="/edit_wanted" class="button">编辑 Wanted 列表</a>
    </div>
</body>
</html>"""

    edit_html = """<!DOCTYPE html>
<html>
<head>
    <title>编辑 Wanted 列表</title>
    <meta charset="UTF-8">
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .container { max-width: 900px; margin: 0 auto; }
        textarea { width: 100%; height: 400px; margin-top: 20px; padding: 10px; }
        .button { display: inline-block; padding: 10px 15px; background-color: #4CAF50; 
                 color: white; text-decoration: none; border-radius: 4px; margin-top: 10px;
                 border: none; cursor: pointer; }
        .cancel { background-color: #f44336; margin-left: 10px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>编辑 Wanted 列表</h1>
        <p>每行输入一个模特名称</p>
        
        <form method="post">
            <textarea name="content">{{ content }}</textarea>
            <div>
                <button type="submit" class="button">保存更改</button>
                <a href="/" class="button cancel">取消</a>
            </div>
        </form>
    </div>
</body>
</html>"""

    # 写入模板文件
    with open(os.path.join(mainDir, 'templates', 'index.html'), 'w', encoding='utf-8') as f:
        f.write(index_html)
    
    with open(os.path.join(mainDir, 'templates', 'edit_wanted.html'), 'w', encoding='utf-8') as f:
        f.write(edit_html)

def firstRun():
    subprocess.call('bash t.sh'.split())


def cls():
    os.system('cls' if os.name == 'nt' else 'clear')


def readConfig():
    global setting

    Config.read(mainDir + '/config.conf')
    setting = {
        'save_directory': Config.get('paths', 'save_directory'),
        'wishlist': Config.get('paths', 'wishlist'),
        'interval': int(Config.get('settings', 'checkInterval')),
        'postProcessingCommand': Config.get('settings', 'postProcessingCommand'),
    }
    try:
        setting['postProcessingThreads'] = int(Config.get('settings', 'postProcessingThreads'))
    except ValueError:
        if setting['postProcessingCommand'] and not setting['postProcessingThreads']:
            setting['postProcessingThreads'] = 1

    if not os.path.exists(f'{setting["save_directory"]}'):
        os.makedirs(f'{setting["save_directory"]}')
    
    # 创建与captures平级的up文件夹，用于存放待上传的已完成录制
    captures_parent_dir = os.path.dirname(setting['save_directory'])
    up_dir = os.path.join(captures_parent_dir, 'up')
    setting['up_directory'] = up_dir  # 保存到设置中方便其他函数使用
    if not os.path.exists(up_dir):
        os.makedirs(up_dir)


def process_existing_captures():
    """处理已经存在于captures目录中的录制文件，将它们移动到up目录"""
    import shutil
    import glob
    
    captures_dir = setting['save_directory']
    up_dir = setting['up_directory']  # 使用保存在设置中的up目录路径
    
    # 查找所有模特子目录
    model_dirs = [d for d in os.listdir(captures_dir) if os.path.isdir(os.path.join(captures_dir, d)) and d != 'up']
    
    moved_count = 0
    for model_dir in model_dirs:
        model_path = os.path.join(captures_dir, model_dir)
        # 查找所有MP4文件
        mp4_files = glob.glob(os.path.join(model_path, '*.mp4'))
        
        for file_path in mp4_files:
            # 检查文件是否大于1KB
            if os.path.getsize(file_path) > 1024:
                try:
                    # 创建模特名称对应的up子目录
                    model_up_dir = os.path.join(up_dir, model_dir)
                    if not os.path.exists(model_up_dir):
                        os.makedirs(model_up_dir)
                    
                    filename = os.path.basename(file_path)
                    dest_path = os.path.join(model_up_dir, filename)
                    # 移动文件
                    shutil.move(file_path, dest_path)
                    moved_count += 1
                    # 记录日志
                    with open('log.log', 'a+') as f:
                        f.write(f'\n{datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")} 已存在的文件已移动到上传文件夹: {dest_path}\n')
                except Exception as e:
                    with open('log.log', 'a+') as f:
                        f.write(f'\n{datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")} 移动已存在文件时出错: {file_path} -> {e}\n')
    
    if moved_count > 0:
        print(f"[初始化] 已将 {moved_count} 个现有录制文件移动到上传文件夹")


def postProcess():
    while True:
        while processingQueue.empty():
            time.sleep(1)
        parameters = processingQueue.get()
        model = parameters['model']
        path = parameters['path']
        filename = os.path.split(path)[-1]
        directory = os.path.dirname(path)
        file = os.path.splitext(filename)[0]
        
        # 执行原有的后处理命令
        if setting['postProcessingCommand']:
            subprocess.call(setting['postProcessingCommand'].split() + [path, filename, directory, model, file, 'cam4'])
        
        try:
            # 将文件移动到up文件夹（与captures平级）下对应模特的子目录
            up_dir = setting['up_directory']
            # 创建模特名称对应的up子目录
            model_up_dir = os.path.join(up_dir, model)
            if not os.path.exists(model_up_dir):
                os.makedirs(model_up_dir)
                
            dest_path = os.path.join(model_up_dir, filename)
            
            # 如果文件仍然存在并且大小大于1KB，则移动到up文件夹
            if os.path.isfile(path) and os.path.getsize(path) > 1024:
                import shutil
                shutil.move(path, dest_path)
                print(f"[移动文件] {filename} 已移动到上传文件夹: {model_up_dir}")
                # 记录日志
                with open('log.log', 'a+') as f:
                    f.write(f'\n{datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")} 文件已移动到上传文件夹: {dest_path}\n')
        except Exception as e:
            with open('log.log', 'a+') as f:
                f.write(f'\n{datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")} 移动文件时出错: {e}\n')


class Modelo(threading.Thread):
    def __init__(self, modelo):
        super().__init__()
        self.modelo = modelo
        self._stopevent = threading.Event()
        self.file = None
        self.online = None
        self.lock = threading.Lock()

    def run(self):
        global recording, hilos
        isOnline = self.isOnline()
        if isOnline == False:
            self.online = False
        else:
            self.online = True
            self.file = os.path.join(setting['save_directory'], self.modelo,
                                     f'{datetime.datetime.fromtimestamp(time.time()).strftime("%Y.%m.%d_%H.%M.%S")}_{self.modelo}.mp4')
            try:
                session = streamlink.Streamlink()
                streams = session.streams(f'hlsvariant://{isOnline}')
                stream = streams['best']
                fd = stream.open()
                if not isModelInListofObjects(self.modelo, recording):
                    os.makedirs(os.path.join(setting['save_directory'], self.modelo), exist_ok=True)
                    with open(self.file, 'wb') as f:
                        self.lock.acquire()
                        recording.append(self)
                        for index, hilo in enumerate(hilos):
                            if hilo.modelo == self.modelo:
                                del hilos[index]
                                break
                        self.lock.release()
                        # 添加最后一次检查在线状态的时间
                        last_online_check = time.time()
                        while not (self._stopevent.isSet() or os.fstat(f.fileno()).st_nlink == 0):
                            try:
                                # 每30秒检查一次模特是否仍在线
                                current_time = time.time()
                                if current_time - last_online_check > 30:
                                    if not self.isOnline():
                                        print(f"[检测] 模特 {self.modelo} 已经下线，停止录制")
                                        with open('log.log', 'a+') as log_f:
                                            log_f.write(f'\n{datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")} 模特已下线，停止录制: {self.modelo}\n')
                                        break
                                    last_online_check = current_time
                                
                                # 使用非阻塞读取，设置1秒超时
                                data = fd.read(1024)
                                if not data:  # 如果没有数据，可能是流已经结束
                                    # 再次检查是否在线
                                    if not self.isOnline():
                                        print(f"[检测] 模特 {self.modelo} 已经下线，停止录制")
                                        with open('log.log', 'a+') as log_f:
                                            log_f.write(f'\n{datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")} 模特已下线，停止录制: {self.modelo}\n')
                                        break
                                f.write(data)
                            except Exception as e:
                                with open('log.log', 'a+') as log_f:
                                    log_f.write(f'\n{datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")} 读取流数据异常: {self.modelo} - {e}\n')
                                fd.close()
                                break
                    if setting['postProcessingCommand']:
                        processingQueue.put({'model': self.modelo, 'path': self.file})
            except Exception as e:
                with open('log.log', 'a+') as f:
                    f.write(f'\n{datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")} EXCEPTION: {e}\n')
                self.stop()
            finally:
                self.exceptionHandler()

    def exceptionHandler(self):
        self.stop()
        self.online = False
        self.lock.acquire()
        for index, hilo in enumerate(recording):
            if hilo.modelo == self.modelo:
                del recording[index]
                break
        self.lock.release()
        try:
            file = os.path.join(os.getcwd(), self.file) if os.getcwd() in self.file else self.file
            if os.path.isfile(file):
                if os.path.getsize(file) <= 1024:
                    os.remove(file)
                elif setting['postProcessingCommand'] == '':
                    # 如果没有设置后处理命令，直接将文件移动到上传文件夹
                    up_dir = setting['up_directory']
                    # 创建模特名称对应的up子目录
                    model_up_dir = os.path.join(up_dir, self.modelo)
                    if not os.path.exists(model_up_dir):
                        os.makedirs(model_up_dir)
                        
                    filename = os.path.basename(file)
                    dest_path = os.path.join(model_up_dir, filename)
                    import shutil
                    shutil.move(file, dest_path)
                    print(f"[移动文件] {filename} 已移动到上传文件夹: {model_up_dir}")
                    # 记录日志
                    with open('log.log', 'a+') as f:
                        f.write(f'\n{datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")} 文件已移动到上传文件夹: {dest_path}\n')
        except Exception as e:
            with open('log.log', 'a+') as f:
                f.write(f'\n{datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")} EXCEPTION: {e}\n')

    def isOnline(self):
        try:
            resp = requests.get(f'https://stripchat.com/api/front/v2/models/username/{self.modelo}/cam').json()
            hls_url = ''
            if 'cam' in resp.keys():
                if {'isCamAvailable', 'streamName'} <= resp['cam'].keys():
                    if resp['cam']['isCamAvailable'] and resp['cam']['streamName']:
                        hls_url = f'https://b-hls-13.doppiocdn.live/hls/{resp["cam"]["streamName"]}/{resp["cam"]["streamName"]}.m3u8'
            if len(hls_url):
                return hls_url
            else:
                return False
        except Exception as e:
            return False

    def stop(self):
        self._stopevent.set()


class CleaningThread(threading.Thread):
    def __init__(self):
        super().__init__()
        self.interval = 0
        self.lock = threading.Lock()

    def run(self):
        global hilos, recording
        while True:
            self.lock.acquire()
            new_hilos = []
            for hilo in hilos:
                if hilo.is_alive() or hilo.online:
                    new_hilos.append(hilo)
            hilos = new_hilos
            self.lock.release()
            for i in range(10, 0, -1):
                self.interval = i
                time.sleep(1)


class AddModelsThread(threading.Thread):
    def __init__(self):
        super().__init__()
        self.wanted = []
        self.lock = threading.Lock()
        self.repeatedModels = []
        self.counterModel = 0

    def run(self):
        global hilos, recording, app_state
        lines = open(setting['wishlist'], 'r').read().splitlines()
        self.wanted = (x for x in lines if x)
        self.lock.acquire()
        aux = []
        for model in self.wanted:
            model = model.lower()
            if model in aux:
                self.repeatedModels.append(model)
            else:
                aux.append(model)
                self.counterModel = self.counterModel + 1
                if not isModelInListofObjects(model, hilos) and not isModelInListofObjects(model, recording):
                    thread = Modelo(model)
                    thread.start()
                    hilos.append(thread)
        for hilo in recording:
            if hilo.modelo not in aux:
                hilo.stop()
        # 更新应用状态
        app_state["repeatedModels"] = self.repeatedModels
        app_state["counterModel"] = self.counterModel
        self.lock.release()


def isModelInListofObjects(obj, lista):
    result = False
    for i in lista:
        if i.modelo == obj:
            result = True
            break
    return result


if __name__ == '__main__':
    firstRun()
    readConfig()
    
    # 处理已有的captures文件
    process_existing_captures()
    
    if setting['postProcessingCommand']:
        processingQueue = queue.Queue()
        postprocessingWorkers = []
        for i in range(0, setting['postProcessingThreads']):
            t = threading.Thread(target=postProcess)
            postprocessingWorkers.append(t)
            t.start()
    cleaningThread = CleaningThread()
    cleaningThread.start()
    
    # 启动web服务器
    print("[Web服务] 正在后台启动Web界面...")
    web_thread = threading.Thread(target=start_web_server)
    web_thread.daemon = True  # 设置为守护线程，这样主程序退出时，web服务器也会退出
    web_thread.start()
    
    while True:
        try:
            readConfig()
            addModelsThread = AddModelsThread()
            addModelsThread.start()
            i = 1
            for i in range(setting['interval'], 0, -1):
                cls()
                # 显示Web状态信息
                print(f"[Web服务状态] {app_state['web_status']}")
                print("=" * 50)
                
                if len(addModelsThread.repeatedModels): print(
                    'The following models are more than once in wanted: [\'' + ', '.join(
                        modelo for modelo in addModelsThread.repeatedModels) + '\']')
                print(
                    f'{len(hilos):02d} alive Threads (1 Thread per non-recording model), cleaning dead/not-online Threads in {cleaningThread.interval:02d} seconds, {addModelsThread.counterModel:02d} models in wanted')
                print(f'Online Threads (models): {len(recording):02d}')
                print('The following models are being recorded:')
                for hiloModelo in recording: print(
                    f'  Model: {hiloModelo.modelo}  -->  File: {os.path.basename(hiloModelo.file)}')
                print(f'Next check in {i:02d} seconds\r', end='')
                time.sleep(1)
            addModelsThread.join()
            del addModelsThread, i
        except:
            break
