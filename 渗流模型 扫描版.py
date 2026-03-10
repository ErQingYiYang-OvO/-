# 模块导入

import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from collections import deque
from matplotlib.colors import ListedColormap
from scipy.ndimage import label
import threading
import time


# 蒙特卡洛核心

# 超参数N，蒙特卡洛模拟次数
N = 100
# 生成网格函数
def generate_grid(n,p,N): # n: 网格大小 p: 概率
    stack = (np.random.rand(N,n,n) < p).astype(np.int8) # 一次生成所有地图
    ocean = sum(is_ocean(stack[i],n) for i in range(N)) # 获取所有地图的连通性
    return(ocean,stack[-1])

# 判断连通性函数
def is_ocean(grid, n):
    labeled, _ = label(grid) # 使用C语言对联通水域打标记
    left_labels  = set(labeled[:, 0].flat) - {0}
    right_labels = set(labeled[:, -1].flat) - {0}
    return bool(left_labels & right_labels)



# 界面构建


class manipulate: # 界面类
    def __init__(self, master):
        self.master = master # 主窗口
        master.title("percolation model")
        self.data = {} # 储存p-概率计算结果

        # 左面板
        left_frame = tk.Frame(master) # master上创建一个frame
        left_frame.pack(side=tk.LEFT,fill=tk.BOTH,expand=True) # 将其置于左侧，填满空间，可随窗口缩放

        # 操控区
        control_frame = tk.LabelFrame(left_frame,text="control") # leftframe中创建一个带标题的frame
        control_frame.pack(fill=tk.X,padx=5,pady=5) # 打包并设置外边距

        tk.Label(control_frame,text="posibility of water p(0~1):").grid(row=0,column=0,padx=5,pady=5) # 创建标签，指定行列与格内边距
        self.p_entry = tk.Entry(control_frame,width=10) # 创建输入p值的框
        self.p_entry.grid(row=0,column=1,padx=5,pady=5) # 放置在0行1列
        self.p_entry.insert(0,"0.5") # 输入框初始值为0.5，0是索引

        tk.Label(control_frame,text="grid size n(>1):").grid(row=1,column=0,padx=5,pady=5)
        self.n_combo = ttk.Combobox(control_frame,values=[10,20,50,100,200,500,1000,2000],width=8) # 创建n的下拉框
        self.n_combo.grid(row=1,column=1,padx=5,pady=5) # 放置在1行1列
        self.n_combo.current(0) # 默认选中第0个

        self.start_button = tk.Button(control_frame,text="start",command=self.start)
        self.start_button.grid(row=2,column=0,columnspan=2,pady=10)

        tk.Label(control_frame,text="scan step").grid(row=3,column=0,padx=5,pady=5) 
        self.step_combo = ttk.Combobox(control_frame,values=[0.1,0.05,0.01],width=8) # 创建步长下拉框
        self.step_combo.grid(row=3,column=1,padx=5,pady=5)
        self.step_combo.current(0)

        self.sacn_button = tk.Button(control_frame,text="scan",command=self.scan) # 创建扫描按钮
        self.sacn_button.grid(row=4,column=0,padx=5,pady=5)

        self.show_error = tk.BooleanVar(value=True) # 误差棒显示选项
        self.show_error_check = tk.Checkbutton(control_frame,text="error bars",variable=self.show_error,command=self.update_plot)
        self.show_error_check.grid(row=4,column=1,padx=5,pady=5)

        # 折线图
        plot_frame = tk.Frame(left_frame)
        plot_frame.pack(fill=tk.BOTH,expand=True,padx=5,pady=5)

        self.fig_left = Figure(figsize=(5,4),dpi=100) # 创建一个figure，制定尺寸和分辨率
        self.ax_left = self.fig_left.add_subplot(111) # 创建一个子图，即绘图区域
        self.ax_left.set_xlabel("p")
        self.ax_left.set_ylabel("possibility of forming a ocean")
        self.ax_left.set_xlim(-0.1,1.1)
        self.ax_left.set_ylim(-0.1,1.1)
        self.ax_left.grid(True) # 添加网格

        self.canvas_left = FigureCanvasTkAgg(self.fig_left,master=plot_frame) # 将matplotlib的figure添加到tkinter的widget中
        self.canvas_left.draw() # 绘制
        self.canvas_left.get_tk_widget().pack(fill=tk.BOTH,expand=True)

        # 地图区
        right_frame = tk.Frame(master)
        right_frame.pack(side=tk.RIGHT,fill=tk.BOTH,expand=True)

        self.fig_right = Figure(figsize=(5,5),dpi=100)
        self.ax_right = self.fig_right.add_subplot(111)
        self.ax_right.set_xticks([])
        self.ax_right.set_yticks([])

        self.canvas_right = FigureCanvasTkAgg(self.fig_right,master=right_frame)
        self.canvas_right.draw()
        self.canvas_right.get_tk_widget().pack(fill=tk.BOTH,expand=True)

    def start(self): # 开始按钮点击事件

        try:
            p = float(self.p_entry.get()) # 获取p值
            if not (0 <= p <= 1): 
                messagebox.showerror("error","p must be in [0,1]")
                raise ValueError
        except ValueError: # 输入错误
            return
        
        try:
            n = int(self.n_combo.get()) # 获取n值
        except:
            messagebox.showerror("error","n must be an integer larger than 1")
            return
        

        ocean,grid = generate_grid(n,p,N) # 获得总联通地图数与最后一张地图

        
        if not (p,n) in self.data: # 添加数据
            self.data[(p,n)] = []
        self.data[(p,n)].append(ocean/N) # 每做一次模拟添加一个数据

        self.ax_right.clear() # 更新地图显示
        cmap = ListedColormap(["green","blue"]) # 颜色映射
        self.ax_right.imshow(grid,cmap=cmap,interpolation="nearest",vmin=0,vmax=1) # 绘制地图
        self.ax_right.set_xticks([]) # 隐藏坐标轴  
        self.ax_right.set_yticks([])     
            
        self.ax_right.set_title(f"p={p:.2f},ocean possibility={ocean/N:.2f},n={n},\n{'Ocean' if is_ocean(grid,n) else 'Lakes'}") # 添加标题
        self.canvas_right.draw() # 绘制地图

        self.update_plot() # 更新折线图,于后定义

    def update_plot(self): # 更新折线图
        self.ax_left.clear()
        self.ax_left.set_xlabel("p")
        self.ax_left.set_ylabel("possibility of forming a ocean")
        self.ax_left.set_xlim(-0.1,1.1)
        self.ax_left.set_ylim(-0.1,1.1)
        self.ax_left.grid(True)

        groups = {} # 创建按n分类的组
        for (p,n),prob in self.data.items(): # 获取数据
            if n not in groups: # 创建组
                groups[n] = []
            avg_prob = np.mean(prob)
            groups[n].append((p,avg_prob))

        for n , points in groups.items(): # 绘制按n分开的折线图
            points.sort() # 按p排序
            p_vals = [pt[0] for pt in points]
            prob_vals = [pt[1] for pt in points]
            self.ax_left.plot(p_vals,prob_vals,marker='o',label=f"n={n}")

        self.ax_left.legend(loc='upper left')
        self.canvas_left.draw()

    def scan(self): # 扫描按钮点击事件
        try:
            n = int(self.n_combo.get()) # 获取n值
        except:
            messagebox.showerror("error","n must be an integer larger than 1")
            return
        step = float(self.step_combo.get()) # 获取扫描步长

        p_vals = np.arange(0,1+step,step) # 创建p值列表
        p_vals = np.clip(p_vals,0,1) # 把可能的越界值截掉

        for i,p in enumerate(p_vals):
            ocean,grid = generate_grid(n,p,N)
            prob = ocean/N

            if not (p,n) in self.data: # 添加数据
                self.data[(p,n)] = []
            self.data[(p,n)].append(prob)

            """
            self.ax_right.clear() # 更新地图显示
            cmap = ListedColormap(["green","blue"])
            self.ax_right.imshow(grid,cmap=cmap,interpolation="nearest",vmin=0,vmax=1)
            self.ax_right.set_xticks([])
            self.ax_right.set_yticks([])
            self.ax_right.set_title(f"p={p:.2f},ocean possibility={prob:.2f},n={n},\n{'Ocean' if is_ocean(grid,n) else 'Lakes'}")
            self.canvas_right.draw()
            """
            # 这里当n较小根本看不见地图刷新，而当n较大时则严重影响计算速度

            self.update_plot() # 更新折线图



# 主程序调用

if __name__ == "__main__": # 仅在主程序调用
    root = tk.Tk()
    app = manipulate(root) # 构建主窗口并传给主程序
    root.mainloop() # 实时响应输入




