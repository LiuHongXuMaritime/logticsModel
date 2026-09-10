import pandas as pd
import gurobipy as gp
from gurobipy import GRB
import numpy as np

# 读取矩阵
reader = pd.read_excel('物流矩阵数据.xlsx', header=0, index_col=0)
reader2 = pd.read_excel("客户需求.xlsx", header=0, index_col=0)
demand_j = reader2["Tonnes"].to_numpy()
arr = reader.to_numpy()
# 客户：
i_ = 54
# 需求第i周的需求
# demand_i = model.addVars()
# Lisiben到第k的距离->const


l_o_k = arr[2, :]
l_port = np.min(arr[[10, 11], :], axis=0)  # Antwerp
print(l_port)
# k个dc 到 第j个客户的距离
miner = 1e8
best_dc = None
# DC:
# for k_ in range(2, 54):
k_ = 54

model = gp.Model("lyys_plan")
l_k_i = model.addVars(k_, i_, name="k_dc_j_dist", vtype=GRB.CONTINUOUS)
x_k_i = model.addVars(k_, i_, name="k_dc_j_x", vtype=GRB.BINARY)
q_k = model.addVars(k_, name="k_dc_q", lb=0, ub=GRB.INFINITY, vtype=GRB.CONTINUOUS)
y_k = model.addVars(k_, name="k_dc_y", vtype=GRB.BINARY)
a_k = model.addVars(k_, name="k_dc_a", vtype=GRB.CONTINUOUS)
e = model.addVar(name="ship_nums", vtype=GRB.CONTINUOUS)
r_k = model.addVars(k_, name="k_dc_r", lb=0, ub=GRB.INFINITY, vtype=GRB.CONTINUOUS)

q1_part1 = gp.quicksum(demand_j[i] * x_k_i[k, i] * (4 + 0.03 * l_o_k[k]) for i in range(i_) for k in range(k_))
q1_part2 = gp.quicksum(demand_j[i] * x_k_i[k, i] * (5 + 0.1 * l_k_i[k, i]) for i in range(i_) for k in range(k_))
q1_part3 = gp.quicksum(2000 * y_k[k] + 8 * q_k[k] for k in range(k_))
q1_part4 = gp.quicksum(q_k[k] * 600 * 20 / 100 / 52 * 3 / 7 for k in range(k_))
obj1 = q1_part1 + q1_part2 + q1_part3 + q1_part4
# 目标1
model.setObjective(obj1, GRB.MINIMIZE)

# 约束
for i in range(i_):
    model.addConstr(gp.quicksum(x_k_i[k, i] for k in range(k_)) == 1, name="q_sb1")

for i in range(i_):
    for k in range(k_):
        model.addConstr(x_k_i[k, i] <= y_k[k], name="q_sb2")

for k in range(k_):
    model.addConstr(q_k[k] == gp.quicksum(demand_j[i] * x_k_i[k, i] for i in range(i_)), name="q_sb3")

model.optimize()

print(best_dc)
df = pd.DataFrame()

df[F"y_k"] = [y_k[k].X for k in range(k_)]

x_k_i_arr = pd.DataFrame([[x_k_i[k, i].X for i in range(i_)] for k in range(k_)],columns=[f"x_k_{i}" for i in range(i_)])
df1 = pd.concat([df, x_k_i_arr], axis=1)
df1.to_excel(f"result1_{model.ObjVal:.2f}.xlsx")
# Q1

model = gp.Model("lyys_plan2")
l_k_i = model.addVars(k_, i_, name="k_dc_j_dist", vtype=GRB.CONTINUOUS)
x_k_i = model.addVars(k_, i_, name="k_dc_j_x", vtype=GRB.BINARY)
q_k = model.addVars(k_, name="k_dc_q", lb=0, ub=GRB.INFINITY, vtype=GRB.CONTINUOUS)
y_k = model.addVars(k_, name="k_dc_y", vtype=GRB.BINARY)
a_k = model.addVars(k_, name="k_dc_a", vtype=GRB.CONTINUOUS)
e = model.addVar(name="ship_nums", vtype=GRB.CONTINUOUS)
r_k = model.addVars(k_, name="k_dc_r", lb=0, ub=GRB.INFINITY, vtype=GRB.INTEGER)

q2_part1 = gp.quicksum(demand_j[i] * x_k_i[k, i] * 0.009 * l_o_k[k] for i in range(i_) for k in range(k_))
q2_part2 = gp.quicksum(r_k[k] * 2500 for k in range(k_))
q2_part3 = gp.quicksum(demand_j[i] * x_k_i[k, i] * (5 + 0.1 * l_k_i[k, i]) for i in range(i_) for k in range(k_))
q2_part4 = gp.quicksum(2000 * y_k[k] + 8 * q_k[k] for k in range(k_))
q2_part5 = gp.quicksum(q_k[k] * 600 * 20 / 100 / 52 * 3 / 7 for k in range(k_))
obj2 = q2_part1 + q2_part2 + q2_part3 + q2_part4 + q2_part5
model.setObjective(obj2, GRB.MINIMIZE)

# 约束
for i in range(i_):
    model.addConstr(gp.quicksum(x_k_i[k, i] for k in range(k_)) == 1, name=f"q_sb1{i}")

for i in range(i_):
    for k in range(k_):
        model.addConstr(x_k_i[k, i] <= y_k[k], name=f"q_sb2{i}_{k}")

for k in range(k_):
    model.addConstr(q_k[k] == gp.quicksum(demand_j[i] * x_k_i[k, i] for i in range(i_)), name=f"q_sb3{k}")
    model.addConstr(q_k[k] / 2000 <= r_k[k], name=f"q{k}")
    model.addConstr(q_k[k] / 2000 + 1 >= r_k[k], name=f"q2{k}")
# Q2
model.optimize()

print(best_dc)
df = pd.DataFrame()

df[F"y_k"] = [y_k[k].X for k in range(k_)]
df[f"整列数量(r_k)"] = [r_k[k].X for k in range(k_)]
x_k_i_arr = pd.DataFrame([[x_k_i[k, i].X for i in range(i_)] for k in range(k_)],columns=[f"x_k_{i}" for i in range(i_)])
df2 = pd.concat([df, x_k_i_arr], axis=1)
df2.to_excel(f"result2_{model.ObjVal:.2f}.xlsx")

# Q3
model = gp.Model("lyys_plan3")
l_k_i = model.addVars(k_, i_, name="k_dc_j_dist", vtype=GRB.CONTINUOUS)
x_k_i = model.addVars(k_, i_, name="k_dc_j_x", vtype=GRB.BINARY)
q_k = model.addVars(k_, name="k_dc_q", lb=0, ub=GRB.INFINITY, vtype=GRB.CONTINUOUS)
y_k = model.addVars(k_, name="k_dc_y", vtype=GRB.BINARY)
a_k = model.addVars(k_, name="k_dc_a", lb=0, ub=3000, vtype=GRB.INTEGER)
e = model.addVar(name="ship_nums", vtype=GRB.CONTINUOUS)
r_k = model.addVars(k_, name="k_dc_r", lb=0, ub=GRB.INFINITY, vtype=GRB.INTEGER)

q3_part1 = gp.quicksum(
    demand_j[i] * x_k_i[k, i] * (a_k[k] * 50 + l_o_k[k]* 0.45 + 5 + 0.1 * l_k_i[k, i]) for i in range(i_)
    for k in range(k_))
q3_part2 = gp.quicksum(2000 * y_k[k] + 8 * q_k[k] + q_k[k] * 600 * 20 / 100 / 52 * 3 for k in range(k_))

obj3 = q3_part1 + q3_part2
model.setObjective(obj3, GRB.MINIMIZE)

# 约束
for i in range(i_):
    model.addConstr(gp.quicksum(x_k_i[k, i] for k in range(k_)) == 1, name=f"q_sb1{i}")

for i in range(i_):
    for k in range(k_):
        model.addConstr(x_k_i[k, i] <= y_k[k], name=f"q_sb2{i}_{k}")

for k in range(k_):
    model.addConstr(q_k[k] == gp.quicksum(demand_j[i] * x_k_i[k, i] for i in range(i_)), name=f"q_sb3{k}")
    model.addConstr(q_k[k] / 50 <= a_k[k], name=f"q{k}")
    model.addConstr(q_k[k] / 50 + 1 >= a_k[k], name=f"q2{k}")

model.setParam(GRB.Param.TimeLimit, 3*600)  # 30分钟超时
model.setParam(GRB.Param.MIPGap, 0.025)  # 1% gap容忍
model.optimize()

print(best_dc)
df = pd.DataFrame()

df[F"y_k"] = [y_k[k].X for k in range(k_)]
df["车厢数量(a_k)"] = [a_k[k].X for k in range(k_)]

x_k_i_arr = pd.DataFrame([[x_k_i[k, i].X for i in range(i_)] for k in range(k_)],columns=[f"x_k_{i}" for i in range(i_)])
df3 = pd.concat([df, x_k_i_arr], axis=1)
df3.to_excel(f"result3_{model.ObjVal:.2f}.xlsx")


model = gp.Model("lyys_plan4")
l_k_i = model.addVars(k_, i_, name="k_dc_j_dist", vtype=GRB.CONTINUOUS)
x_k_i = model.addVars(k_, i_, name="k_dc_j_x", vtype=GRB.BINARY)
q_k = model.addVars(k_, name="k_dc_q", lb=0, ub=GRB.INFINITY, vtype=GRB.CONTINUOUS)
y_k = model.addVars(k_, name="k_dc_y", vtype=GRB.BINARY)
a_k = model.addVars(k_, name="k_dc_a", lb=0, ub=GRB.INFINITY, vtype=GRB.INTEGER)
e = model.addVar(name="ship_nums", lb=0, ub=GRB.INFINITY, vtype=GRB.INTEGER)
r_k = model.addVars(k_, name="k_dc_r", lb=0, ub=GRB.INFINITY, vtype=GRB.INTEGER)
# 使用安特卫普港
q4_part1 = gp.quicksum(
    q_k[k] * (4 + 4 + 0.03 * l_port[k] + 8 + 600 * 20 / 100 / 52 * 6 / 7) + 2000 * y_k[k] for k in range(k_))
q4_part2 = gp.quicksum(demand_j[i] * x_k_i[k, i] * (5 + 0.1 * l_k_i[k, i]) for i in range(i_) for k in range(k_))

model.setObjective(q4_part1 + q4_part2, GRB.MINIMIZE)
# 约束
for i in range(i_):
    model.addConstr(gp.quicksum(x_k_i[k, i] for k in range(k_)) == 1, name=f"q_sb1{i}")

for i in range(i_):
    for k in range(k_):
        model.addConstr(x_k_i[k, i] <= y_k[k], name=f"q_sb2{i}_{k}")

for k in range(k_):
    model.addConstr(q_k[k] == gp.quicksum(demand_j[i] * x_k_i[k, i] for i in range(i_)), name=f"q_sb3{k}")
    model.addConstr(q_k[k] / 50 <= r_k[k], name=f"q{k}")
    model.addConstr(q_k[k] / 50 + 1 >= r_k[k], name=f"q2{k}")
    # model.addConstr(l_port[k] * y_k[k] <= 500, name=f"port_max{k}")

model.addConstr(gp.quicksum(q_k[k] for k in range(k_)) / 3000 <= e, name="e_limit")

model.optimize()

print(best_dc)
df = pd.DataFrame()

df[F"y_k"] = [y_k[k].X for k in range(k_)]
df["船舶数e"] = e.X

x_k_i_arr = pd.DataFrame([[x_k_i[k, i].X for i in range(i_)] for k in range(k_)],columns=[f"x_k_{i}" for i in range(i_)])
df4 = pd.concat([df, x_k_i_arr], axis=1)
df4.to_excel(f"result4_{model.ObjVal:.2f}.xlsx")

