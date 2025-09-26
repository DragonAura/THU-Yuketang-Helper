import tkinter as tk
from tkinter import ttk, messagebox
import json
import functools
from Scripts.Utils import get_config_path, resource_path

class ConfigDialog:
    def __init__(self, parent, main_window):
        self.parent = parent
        self.main_window = main_window
        self.top = tk.Toplevel(parent)
        self.top.title("雨课堂助手设置")
        self.top.geometry("430x550")
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
        
        # 初始化配置
        self.config = main_window.config.copy()
        
        # 创建UI
        self.create_ui()
        
        # 加载配置
        self.load_config()
        
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
        # 创建滚动区域
        self.scrollbar = tk.Scrollbar(self.top)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.canvas = tk.Canvas(self.top, yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.scrollbar.config(command=self.canvas.yview)
        
        # 创建内容框架
        self.content_frame = tk.Frame(self.canvas, bg="white")
        self.canvas_window = self.canvas.create_window((0, 0), window=self.content_frame, anchor=tk.NW)
        
        # 绑定事件以更新滚动区域
        self.content_frame.bind("<Configure>", self.on_frame_configure)
        self.canvas.bind("<Configure>", self.on_canvas_configure)
        
        # 创建各个配置区域
        self.create_danmu_config()
        self.create_auto_answer_config()
        self.create_ai_config()
        self.create_button_area()
    
    def on_frame_configure(self, event=None):
        # 更新滚动区域
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def on_canvas_configure(self, event=None):
        # 调整内容框架宽度以匹配画布
        self.canvas.itemconfig(self.canvas_window, width=event.width)
    
    def create_danmu_config(self):
        # 弹幕设置区域
        danmu_frame = tk.LabelFrame(self.content_frame, text="弹幕设置", font=("STHeiti", 10), bg="white")
        danmu_frame.pack(fill=tk.X, padx=20, pady=10, ipady=10)
        
        # 启用弹幕复选框
        self.danmu_on_var = tk.BooleanVar()
        self.danmu_on = tk.Checkbutton(danmu_frame, text="启用自动发送弹幕", variable=self.danmu_on_var, 
                                      font=("STHeiti", 9), bg="white", command=self.toggle_danmu_settings)
        self.danmu_on.pack(anchor=tk.W, pady=5)
        
        # 弹幕设置详细选项
        self.danmu_settings_frame = tk.Frame(danmu_frame, bg="white")
        self.danmu_settings_frame.pack(fill=tk.X, padx=20)
        
        # 弹幕数量标签
        danmu_label = tk.Label(self.danmu_settings_frame, text="每门课程最多自动发送弹幕数量:", 
                              font=("STHeiti", 9), bg="white")
        danmu_label.pack(anchor=tk.W, pady=5)
        
        # 弹幕数量选择器
        self.danmu_spinbox_var = tk.IntVar()
        self.danmu_spinbox = tk.Spinbox(self.danmu_settings_frame, from_=1, to=100, width=10, 
                                       textvariable=self.danmu_spinbox_var, font=("STHeiti", 9))
        self.danmu_spinbox.pack(anchor=tk.W, pady=5)
    

    
    def create_auto_answer_config(self):
        # 自动答题设置区域
        answer_frame = tk.LabelFrame(self.content_frame, text="自动答题设置", font=("STHeiti", 10), bg="white")
        answer_frame.pack(fill=tk.X, padx=20, pady=10, ipady=10)
        
        # 启用自动答题复选框
        self.auto_answer_var = tk.BooleanVar()
        self.auto_answer = tk.Checkbutton(answer_frame, text="启用自动答题", variable=self.auto_answer_var, 
                                         font=("STHeiti", 9), bg="white", command=self.toggle_answer_settings)
        self.auto_answer.pack(anchor=tk.W, pady=5)
        
        # 自动答题设置详细选项
        self.answer_settings_frame = tk.Frame(answer_frame, bg="white")
        self.answer_settings_frame.pack(fill=tk.X, padx=20)
        
        # 延迟类型选择
        delay_type_frame = tk.Frame(self.answer_settings_frame, bg="white")
        delay_type_frame.pack(fill=tk.X, pady=5)
        
        self.delay_type_var = tk.IntVar(value=1)
        
        tk.Radiobutton(delay_type_frame, text="随机延迟", variable=self.delay_type_var, value=1, 
                      font=("STHeiti", 9), bg="white", command=self.toggle_delay_custom).pack(anchor=tk.W)
        
        tk.Radiobutton(delay_type_frame, text="固定延迟", variable=self.delay_type_var, value=2, 
                      font=("STHeiti", 9), bg="white", command=self.toggle_delay_custom).pack(anchor=tk.W, pady=(5, 0))
        
        # 自定义延迟设置
        self.delay_custom_frame = tk.Frame(self.answer_settings_frame, bg="white")
        self.delay_custom_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(self.delay_custom_frame, text="自定义延迟时间(秒):", 
                font=("STHeiti", 9), bg="white").pack(anchor=tk.W)
        
        self.custom_time_var = tk.IntVar(value=0)
        self.custom_time_spinbox = tk.Spinbox(self.delay_custom_frame, from_=0, to=60, width=10, 
                                            textvariable=self.custom_time_var, font=("STHeiti", 9))
        self.custom_time_spinbox.pack(anchor=tk.W, pady=5)
    
    def create_ai_config(self):
        # AI设置区域
        ai_frame = tk.LabelFrame(self.content_frame, text="AI设置", font=("STHeiti", 10), bg="white")
        ai_frame.pack(fill=tk.X, padx=20, pady=10, ipady=10)
        
        # AI Key标签
        ai_key_label = tk.Label(ai_frame, text="AI API Key:", 
                              font=("STHeiti", 9), bg="white")
        ai_key_label.pack(anchor=tk.W, pady=5)
        
        # AI Key输入框
        self.ai_key_var = tk.StringVar()
        self.ai_key_entry = tk.Entry(ai_frame, textvariable=self.ai_key_var, width=50, 
                                    font=("STHeiti", 9), show="*")
        self.ai_key_entry.pack(anchor=tk.W, pady=5)
        
        # 显示/隐藏密码按钮
        self.show_key_var = tk.BooleanVar()
        self.show_key_check = tk.Checkbutton(ai_frame, text="显示Key", variable=self.show_key_var, 
                                           font=("STHeiti", 9), bg="white", command=self.toggle_key_visibility)
        self.show_key_check.pack(anchor=tk.W, pady=5)
        
    def toggle_key_visibility(self):
        # 切换AI Key的显示/隐藏
        if self.show_key_var.get():
            self.ai_key_entry.config(show="")
        else:
            self.ai_key_entry.config(show="*")
            
    def create_button_area(self):
        # 按钮区域
        button_frame = tk.Frame(self.content_frame, bg="white")
        button_frame.pack(fill=tk.X, padx=20, pady=20)
        
        # 保存按钮
        save_button = tk.Button(button_frame, text="保存设置", command=self.save_config, width=15, 
                              font=("STHeiti", 9), bg="#f0f0f0")
        save_button.pack(anchor=tk.CENTER)
    
    def load_config(self):
        # 加载配置到UI控件
        # 弹幕设置
        self.danmu_on_var.set(self.config.get("auto_danmu", True))
        self.danmu_spinbox_var.set(self.config.get("danmu_config", {}).get("danmu_limit", 5))
        

        
        # 自动答题设置
        self.auto_answer_var.set(self.config.get("auto_answer", True))
        answer_delay = self.config.get("answer_config", {}).get("answer_delay", {})
        self.delay_type_var.set(answer_delay.get("type", 1))
        self.custom_time_var.set(answer_delay.get("custom", {}).get("time", 0))
        
        # AI设置
        self.ai_key_var.set(self.config.get("ai_config", {}).get("api_key", ""))
        
        # 初始化UI状态
        self.toggle_danmu_settings()
        self.toggle_answer_settings()
        self.toggle_delay_custom()
    
    def toggle_danmu_settings(self):
        # 切换弹幕设置区域的可用状态
        state = tk.NORMAL if self.danmu_on_var.get() else tk.DISABLED
        
        for child in self.danmu_settings_frame.winfo_children():
            # 只对支持state选项的控件设置状态
            if hasattr(child, 'config') and 'state' in child.config():
                child.config(state=state)
    

    
    def toggle_answer_settings(self):
        # 切换自动答题设置区域的可用状态
        state = tk.NORMAL if self.auto_answer_var.get() else tk.DISABLED
        
        # 直接控制单选按钮的状态，而不是尝试设置整个Frame的状态
        # 查找delay_type_frame中的单选按钮并设置其状态
        for frame in self.answer_settings_frame.winfo_children():
            if isinstance(frame, tk.Frame):
                for widget in frame.winfo_children():
                    # 只对支持state选项的控件设置状态
                    if hasattr(widget, 'config') and 'state' in widget.config():
                        widget.config(state=state)
        
        # 特别处理延迟设置区域
        self.toggle_delay_custom()
    
    def toggle_delay_custom(self):
        # 切换自定义延迟设置的可用状态
        # 只有在启用自动答题且选择固定延迟时才可用
        state = tk.NORMAL if (self.auto_answer_var.get() and self.delay_type_var.get() == 2) else tk.DISABLED
        
        for child in self.delay_custom_frame.winfo_children():
            # 只对支持state选项的控件设置状态
            if hasattr(child, 'config') and 'state' in child.config():
                child.config(state=state)
    
    def save_config(self):
        # 保存配置
        # 更新配置
        self.config["auto_danmu"] = self.danmu_on_var.get()
        self.config["danmu_config"] = {
            "danmu_limit": self.danmu_spinbox_var.get()
        }
        

        
        self.config["auto_answer"] = self.auto_answer_var.get()
        self.config["answer_config"] = {
            "answer_delay": {
                "type": self.delay_type_var.get(),
                "custom": {
                    "time": self.custom_time_var.get()
                }
            }
        }
        
        # AI设置
        self.config["ai_config"] = {
            "api_key": self.ai_key_var.get()
        }
        
        # 保存到文件
        config_path = get_config_path()
        with open(config_path, 'w') as f:
            json.dump(self.config, f, ensure_ascii=False, indent=4)
        
        # 更新主窗口的配置
        self.main_window.config = self.config
        
        # 显示保存成功消息
        messagebox.showinfo("提示", "配置已保存")
        
        # 关闭窗口
        self.close_window()
    
    def close_window(self):
        # 关闭窗口
        self.top.destroy()
