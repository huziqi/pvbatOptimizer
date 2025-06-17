import pandas as pd
import os

# 设置目录路径
base_dir = 'data/net_load/roof_facade'

# 定义时间粒度子文件夹
time_granularities = ['15min', '1h_mean', '1h_max']

# 地块列表
locations = ['E_13', 'E_25', 'E_37', 'E_39']

print("开始汇总净负荷数据...")

# 处理每种时间粒度
for granularity in time_granularities:
    print(f"\n处理 {granularity} 数据...")
    
    # 构建输入目录路径
    input_dir = os.path.join(base_dir, granularity)
    
    # 存储所有地块的数据
    all_dfs = []
    
    # 读取每个地块的数据
    for location in locations:
        file_path = os.path.join(input_dir, f'net_load_{location}.csv')
        
        if os.path.exists(file_path):
            df = pd.read_csv(file_path)
            df['DateTime'] = pd.to_datetime(df['DateTime'])
            
            # 重命名功率列以包含地块信息
            df = df.rename(columns={'Total Power (kW)': f'Power_{location}'})
            
            all_dfs.append(df)
            print(f"  读取 {location}: {len(df)} 个数据点")
        else:
            print(f"  警告: 文件不存在 - {file_path}")
    
    if len(all_dfs) == 0:
        print(f"  错误: 没有找到任何数据文件")
        continue
    
    # 合并所有数据（按时间对齐）
    print(f"  合并 {len(all_dfs)} 个地块的数据...")
    
    # 从第一个DataFrame开始
    merged_df = all_dfs[0].copy()
    
    # 逐个合并其他DataFrame
    for i in range(1, len(all_dfs)):
        merged_df = pd.merge(merged_df, all_dfs[i], on='DateTime', how='inner')
    
    print(f"  合并后数据点数: {len(merged_df)}")
    
    # 计算总净负荷（所有地块功率之和）
    power_columns = [col for col in merged_df.columns if col.startswith('Power_')]
    merged_df['Total Power (kW)'] = merged_df[power_columns].sum(axis=1)
    
    # 创建最终的输出DataFrame
    result_df = pd.DataFrame({
        'DateTime': merged_df['DateTime'],
        'Total Power (kW)': merged_df['Total Power (kW)']
    })
    
    # 按时间排序
    result_df = result_df.sort_values('DateTime')
    
    # 生成输出文件名
    output_file = os.path.join(input_dir, f'total_net_load_{granularity}.csv')
    
    # 保存汇总数据
    result_df.to_csv(output_file, index=False)
    
    print(f"  生成汇总文件: {output_file}")
    print(f"  汇总数据点数: {len(result_df)}")
    
    # 显示统计信息
    total_avg = result_df['Total Power (kW)'].mean()
    total_max = result_df['Total Power (kW)'].max()
    total_min = result_df['Total Power (kW)'].min()
    
    print(f"  总净负荷统计:")
    print(f"    平均值: {total_avg:.2f} kW")
    print(f"    最大值: {total_max:.2f} kW")
    print(f"    最小值: {total_min:.2f} kW")
    
    # 显示各地块的贡献
    print(f"  各地块平均贡献:")
    for location in locations:
        col_name = f'Power_{location}'
        if col_name in merged_df.columns:
            avg_power = merged_df[col_name].mean()
            contribution = (avg_power / total_avg) * 100 if total_avg != 0 else 0
            print(f"    {location}: {avg_power:.2f} kW ({contribution:.1f}%)")

print("\n所有净负荷数据汇总完成！")
print("生成的汇总文件:")
for granularity in time_granularities:
    output_file = os.path.join(base_dir, granularity, f'total_net_load_{granularity}.csv')
    print(f"- {output_file}")
print("文件格式: DateTime, Total Power (kW)")
print("总净负荷 = 所有地块净负荷之和") 