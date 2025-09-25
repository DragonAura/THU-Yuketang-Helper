import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import os
import datetime
from UI.Login import LoginDialog
from UI.Config import ConfigDialog
from Scripts.Utils import *
from Scripts.Monitor import monitor

class MainWindow:
    def __init__(self, master):
        self.master = master
        self.master.geometry("800x700")
        self.master.configure(bg="white")
        
        # 加载配置
        self.load_config()
        
        # 对象变量初始化
        self.table_index = []
        self.is_active = False
        
        # 创建UI
        self.create_ui()
        
        # 绑定事件
        self.bind_events()
        
        # 初始化日志
        self.add_message("程序已启动", 0)
        
    def load_config(self):
        # 加载配置文件
        config_path = get_config_path()
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                self.config = json.load(f)
        else:
            self.config = get_initial_data()
            with open(config_path, 'w') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=4)
    
    def create_ui(self):
        # 创建菜单栏
        self.create_menu()
        
        # 创建课程表格
        self.create_table()
        
        # 创建消息区域
        self.create_message_area()
    
    def create_menu(self):
        menu_frame = tk.Frame(self.master, bg="#111111", height=60)
        menu_frame.pack(fill=tk.X)
        
        # Logo和标题
        logo_frame = tk.Frame(menu_frame, bg="#111111")
        logo_frame.pack(side=tk.LEFT, padx=10, pady=10)
        
        # 由于tkinter不直接支持QPixmap，这里使用标签代替
        title_label = tk.Label(logo_frame, text="清华大学雨课堂助手", font=("STHeiti", 16), fg="white", bg="#111111")
        title_label.pack(side=tk.LEFT, padx=10)
        
        # 按钮区域
        button_frame = tk.Frame(menu_frame, bg="#111111")
        button_frame.pack(side=tk.RIGHT, padx=10, pady=10)
        
        self.active_btn = tk.Button(button_frame, text="启动监听", bg="white", width=12)
        self.active_btn.pack(side=tk.LEFT, padx=5)
        
        self.login_btn = tk.Button(button_frame, text="登录", bg="white", width=12)
        self.login_btn.pack(side=tk.LEFT, padx=5)
        
        self.config_btn = tk.Button(button_frame, text="设置", bg="white", width=12)
        self.config_btn.pack(side=tk.LEFT, padx=5)
    
    def create_table(self):
        table_frame = tk.Frame(self.master, bg="white")
        table_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # 表格标题
        title_label = tk.Label(table_frame, text="课程列表", font=("STHeiti", 12), bg="white")
        title_label.pack(anchor=tk.W, pady=5)
        
        # 创建表格
        columns = ("course_name", "status", "progress")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=15)
        
        # 定义列
        self.tree.heading("course_name", text="课程名称")
        self.tree.heading("status", text="状态")
        self.tree.heading("progress", text="进度")
        
        # 设置列宽
        self.tree.column("course_name", width=300, anchor=tk.W)
        self.tree.column("status", width=150, anchor=tk.CENTER)
        self.tree.column("progress", width=150, anchor=tk.CENTER)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        
        # 放置表格和滚动条
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def create_message_area(self):
        message_frame = tk.Frame(self.master, bg="white")
        message_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # 消息区域标题
        title_label = tk.Label(message_frame, text="系统消息", font=("STHeiti", 12), bg="white")
        title_label.pack(anchor=tk.W, pady=5)
        
        # 创建消息文本框
        self.message_text = scrolledtext.ScrolledText(message_frame, wrap=tk.WORD, height=10, font=("STHeiti", 10))
        self.message_text.pack(fill=tk.BOTH, expand=True)
        self.message_text.config(state=tk.DISABLED)
    
    def bind_events(self):
        self.active_btn.config(command=self.toggle_monitor)
        self.login_btn.config(command=self.show_login)
        self.config_btn.config(command=self.show_config)
    
    def toggle_monitor(self):
        if not self.is_active:
            # 启动监听
            if not self.config.get("sessionid", ""):
                self.add_message("请先登录", 8)
                return
            
            self.is_active = True
            self.active_btn.config(text="停止监听")
            
            # 启动监听线程
            self.monitor_thread = threading.Thread(target=monitor, args=(self,), daemon=True)
            self.monitor_thread.start()
            
            self.add_message("监听已启动", 0)
        else:
            # 停止监听
            self.is_active = False
            self.active_btn.config(text="启动监听")
            self.add_message("监听已停止", 0)
    
    def show_login(self):
        login_dialog = LoginDialog(self.master, self)
    
    def show_config(self):
        config_dialog = ConfigDialog(self.master, self)
    
    def add_message(self, text, level):
        # 0: 普通信息 7: 课程信息 8: 错误信息
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message = f"[{now}] {text}\n"
        
        self.message_text.config(state=tk.NORMAL)
        self.message_text.insert(tk.END, message)
        
        # 根据级别设置颜色
        if level == 8:
            # 错误信息红色
            last_line = self.message_text.index(f"end-2l linestart")
            self.message_text.tag_add("error", last_line, "end-1l")
            self.message_text.tag_config("error", foreground="red")
        elif level == 7:
            # 课程信息绿色
            last_line = self.message_text.index(f"end-2l linestart")
            self.message_text.tag_add("course", last_line, "end-1l")
            self.message_text.tag_config("course", foreground="green")
        
        self.message_text.see(tk.END)
        self.message_text.config(state=tk.DISABLED)
    
    def add_course(self, course_info, index):
        # 添加课程到表格
        course_name, status, progress = course_info
        self.tree.insert("", tk.END, values=(course_name, status, progress))
    
    def del_course(self, index):
        # 删除课程
        # 注意：由于tkinter的Treeview没有直接的索引删除，这里需要根据实际情况调整
        pass
    
    def save_config(self):
        # 保存配置
        config_path = get_config_path()
        with open(config_path, 'w') as f:
            json.dump(self.config, f, ensure_ascii=False, indent=4)