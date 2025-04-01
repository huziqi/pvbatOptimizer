import matplotlib.pyplot as plt
import numpy as np
# 运行结果中的最优电池容量数据（单位：kWh）
battery_capacities = [
    100000.00,  # 第1次
    100000.00,
    100000.00,  # 第1次
    50076.84,   # 第2次
    45835.97,   # 第3次
    45383.40,   # 第4次
    45368.99,   # 第5次
    45368.99,   # 第6次
]

# 绘制折线图
plt.figure(figsize=(8, 5))
plt.plot([0.99,0.95,0.9, 0.8, 0.7, 0.6, 0.5, 0.4], battery_capacities, marker='o', linestyle='-', color='b', label='Battery Capacity')

# 添加图例、标题和坐标轴标签
plt.xlabel('Sell Price Ratio', fontsize=12)
plt.ylabel('Optimal Battery Capacity (kWh)', fontsize=12)
# plt.xticks(np.arange(0.9, 0.1, -0.1))  # 横轴刻度从0.9到0.1
plt.xticks([0.99,0.95,0.9,0.8,0.7,0.6,0.5,0.4], ['0.99','0.95','0.9','0.8','0.7','0.6','0.5','0.4'])

plt.grid(True, linestyle='--', alpha=0.7)
plt.legend(fontsize=10)

# 显示图表
plt.tight_layout()
plt.savefig('examples/test.png')