import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import os
import datetime
import time
import requests
import json
from PIL import Image, ImageTk
from UI.Login import LoginDialog
from UI.Config import ConfigDialog
from UI.ProblemListWindow import ProblemListWindow
from UI.ProblemDetailWindow import ProblemDetailWindow
from Scripts.Utils import *
from Scripts.Classes import Lesson
from dashscope import MultiModalConversation

# 导入测试数据模块
from UI.TestData import get_test_lessons, create_test_lesson

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
        # 添加测试模式标志
        self.test_mode = False
        
        # 课程相关变量
        self.on_lesson_list = []  # 已经签到完成加入监听列表的课程
        self.lesson_list = []     # 检测到的未加入监听列表的课程
        
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
        
        # 添加测试模式按钮
        self.test_mode_btn = tk.Button(button_frame, text="测试模式", bg="white", width=12)
        self.test_mode_btn.pack(side=tk.LEFT, padx=5)
        
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
        self.test_mode_btn.config(command=self.toggle_test_mode)
        self.login_btn.config(command=self.show_login)
        self.config_btn.config(command=self.show_config)
        # 绑定课程列表点击事件
        self.tree.bind("<ButtonRelease-1>", self.on_course_click)
    
    def on_course_click(self, event):
        """课程列表点击事件处理"""
        item = self.tree.selection()
        if item:
            # 获取选中的课程
            course_name = self.tree.item(item[0], "values")[0]
            # 在已监听课程列表中查找对应的课程对象
            for lesson in self.on_lesson_list:
                if lesson.lessonname == course_name:
                    # 创建并显示题目列表窗口
                    self.problem_window = ProblemListWindow(self.master, course_name, lesson.problems_ls)
                    break
    
    def toggle_test_mode(self):
        """切换测试模式"""
        if not self.test_mode:
            # 进入测试模式
            self.test_mode = True
            self.test_mode_btn.config(text="退出测试", bg="yellow")
            self.active_btn.config(state=tk.DISABLED)
            self.login_btn.config(state=tk.DISABLED)
            
            # 加载测试课程
            self.load_test_data()
            
            self.add_message("已进入测试模式，加载了测试课程'test'及其题目", 0)
        else:
            # 退出测试模式
            self.test_mode = False
            self.test_mode_btn.config(text="测试模式", bg="white")
            self.active_btn.config(state=tk.NORMAL)
            self.login_btn.config(state=tk.NORMAL)
            
            # 清除课程表格
            for item in self.tree.get_children():
                self.tree.delete(item)
            
            # 清空课程列表
            self.lesson_list = []
            self.on_lesson_list = []
            
            self.add_message("已退出测试模式", 0)
    
    def load_test_data(self):
        """加载测试数据"""
        # 获取测试课程列表
        self.lesson_list = get_test_lessons()
        
        # 创建测试课程对象
        test_lesson = create_test_lesson(self)
        self.on_lesson_list.append(test_lesson)
        
        # 更新课程表格
        self.update_course_table()
    
    def toggle_monitor(self):
        if not self.is_active:
            # 启动监听
            if not self.config.get("sessionid", ""):
                self.add_message("请先登录", 8)
                return
            
            self.is_active = True
            self.active_btn.config(text="停止监听")
            
            # 启动监听线程
            self.monitor_thread = threading.Thread(target=self.monitor, daemon=True)
            self.monitor_thread.start()
            
            self.add_message("监听已启动", 0)
        else:
            # 停止监听
            self.is_active = False
            self.active_btn.config(text="启动监听")
            
            # 清除课程表格
            for item in self.tree.get_children():
                self.tree.delete(item)
            
            self.add_message("监听已停止", 0)
    
    def monitor(self):
        # 监听器函数
        def del_onclass(lesson_obj):
            # 作为回调函数传入start_lesson
            if lesson_obj in self.on_lesson_list:
                self.on_lesson_list.remove(lesson_obj)
                # 从UI中移除课程
                self.update_course_table()
        
        network_status = True
        sessionid = self.config["sessionid"]
        
        while self.is_active:
            # 获取课程列表
            try:
                self.lesson_list = get_on_lesson(sessionid)
            except requests.exceptions.ConnectionError:
                meg = "网络异常，监听中断"
                self.add_message(meg, 8)
                network_status = False
            except Exception as e:
                self.add_message(f"获取课程列表异常: {str(e)}", 8)
            
            # 网络异常处理
            while self.is_active and not network_status:
                ret = test_network()
                if ret == True:
                    try:
                        self.lesson_list = get_on_lesson(sessionid)
                    except Exception as e:
                        self.add_message(f"恢复网络后获取课程列表异常: {str(e)}", 8)
                    else:
                        network_status = True
                        meg = "网络已恢复，监听开始"
                        self.add_message(meg, 8)
                        break
                # 可结束线程的计时器
                timer = 0
                while self.is_active and timer <= 5:
                    time.sleep(1)
                    timer += 1
                    if not self.is_active:
                        break
            if not self.is_active:
                break
            
            # 更新课程表格
            self.update_course_table()
            
            # 检查新课程
            for lesson in self.lesson_list:
                # 如果课程不在已监听列表中，并且课程已经开始
                if not any(lesson_obj.lessonid == lesson["lessonId"] for lesson_obj in self.on_lesson_list) and lesson["status"] == 1:
                    # 创建课程对象
                    lesson_obj = Lesson(lesson["lessonId"], lesson["courseName"], lesson["classroomId"], self)
                    # 将课程添加到监听列表
                    self.on_lesson_list.append(lesson_obj)
                    # 开始监听课程
                    lesson_obj.start_lesson(del_onclass)
                    # 更新课程表格
                    self.update_course_table()
                    break
            # 每5秒检查一次
            time.sleep(5)
    
    def update_course_table(self):
        # 在主线程中更新UI
        def update():
            # 清空表格
            for item in self.tree.get_children():
                self.tree.delete(item)
            
            # 添加课程
            for lesson in self.lesson_list:
                status = "进行中" if lesson["status"] == 1 else "未开始"
                self.tree.insert("", "end", values=(lesson["courseName"], status, lesson["progress"]))
        
        # 在主线程中执行
        self.master.after(0, update)
    
    def show_login(self):
        # 显示登录对话框
        login_dialog = LoginDialog(self.master)
        self.master.wait_window(login_dialog.top)
        # 重新加载配置
        self.load_config()
    
    def show_config(self):
        # 显示设置对话框
        config_dialog = ConfigDialog(self.master, self)
        self.master.wait_window(config_dialog.top)
        # 重新加载配置
        self.load_config()
    
    def add_message(self, message, type=0):
        # 添加消息到消息区域
        def add():
            self.message_text.config(state=tk.NORMAL)
            # 获取当前时间
            now = datetime.datetime.now().strftime("%H:%M:%S")
            # 根据类型添加不同的前缀
            prefix = "[信息]" if type == 0 else "[警告]" if type == 8 else "[错误]" if type == 4 else "[其他]"
            # 添加消息
            self.message_text.insert(tk.END, f"{now} {prefix} {message}\n")
            # 滚动到底部
            self.message_text.see(tk.END)
            self.message_text.config(state=tk.DISABLED)
        
        # 在主线程中执行
        self.master.after(0, add)