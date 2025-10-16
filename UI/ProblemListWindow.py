import tkinter as tk
from tkinter import ttk, messagebox
import threading
import os
import json
from dashscope import MultiModalConversation
from UI.ProblemDetailWindow import ProblemDetailWindow

class ProblemListWindow:
    """显示课程题目列表的窗口"""
    def __init__(self, master, lesson_name, problems_ls):
        self.window = tk.Toplevel(master)
        self.window.title(f"{lesson_name} - 题目列表")
        self.window.geometry("800x600")
        self.problems_ls = problems_ls
        
        # 保存答案的字典
        self.solved_problems = {}
        
        # 创建题目列表
        self.create_problem_list()
        
        # 初始化AI key输入框的值
        self.load_ai_key()
    
    def create_problem_list(self):
        # 创建主框架
        main_frame = tk.Frame(self.window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 创建标题
        title_label = tk.Label(main_frame, text="题目列表", font=("STHeiti", 12))
        title_label.pack(anchor=tk.W, pady=5)
        
        # 添加AI解答所有题目功能
        ai_frame = tk.Frame(main_frame)
        ai_frame.pack(fill=tk.X, pady=5)
        
        key_label = tk.Label(ai_frame, text="API Key:", font=("STHeiti", 10))
        key_label.pack(side=tk.LEFT, padx=5)
        
        self.ai_key_entry = tk.Entry(ai_frame, font=("STHeiti", 10), width=40, show="*")
        self.ai_key_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        self.solve_all_btn = tk.Button(ai_frame, text="AI 解答所有题目", font=("STHeiti", 10), 
                                     command=self.on_solve_all_click)
        self.solve_all_btn.pack(side=tk.RIGHT, padx=5)
        
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
            
            # 检查问题是否有result键且非空
            has_result = 'result' in problem and problem['result']
            
            if has_result:
                # 有结果，锁住题目，设置为灰色背景
                problem_frame.config(bg="#E0E0E0", cursor="arrow")
                # 页码
                page_label = tk.Label(problem_frame, text=f"页码: {problem.get('page', 'N/A')} (已解答)", 
                                    font=("STHeiti", 10), width=20, anchor=tk.W, cursor="arrow", bg="#E0E0E0")
                page_label.pack(side=tk.LEFT, padx=5, pady=5)
                # 问题内容
                content_label = tk.Label(problem_frame, text=f"{problem.get('body', '无问题内容')}", 
                                       font=("STHeiti", 10), wraplength=600, justify=tk.LEFT, cursor="arrow", bg="#E0E0E0")
                content_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, pady=5)
            else:
                # 没有结果，可点击
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
    
    def load_ai_key(self):
        # 从配置中加载AI key
        try:
            from Scripts.Utils import get_config_path
            config_path = get_config_path()
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    ai_key = config.get("ai_config", {}).get("api_key", "")
                    self.ai_key_entry.delete(0, tk.END)
                    self.ai_key_entry.insert(0, ai_key)
        except Exception as e:
            # 如果加载失败，使用环境变量作为备选
            ai_key = os.getenv("API_KEY_QWEN", "")
            self.ai_key_entry.delete(0, tk.END)
            self.ai_key_entry.insert(0, ai_key)
    
    def on_problem_click(self, problem):
        """题目点击事件处理"""
        # 如果题目已经被解答，恢复答案
        if problem.get('page') in self.solved_problems:
            problem['answers'] = self.solved_problems[problem.get('page')]
        
        # 创建并显示问题详情窗口
        self.problem_detail_window = ProblemDetailWindow(self.window, problem)
    
    def on_solve_all_click(self):
        # AI解答所有题目按钮点击事件
        # 获取AI key
        ai_key = self.ai_key_entry.get()
        if not ai_key:
            # 如果没有输入key，显示一个提示
            messagebox.showwarning("提示", "请输入API Key")
            return
        
        # 模拟AI思考过程
        self.solve_all_btn.config(state=tk.DISABLED, text="AI 解答中...")
        self.window.update()
        
        # 启动一个线程来调用AI接口，避免阻塞UI
        ai_thread = threading.Thread(target=self._solve_all_problems, args=(ai_key,))
        ai_thread.daemon = True
        ai_thread.start()
    
    def _solve_all_problems(self, ai_key):
        try:
            solved_count = 0
            total_count = len(self.problems_ls)
            
            # 依次处理每个问题，跳过已有result的问题
            for idx, problem in enumerate(self.problems_ls):
                # 检查问题是否已有result键且非空，如果有则跳过
                if 'result' in problem and problem['result']:
                    continue
                    
                try:
                    # 更新按钮文本显示进度
                    progress_text = f"AI 解答中... ({idx+1}/{total_count})"
                    self.window.after(0, lambda text=progress_text: 
                                     self.solve_all_btn.config(text=text))
                    
                    # 调用AI接口解答当前问题
                    ai_answer = self._call_ai_api_for_problem(ai_key, problem)
                    
                    if ai_answer:
                        # 保存答案
                        problem['answers'] = ai_answer
                        self.solved_problems[problem.get('page')] = ai_answer
                        solved_count += 1
                    
                except Exception as e:
                    # 单个问题处理失败，继续处理下一个
                    print(f"处理题目{problem.get('page')}时出错: {str(e)}")
                    continue
            
            # 全部处理完毕后显示结果
            self.window.after(0, lambda: messagebox.showinfo("提示", 
                             f"AI解答完成！共处理{total_count}个题目，成功解答{solved_count}个题目"))
            
        except Exception as e:
            # 处理整体错误
            self.window.after(0, lambda: messagebox.showerror("错误", 
                             f"AI批量解答失败: {str(e)}"))
        finally:
            # 恢复按钮状态
            self.window.after(0, lambda: self.solve_all_btn.config(
                             state=tk.NORMAL, text="AI 解答所有题目"))
    
    def _call_ai_api_for_problem(self, ai_key, problem):
        # 调用AI API解答单个问题
        image_path = problem.get('image', '')
        
        if image_path and os.path.exists(image_path):
            # 构建消息
            messages = [
                {"role": "system", "content": [{"text": "You are a helpful assistant."}]},
                {
                    'role':'user',
                    'content': [
                        {'image': f"file://{os.path.abspath(image_path)}"},
                        {'text': '请以JSON格式回答图片中的问题。如果是选择题，则返回{{"question": "问题", "answer": ["选项（A/B/C/...）"]}}，选项为圆形则为单选，选项为矩形则为多选；如果是填空题，则返回{{"question": "问题", "answer": ["填空1答案", "填空2答案", ...]}}；如果是主观题，则返回{{"question": "问题", "answer": ["主观题答案"]}}'}
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
            return ai_answer
        else:
            # 没有图片的情况，不进行处理
            return None