# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk, messagebox, PhotoImage
import websocket
import time
import os
import base64
from io import BytesIO
from PIL import Image, ImageTk
from Scripts.Utils import dict_result, get_config_path, resource_path
import requests
import json
import threading

class LoginDialog:
    def __init__(self, parent, main_window):
        self.parent = parent
        self.main_window = main_window
        self.top = tk.Toplevel(parent)
        self.top.title("雨课堂登录")
        self.top.geometry("350x500")
        self.top.configure(bg="white")
        self.top.resizable(False, False)
        
        # 窗口居中
        self.center_window()
        
        # 设置窗口图标
        try:
            ico_path = resource_path("UI/Image/favicon.ico")
            if os.path.exists(ico_path):
                self.top.iconbitmap(ico_path)
        except:
            pass
        
        # 初始化变量
        self.flush_on = True
        self.sessionid = ""
        self.login_success = False
        
        # 创建UI
        self.create_ui()
        
        # 启动WebSocket连接
        self.start_wssapp()
        
        # 设置关闭窗口时的回调
        self.top.protocol("WM_DELETE_WINDOW", self.close_window)
        
        # 模态窗口
        self.top.grab_set()
    
    def center_window(self):
        # 窗口居中显示
        self.top.update_idletasks()
        width = self.top.winfo_width()
        height = self.top.winfo_height()
        x = (self.top.winfo_screenwidth() // 2) - (width // 2)
        y = (self.top.winfo_screenheight() // 2) - (height // 2)
        self.top.geometry('{}x{}+{}+{}'.format(width, height, x, y))
    
    def create_ui(self):
        # 创建主框架
        main_frame = tk.Frame(self.top, bg="white")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # 标题标签
        title_label = tk.Label(main_frame, text="微信扫码登录雨课堂", font=("STHeiti", 16), bg="white")
        title_label.pack(pady=(20, 10))
        
        # 提示标签
        hint_label = tk.Label(main_frame, text="注：扫码登录仅用于获取您的登录状态以便软件监听雨课堂信息。", 
                             font=("STHeiti", 8), fg="red", bg="white", wraplength=300, justify=tk.CENTER)
        hint_label.pack(pady=(0, 20))
        
        # 二维码显示区域 - 移除白边
        self.qrcode_frame = tk.Frame(main_frame, bg="white", width=256, height=256)
        self.qrcode_frame.pack(pady=20)
        self.qrcode_frame.pack_propagate(False)  # 防止框架大小被内容改变
        
        # 二维码标签
        self.qrcode_label = tk.Label(self.qrcode_frame, bg="white")
        self.qrcode_label.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)  # 确保没有内边距
        
        # 登录状态标签
        self.status_label = tk.Label(main_frame, text="", font=("STHeiti", 10), fg="red", bg="white")
        self.status_label.pack(pady=10)
    
    def start_wssapp(self):
        def on_open(wsapp):
            data={"op":"requestlogin","role":"web","version":1.4,"type":"qrcode","from":"web"}
            wsapp.send(json.dumps(data))

        def on_close(wsapp):
            print("WebSocket closed")

        def on_message(wsapp, message):
            data = dict_result(message)
            # 二维码刷新
            if data["op"] == "requestlogin":
                img = requests.get(url=data["ticket"], proxies={"http": None, "https": None}).content
                # 使用PIL将字节流转换为ImageTk对象
                pil_img = Image.open(BytesIO(img))
                # 调整图片大小以消除白边
                pil_img = pil_img.resize((256, 256), Image.LANCZOS)
                tk_img = ImageTk.PhotoImage(pil_img)
                # 更新二维码显示
                self.qrcode_label.config(image=tk_img, bg="white")
                self.qrcode_label.image = tk_img  # 保持引用，防止被垃圾回收
            # 扫码且登录成功
            elif data["op"] == "loginsuccess":
                web_login_url = "https://pro.yuketang.cn/pc/web_login"
                login_data = {
                    "UserID": data["UserID"],
                    "Auth": data["Auth"]
                }
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:104.0) Gecko/20100101 Firefox/104.0"
                }
                login_data = json.dumps(login_data)
                # 使用Auth和UserID正式登录获取sessionid
                r = requests.post(url=web_login_url, data=login_data, headers=headers, proxies={"http": None, "https": None})
                sessionid = dict(r.cookies)["sessionid"]
                # 保存sessionid到配置
                self.sessionid = sessionid
                self.config = self.main_window.config
                self.config["sessionid"] = sessionid
                self.save(sessionid)
                self.login_success = True
                self.top.destroy()
            # 其他状态处理
            elif data["op"] == "loginerror":
                self.status_label.config(text="登录失败，请重试")
            elif data["op"] == "scanqr":
                self.status_label.config(text="已扫码，请在手机上确认")
        
        login_wss_url = "wss://pro.yuketang.cn/wsapp/"
        # 开启websocket线程
        self.wsapp = websocket.WebSocketApp(url=login_wss_url, on_open=on_open, on_message=on_message, on_close=on_close)
        self.wsapp_t = threading.Thread(target=self.wsapp.run_forever, daemon=True)
        self.wsapp_t.start()
        
        # 开启定时刷新二维码线程
        self.flush_on = True
        self.flush_t = threading.Thread(target=self._flush_login_QRcode, daemon=True)
        self.flush_t.start()
    
    def _flush_login_QRcode(self):
        # 刷新登录二维码，单独线程运行
        count = 0
        # 便于退出的sleep
        while self.flush_on:
            if count == 60:
                count = 0
                data={"op":"requestlogin","role":"web","version":1.4,"type":"qrcode","from":"web"}
                try:
                    self.wsapp.send(json.dumps(data))
                except:
                    pass
            else:
                time.sleep(1)
                count += 1
    
    def save(self, sessionid):
        # 保存sessionid
        config = self.config
        config["sessionid"] = sessionid
        config_path = get_config_path()
        with open(config_path, "w+") as f:
            json.dump(config, f)
    
    def close_window(self):
        # 关闭窗口时的清理工作
        self.flush_on = False
        if hasattr(self, 'wsapp'):
            self.wsapp.close()
        self.top.destroy()
