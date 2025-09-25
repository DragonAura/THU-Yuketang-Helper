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
from Scripts.Utils import *
from Scripts.Classes import Lesson
from dashscope import MultiModalConversation

# 导入测试数据模块
from UI.TestData import get_test_lessons, create_test_lesson

class ProblemDetailWindow:
    """问题详情窗口"""
    def __init__(self, master, problem):
        self.window = tk.Toplevel(master)
        self.window.title(f"问题详情 - 页码: {problem.get('page', 'N/A')}")
        self.window.geometry("900x700")
        self.problem = problem
        
        # 创建UI组件
        self.create_ui()
        
        # 初始化AI key输入框的值
        self.load_ai_key()
    
    def load_ai_key(self):
        # 从环境变量或配置中加载AI key
        ai_key = os.getenv("API_KEY_QWEN", "")
        self.ai_key_entry.delete(0, tk.END)
        self.ai_key_entry.insert(0, ai_key)
    
    def create_ui(self):
        # 创建主框架
        main_frame = tk.Frame(self.window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 第一行：问题内容
        content_frame = tk.Frame(main_frame)
        content_frame.pack(fill=tk.X, pady=5)
        
        content_label = tk.Label(content_frame, text="问题内容:", font=("STHeiti", 12, "bold"))
        content_label.pack(anchor=tk.W)
        
        problem_content = tk.Text(content_frame, font=("STHeiti", 10), wrap=tk.WORD, height=3)
        problem_content.pack(fill=tk.X, expand=True, pady=5)
        problem_content.insert(tk.END, self.problem.get('body', '无问题内容'))
        problem_content.config(state=tk.DISABLED)
        
        # 第二行：问题图片
        image_frame = tk.Frame(main_frame)
        image_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        image_label = tk.Label(image_frame, text="问题图片:", font=("STHeiti", 12, "bold"))
        image_label.pack(anchor=tk.W)
        
        # 图片容器
        self.image_container = tk.Label(image_frame)
        self.image_container.pack(fill=tk.BOTH, expand=True)
        
        # 尝试加载并显示图片
        self.load_and_display_image()
        
        # 第三行：AI答题按钮和key输入
        ai_frame = tk.Frame(main_frame)
        ai_frame.pack(fill=tk.X, pady=5)
        
        ai_label = tk.Label(ai_frame, text="AI答题:", font=("STHeiti", 12, "bold"))
        ai_label.pack(anchor=tk.W)
        
        # AI key输入和按钮
        input_frame = tk.Frame(ai_frame)
        input_frame.pack(fill=tk.X, pady=5)
        
        key_label = tk.Label(input_frame, text="AI Key:", font=("STHeiti", 10))
        key_label.pack(side=tk.LEFT, padx=5)
        
        self.ai_key_entry = tk.Entry(input_frame, font=("STHeiti", 10), width=40)
        self.ai_key_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        self.ai_answer_btn = tk.Button(input_frame, text="AI 答题", font=("STHeiti", 10), 
                                     command=self.on_ai_answer_click)
        self.ai_answer_btn.pack(side=tk.RIGHT, padx=5)
        
        # 第四行：根据problemType渲染答题区域
        answer_frame = tk.Frame(main_frame)
        answer_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        answer_label = tk.Label(answer_frame, text="您的答案:", font=("STHeiti", 12, "bold"))
        answer_label.pack(anchor=tk.W)
        
        # 根据问题类型创建不同的答题区域
        self.answer_vars = []
        self.answer_entries = []
        
        if self.problem.get('problemType') == 1:  # 单选题
            self.create_radio_answer_area(answer_frame)
        elif self.problem.get('problemType') == 2 or self.problem.get('problemType') == 3:  # 多选题
            self.create_check_answer_area(answer_frame)
        elif self.problem.get('blanks'):  # 填空题
            self.create_fill_answer_area(answer_frame)
        
        # 第五行：取消/确认按钮
        button_frame = tk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        self.cancel_btn = tk.Button(button_frame, text="取消", font=("STHeiti", 10), 
                                  width=15, command=self.on_cancel_click)
        self.cancel_btn.pack(side=tk.RIGHT, padx=10)
        
        self.confirm_btn = tk.Button(button_frame, text="确认", font=("STHeiti", 10), 
                                  width=15, command=self.on_confirm_click)
        self.confirm_btn.pack(side=tk.RIGHT, padx=10)

    def on_cancel_click(self):
        """取消按钮点击事件"""
        self.window.destroy()

    def on_confirm_click(self):
        """确认按钮点击事件"""
        # 根据问题类型读取当前UI中的答案
        if self.problem.get('problemType') == 1:  # 单选题
            answer = [self.answer_var.get()]
        elif self.problem.get('problemType') == 2 or self.problem.get('problemType') == 3:  # 多选题
            answer = [key for key, var in self.answer_vars if var.get()]
        elif self.problem.get('blanks'):  # 填空题
            answer = [entry.get() for entry in self.answer_entries]
        
        # 将答案写回到原始的problem对象
        self.problem['answers'] = answer
        
        messagebox.showinfo("提示", "答案已保存")
        self.window.destroy()

    def _update_answer_ui(self, ai_answer):
        # 根据问题类型更新答案UI
        if not ai_answer:
            messagebox.showinfo("提示", "AI未返回有效答案")
            return
        
        if self.problem.get('problemType') == 1:  # 单选题
            if ai_answer:
                self.answer_var.set(ai_answer[0])
        elif self.problem.get('problemType') == 2 or self.problem.get('problemType') == 3:  # 多选题
            # 先取消所有选择
            for key, var in self.answer_vars:
                var.set(False)
            
            # 根据AI答案选择对应的选项
            for key, var in self.answer_vars:
                if key in ai_answer:
                    var.set(True)
        elif self.problem.get('blanks'):  # 填空题
            for i, entry in enumerate(self.answer_entries):
                if i < len(ai_answer):
                    entry.delete(0, tk.END)
                    entry.insert(0, ai_answer[i])
        
        messagebox.showinfo("提示", "AI答题完成，请点击确认保存答案")

    def load_and_display_image(self):
        # 尝试加载并显示图片
        image_path = self.problem.get('image', '')
        if image_path and os.path.exists(image_path):
            try:
                # 打开图片
                image = Image.open(image_path)
                # 调整图片大小以适应窗口
                max_width = 800
                max_height = 400
                width, height = image.size
                ratio = min(max_width/width, max_height/height)
                new_width = int(width * ratio)
                new_height = int(height * ratio)
                image = image.resize((new_width, new_height), Image.LANCZOS)
                
                # 转换为tkinter可用的图片
                photo = ImageTk.PhotoImage(image)
                
                # 保存引用，防止被垃圾回收
                self.image_photo = photo
                
                # 显示图片
                self.image_container.config(image=photo)
            except Exception as e:
                self.image_container.config(text=f"图片加载失败: {str(e)}")
        else:
            self.image_container.config(text="无图片")
    
    def create_radio_answer_area(self, parent):
        # 创建单选题答题区域
        options = self.problem.get('options', [])
        default_answer = self.problem.get('answers', [])[0] if self.problem.get('answers') else ''
        
        self.answer_var = tk.StringVar(value=default_answer)
        
        for option in options:
            key = option.get('key', '')
            value = option.get('value', '')
            
            frame = tk.Frame(parent)
            frame.pack(fill=tk.X, padx=10, pady=2)
            
            radio = tk.Radiobutton(frame, text=f"{key}: {value}", variable=self.answer_var, value=key, 
                                 font=("STHeiti", 10), anchor=tk.W)
            radio.pack(fill=tk.X, padx=10)
    
    def create_check_answer_area(self, parent):
        # 创建多选题答题区域
        options = self.problem.get('options', [])
        default_answers = self.problem.get('answers', [])
        
        self.answer_vars = []
        
        for option in options:
            key = option.get('key', '')
            value = option.get('value', '')
            
            var = tk.BooleanVar(value=key in default_answers)
            self.answer_vars.append((key, var))
            
            frame = tk.Frame(parent)
            frame.pack(fill=tk.X, padx=10, pady=2)
            
            check = tk.Checkbutton(frame, text=f"{key}: {value}", variable=var, 
                                 font=("STHeiti", 10), anchor=tk.W)
            check.pack(fill=tk.X, padx=10)
    
    def create_fill_answer_area(self, parent):
        # 创建填空题答题区域
        blanks_count = len(self.problem.get('blanks', []))
        default_answers = self.problem.get('answers', [])
        
        self.answer_entries = []
        
        for i in range(blanks_count):
            frame = tk.Frame(parent)
            frame.pack(fill=tk.X, padx=10, pady=2)
            
            label = tk.Label(frame, text=f"填空{i+1}: ", font=("STHeiti", 10), width=10, anchor=tk.W)
            label.pack(side=tk.LEFT, padx=5)
            
            entry = tk.Entry(frame, font=("STHeiti", 10))
            entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
            
            # 设置默认值
            if i < len(default_answers):
                entry.delete(0, tk.END)
                entry.insert(0, default_answers[i])
            
            self.answer_entries.append(entry)
    
    def on_ai_answer_click(self):
        # AI答题按钮点击事件
        # 获取AI key
        ai_key = self.ai_key_entry.get()
        if not ai_key:
            # 如果没有输入key，显示一个提示
            messagebox.showwarning("提示", "请输入AI Key")
            return
        
        # 模拟AI思考过程
        self.ai_answer_btn.config(state=tk.DISABLED, text="AI 思考中...")
        self.window.update()
        
        # 启动一个线程来调用AI接口，避免阻塞UI
        ai_thread = threading.Thread(target=self._call_ai_api, args=(ai_key,))
        ai_thread.daemon = True
        ai_thread.start()
    
    def _call_ai_api(self, ai_key):
        try:
            # 这里应该实现真正的AI API调用逻辑
            # 参考Classes.py中的get_problems方法
            image_path = self.problem.get('image', '')
            
            if image_path and os.path.exists(image_path):
                # 构建消息
                messages = [
                    {"role": "system", "content": [{"text": "You are a helpful assistant."}]},
                    {
                        'role':'user',
                        'content': [
                            {'image': f"file://{os.path.abspath(image_path)}"},
                            {'text': '请以JSON格式回答图片中的问题。如果是选择题，则返回{{"question": "问题", "answer": ["选项（A/B/C/...）"]}}，选项为圆形则为单选，选项为矩形则为多选；如果是填空题，则返回{{"question": "问题", "answer": ["填空1答案", "填空2答案", ...]}}'}
                        ]
                    }
                ]
                
                # 实际的API调用
                response = MultiModalConversation.call(
                    api_key=ai_key,
                    model='qwen-vl-max-latest',
                    messages=messages,
                    response_format={"type": "json_object"},
                    vl_high_resolution_images=True)
                
                # 解析API返回结果
                json_output = response["output"]["choices"][0]["message"].content[0]["text"]
                res = json.loads(json_output)
                
                # 获取答案
                ai_answer = res.get('answer', [])
                
                # 在主线程中更新UI
                self.window.after(0, self._update_answer_ui, ai_answer)
            else:
                # 没有图片的情况，只使用文本问题
                # 这里可以实现纯文本的API调用
                messagebox.showinfo("提示", "该问题没有图片，无法使用AI答题功能")
                
        except json.JSONDecodeError as e:
            # JSON解析错误处理
            self.window.after(0, lambda: messagebox.showerror("错误", f"AI返回结果解析失败: {str(e)}"))
        except Exception as e:
            # 其他错误处理
            self.window.after(0, lambda: messagebox.showerror("错误", f"AI答题失败: {str(e)}"))
        finally:
            # 在主线程中恢复按钮状态
            self.window.after(0, lambda: self.ai_answer_btn.config(state=tk.NORMAL, text="AI 答题"))

class ProblemListWindow:
    """显示课程题目列表的窗口"""
    def __init__(self, master, lesson_name, problems_ls):
        self.window = tk.Toplevel(master)
        self.window.title(f"{lesson_name} - 题目列表")
        self.window.geometry("800x600")
        self.problems_ls = problems_ls
        
        # 创建题目列表
        self.create_problem_list()
    
    def create_problem_list(self):
        # 创建滚动窗口
        frame = tk.Frame(self.window)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 创建标题
        title_label = tk.Label(frame, text="题目列表", font=("STHeiti", 12))
        title_label.pack(anchor=tk.W, pady=5)
        
        # 创建滚动条
        scrollbar = ttk.Scrollbar(frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 创建Canvas
        canvas = tk.Canvas(frame, yscrollcommand=scrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=canvas.yview)
        
        # 创建内部框架
        inner_frame = tk.Frame(canvas)
        canvas_window = canvas.create_window((0, 0), window=inner_frame, anchor="nw")
        
        # 绑定事件，确保Canvas大小适应内容
        def on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        
        inner_frame.bind("<Configure>", on_frame_configure)
        
        # 添加题目项
        for idx, problem in enumerate(self.problems_ls):
            # 创建问题项
            problem_frame = tk.Frame(inner_frame, bd=1, relief=tk.RAISED)
            problem_frame.pack(fill=tk.X, pady=5, padx=5)
            problem_frame.bind("<Button-1>", lambda e, p=problem: self.on_problem_click(p))
            problem_frame.config(cursor="hand2")
            
            # 页码
            page_label = tk.Label(problem_frame, text=f"页码: {problem.get('page', 'N/A')}", 
                                font=("STHeiti", 10), width=15, anchor=tk.W, cursor="hand2")
            page_label.pack(side=tk.LEFT, padx=5, pady=5)
            page_label.bind("<Button-1>", lambda e, p=problem: self.on_problem_click(p))
            
            # 问题内容
            content_label = tk.Label(problem_frame, text=f"{problem.get('body', '无问题内容')}", 
                                   font=("STHeiti", 10), wraplength=600, justify=tk.LEFT, cursor="hand2")
            content_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, pady=5)
            content_label.bind("<Button-1>", lambda e, p=problem: self.on_problem_click(p))
    
    def on_problem_click(self, problem):
        """题目点击事件处理"""
        # 创建并显示问题详情窗口
        self.problem_detail_window = ProblemDetailWindow(self.window, problem)

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
        config_dialog = ConfigDialog(self.master)
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