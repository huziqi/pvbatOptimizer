import pandas as pd
import os
from datetime import datetime

# 设置目录路径
pv_base_dir = 'data/PV_raw_data/roof_facade'
load_base_dir = 'data/load_raw_data'
output_base_dir = 'data/net_load/roof_facade'

# 确保输出目录存在
for subdir in ['15min', '1h_mean', '1h_max']:
    output_dir = os.path.join(output_base_dir, subdir)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

# 定义数据处理配置
data_configs = [
    {
        'name': '15min',
        'pv_dir': os.path.join(pv_base_dir, '15min'),
        'load_dir': os.path.join(load_base_dir, '15min'),
        'output_dir': os.path.join(output_base_dir, '15min')
    },
    {
        'name': '1h_mean',
        'pv_dir': os.path.join(pv_base_dir, '1h'),
        'load_dir': os.path.join(load_base_dir, '1h_mean'),
        'output_dir': os.path.join(output_base_dir, '1h_mean')
    },
    {
        'name': '1h_max',
        'pv_dir': os.path.join(pv_base_dir, '1h'),
        'load_dir': os.path.join(load_base_dir, '1h_max'),
        'output_dir': os.path.join(output_base_dir, '1h_max')
    }
]

# 获取地块列表
locations = [
    {'pv_name': 'E_13', 'load_name': 'E13'},
    {'pv_name': 'E_25', 'load_name': 'E25'},
    {'pv_name': 'E_37', 'load_name': 'E37'},
    {'pv_name': 'E_39', 'load_name': 'E39'}
]

print("开始处理净负荷数据...")

# 处理每种数据配置
for config in data_configs:
    print(f"\n处理 {config['name']} 数据...")
    
    for location in locations:
        pv_name = location['pv_name']
        load_name = location['load_name']
        print(f"  处理地块: {pv_name}")
        
        # 构建文件路径
        pv_file = os.path.join(config['pv_dir'], f"{pv_name}.csv")
        load_file = os.path.join(config['load_dir'], f"load_{load_name}.csv")
        output_file = os.path.join(config['output_dir'], f"net_load_{pv_name}.csv")
        
        # 检查文件是否存在
        if not os.path.exists(pv_file):
            print(f"    警告: PV文件不存在: {pv_file}")
            continue
        if not os.path.exists(load_file):
            print(f"    警告: 负荷文件不存在: {load_file}")
            continue
        
        # 读取PV数据
        pv_df = pd.read_csv(pv_file)
        print(f"    PV数据点数: {len(pv_df)}")
        
        # 读取负荷数据
        load_df = pd.read_csv(load_file)
        print(f"    负荷数据点数: {len(load_df)}")
        
        # 以负荷数据为基准，处理PV数据长度不一致的情况
        if len(pv_df) != len(load_df):
            print(f"    警告: 数据点数不一致 - PV: {len(pv_df)}, 负荷: {len(load_df)}")
            if len(pv_df) < len(load_df):
                # PV数据不足，用0填充缺失的部分
                missing_rows = len(load_df) - len(pv_df)
                print(f"    PV数据不足{missing_rows}个数据点，用0填充")
                
                # 创建缺失行的DataFrame，功率为0
                missing_data = pd.DataFrame({
                    'DateTime': [''] * missing_rows,  # 时间会从负荷数据获取
                    'Total Power (kW)': [0.0] * missing_rows
                })
                
                # 拼接PV数据
                pv_df = pd.concat([pv_df, missing_data], ignore_index=True)
            else:
                # PV数据多于负荷数据，截取到负荷数据长度
                print(f"    PV数据多于负荷数据，截取到负荷数据长度: {len(load_df)}")
                pv_df = pv_df.iloc[:len(load_df)].copy()
        
        # 创建净负荷数据
        # 净负荷 = 建筑负荷 - PV发电量
        net_load_df = pd.DataFrame()
        net_load_df['DateTime'] = load_df['DateTime'].copy()
        
        # 计算净负荷（确保PV数据为数值类型）
        pv_power = pd.to_numeric(pv_df['Total Power (kW)'], errors='coerce').fillna(0)
        load_power = pd.to_numeric(load_df['Total Power (kW)'], errors='coerce').fillna(0)
        
        net_load_df['Total Power (kW)'] = load_power - pv_power
        
        # 保存净负荷数据
        net_load_df.to_csv(output_file, index=False)
        
        print(f"    生成净负荷文件: {output_file}")
        print(f"    净负荷数据点数: {len(net_load_df)}")
        
        # 显示一些统计信息
        avg_load = load_power.mean()
        avg_pv = pv_power.mean()
        avg_net = net_load_df['Total Power (kW)'].mean()
        
        print(f"    平均负荷: {avg_load:.2f} kW")
        print(f"    平均PV: {avg_pv:.2f} kW")
        print(f"    平均净负荷: {avg_net:.2f} kW")

print("\n所有净负荷数据处理完成！")
print("输出目录结构:")
print("- data/net_load/15min/")
print("- data/net_load/1h_mean/")
print("- data/net_load/1h_max/")
print("文件格式: DateTime, Total Power (kW)")
print("净负荷 = 建筑负荷 - PV发电量") 