import pandas as pd
import os
import numpy as np

# 设置输入和输出目录
input_dir = 'data/PV_raw_data/roof_facade/1h'
output_dir = 'data/PV_raw_data/roof_facade/15min'

# 创建输出目录（如果不存在）
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# 获取所有CSV文件
csv_files = [f for f in os.listdir(input_dir) if f.endswith('.csv')]

# 处理每个CSV文件
for csv_file in csv_files:
    # 构建完整的文件路径
    input_path = os.path.join(input_dir, csv_file)
    output_path = os.path.join(output_dir, csv_file)
    
    # 读取CSV文件
    df = pd.read_csv(input_path)
    
    # 确保时间列是datetime类型
    df['DateTime'] = pd.to_datetime(df['DateTime'])
    
    # 创建15分钟间隔的时间序列
    new_times = []
    new_values = []
    
    for idx, row in df.iterrows():
        # 获取当前小时的值
        current_value = row['Total Power (kW)']
        current_time = row['DateTime']
        
        # 每个15分钟的功率等于1小时的功率（功率是瞬时值，不是累积值）
        value_per_15min = current_value
        
        # 创建4个15分钟的时间点
        for i in range(4):
            new_time = current_time + pd.Timedelta(minutes=15*i)
            new_times.append(new_time)
            new_values.append(value_per_15min)
    
    # 创建新的DataFrame
    new_df = pd.DataFrame({
        'DateTime': new_times,
        'Total Power (kW)': new_values
    })
    
    # 按时间排序
    new_df = new_df.sort_values('DateTime')
    
    # 保存为CSV文件
    new_df.to_csv(output_path, index=False)
    print(f'已转换: {csv_file}')

print('所有文件转换完成！')