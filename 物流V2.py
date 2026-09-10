import pandas as pd
import gurobipy as gp
from gurobipy import GRB
import numpy as np

# 读取矩阵
reader = pd.read_excel('物流矩阵数据.xlsx', header=0, index_col=0)
reader2 = pd.read_excel("客户需求.xlsx", header=0, index_col=0)
demand_j = reader2["Tonnes"].to_numpy()
arr = reader.to_numpy()
# 客户
i_ = j_ = 54
# DC
k_ = 54

l_o_k = arr[2, :]
l_port = np.min(arr[[10, 11], :], axis=0)

model = gp.Model("物流")

kj = model.addVars(i_, vtype=GRB.INTEGER, name="kj")
q_i_j = model.addVars(i_, j_, vtype=GRB.INTEGER, name="q_i_j")
yj = model.addVars(j_, vtype=GRB.BINARY, name="yj")
# 2 是工厂里斯本
part1 = gp.quicksum(yj[j] * (kj[j] * 2500 + 0.009 * l_o_k[j] * q_i_j[2, j]) for j in range(j_))
# j 是 DC
part2 = gp.quicksum(yj[j] * q_i_j[j, i] * (5 + 0.1 * arr[j, i]) for j in range(j_) for i in range(i_))
#
part3 = gp.quicksum(yj[j] * 2000 + 8 * q_i_j[2, j] for j in range(j_))
#
part4 = gp.quicksum(q_i_j[2, j] * 600 * 20 / 100 / 52 / 7 * 3 for j in range(j_))
obj1 = part1 + part2 + part3 + part4

model.setObjective(obj1, GRB.MINIMIZE)

model.addConstr(
    gp.quicksum(yj[j] * q_i_j[2, j] for j in range(j_)) == gp.quicksum(demand_j[j] * (1 - yj[j]) for j in range(j_)))

for j in range(j_):
    model.addConstr(gp.quicksum(yj[j] * q_i_j[j, i] for i in range(i_)) == yj[j] * q_i_j[2, j])

for i in range(i_):
    model.addConstr(gp.quicksum(yj[j] * q_i_j[j, i] for j in range(j_)) == demand_j[i])


model.optimize()