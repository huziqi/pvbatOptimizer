import pandas as pd
import os

# 设置输入和输出目录
input_dir = 'data/load_raw_data/15min'
output_dir = 'data/load_raw_data/1h_max'

# 创建输出目录（如果不存在）
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# 获取所有CSV文件
csv_files = [f for f in os.listdir(input_dir) if f.endswith('.csv')]

print(f"找到{len(csv_files)}个CSV文件")

# 处理每个CSV文件
for csv_file in csv_files:
    print(f"\n处理文件: {csv_file}")
    
    # 读取CSV文件
    input_path = os.path.join(input_dir, csv_file)
    df = pd.read_csv(input_path)
    
    # 确保时间列是datetime类型
    df['DateTime'] = pd.to_datetime(df['DateTime'])
    
    # 设置DateTime为索引
    df.set_index('DateTime', inplace=True)
    
    # 按小时聚合数据（取最大值）
    # 对于峰值负荷分析，取最大值更有意义
    hourly_df = df.resample('H').max()
    
    # 重置索引，使DateTime重新成为列
    hourly_df.reset_index(inplace=True)
    
    # 格式化DateTime列
    hourly_df['DateTime'] = hourly_df['DateTime'].dt.strftime('%Y-%m-%d %H:%M:%S')
    
    # 保存到输出目录
    output_path = os.path.join(output_dir, csv_file)
    hourly_df.to_csv(output_path, index=False)
    
    print(f"已聚合: {csv_file}")
    print(f"原始数据点: {len(df)}")
    print(f"聚合后数据点: {len(hourly_df)}")
    print(f"聚合比例: {len(df)} -> {len(hourly_df)} (1:4比例)")

print('\n所有负荷文件聚合完成！')
print('聚合方法: 15分钟数据取最大值')
print('输出格式: DateTime, Total Power (kW)')
print('时间粒度: 1小时')
print(f'输出目录: {output_dir}') 