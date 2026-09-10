import gurobipy as gp
from gurobipy import GRB
import numpy as np
import pandas as pd

from LYY.plot_function import plot_result

reader = pd.read_excel('物流矩阵数据.xlsx', header=0, index_col=0)
reader2 = pd.read_excel("客户需求.xlsx", header=0, index_col=0)
demand = reader2["Tonnes"].to_numpy()
arr = reader.to_numpy()
n_customers = n_dc_candidates = len(arr)  # 假设50个客户（可根据实际调整）
# 客户需求量（示例）
di = demand

# 工厂到DC候选点的距离（Loj）
Loj = arr[2, :]

# DC候选点到每个客户的距离矩阵（Lji）
Lji = arr

# 每个DC候选点的固定运营成本（可差异化，示例统一为2000）
fixed_cost_dc = np.full(n_dc_candidates, 2000)

# 大M值（取客户总需求，确保约束有效）
M = sum(di)

# ===================== 2. 创建模型并优化参数 =====================
model = gp.Model("候选点DC选址优化")
model.setParam("OutputFlag", 1)  # 显示求解日志
model.setParam("MIPGap", 0.01)  # 允许1%的最优解间隙（加速求解）
model.setParam("TimeLimit", 600)  # 最大求解时间（秒）

# ===================== 3. 核心变量定义（融入DC选址决策） =====================
# y[j] = 1 表示在第j个候选地点建设DC，0表示不建设（j=0~43对应44个候选点）
y = model.addVars(n_dc_candidates, vtype=GRB.BINARY, name="Build_DC")

# qS[j]：工厂到第j个候选DC的运输量（仅建设的DC有流量）
qS = model.addVars(n_dc_candidates, vtype=GRB.CONTINUOUS, lb=0, name="Factory_to_DC")

# qji[j,i]：第j个候选DC到第i个客户的运输量
qji = model.addVars(n_dc_candidates, n_customers, vtype=GRB.CONTINUOUS, lb=0, name="DC_to_Customer")

# 火车整箱量
kj = model.addVars(n_dc_candidates, vtype=GRB.INTEGER, lb=0, name="Train_Box")
# ===================== 4. 改进后的目标函数 =====================
# 成本项1：工厂→DC的干线运输成本
cost_trans_factory_dc = gp.quicksum(2500 * kj[j] + 0.009 * Loj[j] * qS[j] for j in range(n_dc_candidates))

# 成本项2：DC→客户的配送成本
cost_trans_dc_customer = gp.quicksum(
    (5 + 0.1 * Lji[j, i]) * qji[j, i] for j in range(n_dc_candidates) for i in range(n_customers))

# 成本项3：DC固定运营成本（仅建设的DC产生）+ 装卸成本
cost_operation = gp.quicksum(fixed_cost_dc[j] * y[j] + 8 * qS[j] for j in range(n_dc_candidates))

# 成本项4：DC库存持有成本（按周换算）
cost_inventory = gp.quicksum(qS[j] * 600 * 0.2 * (1 / 52) * (3 / 7) for j in range(n_dc_candidates))

# 总成本（最小化）
total_cost = cost_trans_factory_dc + cost_trans_dc_customer + cost_operation + cost_inventory
model.setObjective(total_cost, GRB.MINIMIZE)

# ===================== 5. 约束条件改进 =====================
# 约束1：工厂总发货量 = 所有客户总需求
model.addConstr(
    gp.quicksum(qS[j] for j in range(n_dc_candidates)) == gp.quicksum(di[i] for i in range(n_customers)),
    name="Total_Supply_Demand"
)

# 约束2：每个候选DC的流入量=流出量（流量守恒，仅建设的DC生效）
for j in range(n_dc_candidates):
    model.addConstr(
        qS[j] == gp.quicksum(qji[j, i] for i in range(n_customers)),
        name=f"Flow_Balance_DC_{j}"
    )

# 约束3：每个客户的需求必须被满足
for i in range(n_customers):
    model.addConstr(
        gp.quicksum(qji[j, i] for j in range(n_dc_candidates)) == di[i],
        name=f"Demand_Satisfaction_Customer_{i}"
    )

# 约束4：不建设的DC无运输量（核心选址约束）
for j in range(n_dc_candidates):
    model.addConstr(
        qS[j] <= M * y[j],
        name=f"No_Flow_Unbuilt_DC_{j}"
    )
    # 不是DC没有列车数
    model.addConstr(
        kj[j] <= M * y[j],
        name=f"No_Flow_Unbuilt_DC_{j}"
    )
    model.addConstr(
        kj[j] >= qS[j] / 2000,
        name=f"train_number_lb_{j}"
    )
    model.addConstr(
        kj[j] <= qS[j] / 2000 + 1,
        name=f"train_number_ub_{j}"
    )
# （可选）约束5：限制DC建设总数（若业务有数量要求）
# model.addConstr(gp.quicksum(y[j] for j in range(n_dc_candidates)) <= 5, name="Max_DC_Count")

# ===================== 6. 求解与结果输出 =====================
model.optimize()

# ===================== 7. 关键结果提取（聚焦DC选址） =====================
if model.status == GRB.OPTIMAL or model.status == GRB.TIME_LIMIT:
    print("\n===================== DC选址结果 =====================")
    # 提取建设的DC编号（j从0开始，对应44个候选点）
    built_dc = [j for j in range(n_dc_candidates) if y[j].X > 0.5]
    print(f"候选点中选中的DC编号：{built_dc}")
    print(f"最终建设DC数量：{len(built_dc)}")
    print(f"最小总成本（元/周）：{model.objVal:.2f}")
    print("\n===================== 列车数详情 =====================")
    for j in built_dc:
        print(f"DC候选点{j}：")
        print(f"  - 列车数：{kj[j].X:.2f}")
    # 输出建设DC的详细信息
    if built_dc:
        print("\n===================== 建设DC的运输详情 =====================")
        for j in built_dc:
            print(f"\nDC候选点{j}：")
            print(f"  - 工厂到货量：{qS[j].X:.2f} 吨/周")
            print(f"  - 服务客户的配送量（前5客户示例）：")
            for i in range(5):
                if qji[j, i].X > 1e-6:
                    print(f"    → 客户{i}：{qji[j, i].X:.2f} 吨/周")
else:
    print(f"模型求解失败，状态码：{model.status}")
    if model.status == GRB.INFEASIBLE:
        model.computeIIS()
        print("不可行约束：")
        for c in model.getConstrs():
            if c.IISConstr:
                print(c.ConstrName)

df = pd.DataFrame()
df["是否建立DC(y_j)"] = [y[j].X for j in range(n_dc_candidates)]
df["工厂到DC的运输量(qS_j)"] = [qS[j].X for j in range(n_dc_candidates)]
df["整列车数(k_j)"] = [kj[j].X for j in range(n_dc_candidates)]
for i in range(n_customers):
    df[f"DC到客户{i}配送量(qji_j_{i})"] = [qji[j, i].X for j in range(n_dc_candidates)]
df.to_excel(f"DC选址结果2_价格{model.objVal:.2f}.xlsx")

dcnparr = df["是否建立DC(y_j)"].to_numpy()
DClst = np.where(dcnparr == 1)[0]

plot_result(DClst, [qS[j].X for j in range(n_dc_candidates)],
            [[qji[j, i].X for i in range(n_customers)] for j in range(n_dc_candidates)],title=f"物流网络拓扑图2_价格{model.objVal:.2f}")
