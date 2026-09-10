# utf-8 encoding
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import networkx as nx

matplotlib.use("TKAgg")
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

# ===================== 1. 定义44个DC候选地点的基础参数 =====================
reader = pd.read_excel('物流矩阵数据.xlsx', header=0, index_col=0)
reader2 = pd.read_excel("客户需求.xlsx", header=0, index_col=0)
demand = reader2["Tonnes"].to_numpy()
dist_arr = reader.to_numpy()

n_customers = n_dc_candidates = len(dist_arr)


def plot_result(DClst, Qs_arr, qji_arr, numbers: int = 54, title: str = "物流网络拓扑图", save: bool = True):
    """
    绘制物流网络拓扑图
    :param DClst: 构建的DC编号列表 包括工厂
    :param Qs_arr: 工厂到DC的运输量向量
    :param qji_arr: DC到客户配送量矩阵
    :return: None
    """
    plt.figure(figsize=(16, 10))
    startpoint = 2
    # DClst.remove(startpoint)
    DCset = set(DClst)

    dc_r = 1
    dc_e = np.linspace(-np.pi / 2, np.pi / 2, len(DClst) - 1)
    dc_x = np.cos(dc_e) * dc_r
    dc_y = np.sin(dc_e) * dc_r

    count = 0
    pos_dic = {}
    # 绘制Dc and Factory
    dc_first = True  # 标记是否首次绘制DC
    factory_drawn = False  # 标记是否绘制Factory

    factory_color = "#1F77B4"
    dc_color = "#FF7F0E"
    cus_color = "#2CA02C"

    f2dc_color = "#6BAED6"
    dc2cus_color = "#FFBB78"

    # 绘制DC and Factory
    for i in range(len(DClst)):
        if DClst[i] != startpoint:
            # 首次绘制DC时设置label，后续不设置
            label_dc = "DC" if dc_first else "_nolegend_"
            plt.scatter(dc_x[count], dc_y[count], c=dc_color, s=20, label=label_dc, edgecolors="gray", zorder=10)
            plt.text(dc_x[count] + 0.02, dc_y[count] + 0.02, f"{DClst[i]}", fontsize=10)
            pos_dic[DClst[i]] = (dc_x[count], dc_y[count])
            dc_first = False  # 首次绘制后标记为False
            count += 1
        else:
            # 绘制Factory，仅设置一次label
            plt.scatter(0, 0, c=factory_color, s=40, label="Factory", edgecolors="gray", zorder=10)
            plt.text(0.02, 0.02, f"{DClst[i]}", fontsize=10)
            pos_dic[DClst[i]] = (0, 0)
            factory_drawn = True

    # 绘制Customer
    cus_set = set(range(numbers + 1)) - DCset
    cus_lst = list(cus_set)
    custom_r = 2
    cs_e = np.linspace(-np.pi / 2, np.pi / 2, len(cus_set))
    cs_x = np.cos(cs_e) * custom_r
    cs_y = np.sin(cs_e) * custom_r

    cus_first = True  # 标记是否首次绘制Customer
    for i in range(len(cus_set)):
        # 首次绘制Customer时设置label，后续不设置
        label_cus = "Customer" if cus_first else "_nolegend_"
        plt.scatter(cs_x[i], cs_y[i], c=cus_color, s=30, label=label_cus, edgecolors="gray", zorder=10)
        plt.text(cs_x[i] + 0.02, cs_y[i] + 0.02, f"{cus_lst[i]}", fontsize=10)
        pos_dic[cus_lst[i]] = (cs_x[i], cs_y[i])
        cus_first = False  # 首次绘制后标记为False
    # print(pos_dic)
    for dc_end in range(len(Qs_arr)):
        if dc_end in DCset:
            plt.plot(*zip(pos_dic[2], pos_dic[dc_end]), c=f2dc_color, linewidth=1, )
            plt.quiver(pos_dic[2][0], pos_dic[2][1], pos_dic[dc_end][0] - pos_dic[2][0],
                       pos_dic[dc_end][1] - pos_dic[2][1], angles='xy', scale_units='xy', scale=2, width=0.001,
                       headwidth=7,
                       color=f2dc_color)

            for i in range(len(qji_arr[0])):
                if qji_arr[dc_end][i] > 0:
                    plt.plot(*zip(pos_dic[dc_end], pos_dic[i + 1]), c=dc2cus_color, linewidth=1)
                    plt.quiver(pos_dic[dc_end][0], pos_dic[dc_end][1], pos_dic[i + 1][0] - pos_dic[dc_end][0],
                               pos_dic[i + 1][1] - pos_dic[dc_end][1], angles='xy', scale_units='xy', scale=2,
                               headwidth=7,
                               width=0.001, color=dc2cus_color)

    # plt.text(0.85, 0.05, f"Alemiya|必为精品!", fontsize=10, transform=plt.gca().transAxes,alpha=0.1)
    # plt.tick_params(axis="both", which="both", bottom=False, top=False, left=False, right=False,)
    plt.title(title)
    plt.legend()
    if save:
        plt.savefig(f"{title}.png",dpi=300)
    plt.show()
