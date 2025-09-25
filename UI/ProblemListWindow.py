import tkinter as tk
from tkinter import ttk
from UI.ProblemDetailWindow import ProblemDetailWindow

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
        # 创建主框架
        main_frame = tk.Frame(self.window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 创建标题
        title_label = tk.Label(main_frame, text="题目列表", font=("STHeiti", 12))
        title_label.pack(anchor=tk.W, pady=5)
        
        # 创建滚动区域框架
        scroll_frame = tk.Frame(main_frame)
        scroll_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建垂直滚动条
        y_scrollbar = ttk.Scrollbar(scroll_frame)
        y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 创建水平滚动条
        x_scrollbar = ttk.Scrollbar(scroll_frame, orient=tk.HORIZONTAL)
        x_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # 创建Canvas
        canvas = tk.Canvas(scroll_frame, yscrollcommand=y_scrollbar.set, xscrollcommand=x_scrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 配置滚动条
        y_scrollbar.config(command=canvas.yview)
        x_scrollbar.config(command=canvas.xview)
        
        # 创建内部框架
        inner_frame = tk.Frame(canvas)
        canvas_window = canvas.create_window((0, 0), window=inner_frame, anchor="nw")
        
        # 绑定事件，确保Canvas大小适应内容
        def on_frame_configure(event):
            # 更新Canvas的滚动区域
            canvas.configure(scrollregion=canvas.bbox("all"))
        
        inner_frame.bind("<Configure>", on_frame_configure)
        
        # 绑定鼠标滚轮事件实现垂直滚动
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        canvas.bind_all("<MouseWheel>", on_mousewheel)
        
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