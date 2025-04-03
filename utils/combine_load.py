#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
将多个区域的负荷数据按时间合并为总负荷
"""

import os
import pandas as pd
import glob
from pathlib import Path

def combine_load_data(input_files, output_file):
    """
    将多个区域的负荷数据按时间加和
    
    Args:
        input_files: 输入的CSV文件列表
        output_file: 输出的CSV文件路径
    """
    print(f"合并负荷数据从 {len(input_files)} 个文件...")
    
    # 存储所有区域的数据
    all_data = []
    
    # 读取每个CSV文件
    for file_path in input_files:
        try:
            # 提取区域名称
            region = Path(file_path).stem.replace('load_', '').replace('_hourly', '')
            
            # 读取CSV文件
            df = pd.read_csv(file_path)
            
            # 确保datetime列是正确的格式
            df['datetime'] = pd.to_datetime(df['datetime'])
            
            # 添加区域标识
            df['region'] = region
            
            # 将数据添加到列表
            all_data.append(df)
            
            print(f"成功读取 {file_path}, 包含 {len(df)} 行数据")
        
        except Exception as e:
            print(f"读取 {file_path} 时出错: {e}")
    
    if not all_data:
        print("没有成功读取任何数据文件")
        return False
    
    try:
        # 合并所有区域的数据
        combined_df = pd.concat(all_data, ignore_index=True)
        
        # 按时间分组并计算负荷总和
        total_df = combined_df.groupby('datetime')['load_kW'].sum().reset_index()
        
        
        # 添加PV_power_rate列，值全为0
        total_df['PV_power_rate'] = 0
        
        # 格式化datetime为字符串
        total_df['datetime'] = total_df['datetime'].dt.strftime('%Y-%m-%d %H:%M:%S')
        
        # 保存到CSV
        total_df.to_csv(output_file, index=False)
        print(f"已将合并后的数据保存到: {output_file}")
        print(f"合并后的数据样本:")
        print(total_df.head(3))
        
        # 显示总负荷的基本统计信息
        print(f"\n总负荷统计信息:")
        print(f"数据行数: {len(total_df)}")
        print(f"最小负荷: {total_df['load_kW'].min():.2f} kW")
        print(f"最大负荷: {total_df['load_kW'].max():.2f} kW")
        print(f"平均负荷: {total_df['load_kW'].mean():.2f} kW")
        print(f"总负荷: {total_df['load_kW'].sum():.2f} kWh")
        
        return True
    
    except Exception as e:
        print(f"合并数据时出错: {e}")
        return False

def main():
    # 设置输入和输出文件路径
    input_files = [
        'data/load_E13_hourly.csv',
        'data/load_E25_hourly.csv',
        'data/load_E37_hourly.csv',
        'data/load_E39_hourly.csv'
    ]
    
    output_file = 'data/load_total_hourly.csv'
    
    # 确保输出目录存在
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # 合并负荷数据
    combine_load_data(input_files, output_file)

if __name__ == "__main__":
    main()
    print("处理完成")
