import sys
import tkinter as tk
from tkinter import messagebox
from UI.MainWindow import MainWindow

if __name__ == "__main__":
    # 初始化tkinter应用
    root = tk.Tk()
    root.title("清华大学雨课堂助手")
    
    # 创建并显示主窗口
    app = MainWindow(root)
    
    # 启动主事件循环
    root.mainloop()

