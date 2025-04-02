#!/home/user/anaconda3/bin/python
# -*- coding: utf-8 -*-

"""
提取2024年用电负荷数据并按小时粒度合并
将15分钟粒度的数据整合为1小时粒度
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime
import glob

def show_excel_structure(xlsx_file):
    """
    显示Excel文件的结构
    
    Args:
        xlsx_file: Excel文件路径
    """
    try:
        # 读取Excel文件
        df = pd.read_excel(xlsx_file)
        
        # 显示列信息
        print(f"\nExcel文件结构 ({xlsx_file}):")
        print(f"列名: {df.columns.tolist()}")
        print(f"数据类型:\n{df.dtypes}")
        
        # 显示前5行数据
        print("\n前5行数据:")
        print(df.head(5))
        
        # 显示数据统计信息
        print("\n数据统计信息:")
        print(f"行数: {len(df)}")
        
        # 检查是否有时间列
        date_cols = [col for col in df.columns if df[col].dtype in ['datetime64[ns]', 'object']]
        for col in date_cols:
            try:
                # 尝试将列转换为日期时间类型
                test_dates = pd.to_datetime(df[col])
                # 检查是否转换成功
                if not pd.isna(test_dates).all():
                    print(f"可能的时间列: {col}")
                    # 显示日期时间范围
                    min_date = test_dates.min()
                    max_date = test_dates.max()
                    print(f"日期范围: {min_date} 至 {max_date}")
            except:
                pass
        
        return df
    except Exception as e:
        print(f"读取Excel文件时出错: {e}")
        return None

def extract_load_data(xlsx_file, output_csv):
    """
    从xlsx文件中提取2024年的用电负荷数据，并按小时粒度整合
    
    Args:
        xlsx_file: 输入的Excel文件路径
        output_csv: 输出的CSV文件路径
    """
    print(f"正在处理文件: {xlsx_file}")
    
    # 读取Excel文件
    try:
        df = pd.read_excel(xlsx_file)
        print(f"Excel文件已读取，共有{len(df)}行数据")
    except Exception as e:
        print(f"读取Excel文件时出错: {e}")
        return False
    
    # 根据实际Excel结构确定处理方法
    # 检查是否包含'日期'列和时间点列(如'00:00', '00:15'等)
    columns = df.columns.tolist()
    if '日期' in columns and '00:00' in columns and '00:15' in columns:
        print("检测到标准格式: 包含'日期'列和时间点列")
        return process_standard_format(df, output_csv)
    else:
        print("未检测到标准格式，尝试通用处理方法")
        return process_generic_format(df, output_csv)

def process_standard_format(df, output_csv):
    """
    处理标准格式的Excel文件：包含'日期'列和每15分钟的负荷列
    
    Args:
        df: 数据框
        output_csv: 输出CSV文件路径
    """
    # 检查日期列的类型和值
    print(f"日期列的类型: {df['日期'].dtype}")
    print(f"日期列的前5个值: {df['日期'].head(5).tolist()}")
    
    # 特殊处理整数格式的日期
    if df['日期'].dtype == 'int64':
        # 假设日期是以YYYYMMDD格式存储的整数
        try:
            # 将整数转换为字符串，然后解析为日期
            df['日期字符串'] = df['日期'].astype(str)
            df['日期解析'] = pd.to_datetime(df['日期字符串'], format='%Y%m%d', errors='coerce')
            
            # 检查是否成功转换
            if df['日期解析'].isna().all():
                print("无法将整数日期转换为日期时间格式")
                return False
            
            # 使用转换后的日期列
            date_col = '日期解析'
            print(f"已将整数日期列转换为日期时间格式")
            print(f"日期范围: {df[date_col].min()} 到 {df[date_col].max()}")
        except Exception as e:
            print(f"转换日期时出错: {e}")
            return False
    else:
        # 尝试常规方式转换日期
        try:
            df['日期解析'] = pd.to_datetime(df['日期'], errors='coerce')
            if df['日期解析'].isna().all():
                print("无法将日期列转换为日期时间格式")
                return False
            date_col = '日期解析'
            print(f"日期范围: {df[date_col].min()} 到 {df[date_col].max()}")
        except:
            print("无法将日期列转换为日期时间格式")
            return False
    
    # 筛选2024年的数据
    df_2024 = df[df[date_col].dt.year == 2024].copy()
    print(f"2024年数据共有{len(df_2024)}行")
    
    if len(df_2024) == 0:
        print("没有找到2024年的数据")
        return False
    
    # 获取所有15分钟间隔的时间列
    time_columns = [col for col in df_2024.columns if ':' in col and len(col) == 5]
    time_columns.sort()  # 确保按时间顺序排列
    
    if not time_columns:
        print("未找到时间点列")
        return False
    
    print(f"找到{len(time_columns)}个时间点列")
    
    # 创建一个新的DataFrame来存储小时粒度的数据
    hourly_data = []
    
    # 对于每一天
    for date in df_2024[date_col].unique():
        # 将numpy.datetime64转换为pandas的Timestamp
        date_pd = pd.Timestamp(date)
        date_str = date_pd.strftime('%Y-%m-%d')
        day_data = df_2024[df_2024[date_col] == date].iloc[0]  # 获取这一天的数据行
        
        # 调试: 处理日期 date_str 的第0小时数据
        print(f"调试: 处理日期 {date_str} 的第0小时数据")
        hour_str = "00"
        hour_columns = [f"{hour_str}:00", f"{hour_str}:15", f"{hour_str}:30", f"{hour_str}:45"]
        for col in hour_columns:
            if col in day_data:
                print(f"列 {col} 的值: {day_data[col]}")
        
        # 对于每小时，取该小时内的4个15分钟值的总和
        for hour in range(24):
            hour_str = f"{hour:02d}"
            # 该小时的4个15分钟时间点
            hour_columns = [f"{hour_str}:00", f"{hour_str}:15", f"{hour_str}:30", f"{hour_str}:45"]
            
            # 过滤实际存在的列
            existing_columns = [col for col in hour_columns if col in time_columns]
            
            if existing_columns:
                # 提取值并打印调试信息(仅对第一个小时)
                if hour == 0:
                    print(f"第0小时的列: {existing_columns}")
                    for col in existing_columns:
                        print(f"列 {col} 的值: {day_data[col]}")
                
                # 计算总负荷(加和)
                values = [day_data[col] for col in existing_columns]
                # 过滤掉非数值
                numeric_values = [v for v in values if isinstance(v, (int, float)) and not np.isnan(v)]
                
                if numeric_values:
                    total_load = sum(numeric_values)
                    if hour == 0:
                        print(f"第0小时的值总和: {total_load}")
                    # 添加到结果列表
                    hourly_data.append({
                        'datetime': f"{date_str} {hour_str}:00:00",
                        'load': total_load
                    })
    
    # 创建DataFrame并排序
    result_df = pd.DataFrame(hourly_data)
    result_df['datetime'] = pd.to_datetime(result_df['datetime'])
    result_df = result_df.sort_values('datetime')
    result_df['datetime'] = result_df['datetime'].dt.strftime('%Y-%m-%d %H:%M:%S')
    
    # 添加PV_power_rate列，值全为0
    result_df['PV_power_rate'] = 0
    
    # 显示处理后的数据样本
    print("处理后的数据样本:")
    print(result_df.head(3))
    print(f"总计生成{len(result_df)}小时的数据")
    
    # 保存到CSV
    result_df.to_csv(output_csv, index=False)
    print(f"已将数据保存到: {output_csv}")
    
    return True

def process_generic_format(df, output_csv):
    """
    通用方法处理Excel文件
    
    Args:
        df: 数据框
        output_csv: 输出CSV文件路径
    """
    # 尝试找到日期/时间列
    date_col = None
    for col in df.columns:
        # 如果是整数型，可能是YYYYMMDD格式
        if pd.api.types.is_integer_dtype(df[col]):
            try:
                # 转换为字符串再解析
                date_strings = df[col].astype(str)
                test_dates = pd.to_datetime(date_strings, format='%Y%m%d', errors='coerce')
                if not test_dates.isna().all():
                    df[col + '_日期'] = test_dates
                    date_col = col + '_日期'
                    print(f"找到整数日期列: {col}，已转换为: {date_col}")
                    break
            except:
                continue
        else:
            try:
                test_dates = pd.to_datetime(df[col], errors='coerce')
                if not test_dates.isna().all():
                    df[col + '_日期'] = test_dates
                    date_col = col + '_日期'
                    print(f"找到日期时间列: {col}，已转换为: {date_col}")
                    break
            except:
                continue
    
    if date_col is None:
        print("无法找到日期时间列")
        return False
    
    # 筛选2024年的数据
    df_2024 = df[pd.DatetimeIndex(df[date_col]).year == 2024].copy()
    print(f"2024年数据共有{len(df_2024)}行")
    
    if len(df_2024) == 0:
        print("没有找到2024年的数据")
        return False
    
    # 找出可能的负荷列
    load_col = None
    for col in df.columns:
        if col != date_col and pd.api.types.is_numeric_dtype(df[col]):
            load_col = col
            print(f"找到可能的负荷列: {load_col}")
            break
    
    if load_col is None:
        print("无法找到负荷列")
        return False
    
    # 创建小时粒度的时间列
    df_2024['hour'] = pd.DatetimeIndex(df_2024[date_col]).floor('H')
    
    # 按小时分组并计算负荷总和
    hourly_data = df_2024.groupby('hour')[load_col].sum().reset_index()
    
    # 重命名列
    hourly_data.columns = ['datetime', 'load']
    
    # 格式化日期时间为标准格式
    hourly_data['datetime'] = pd.DatetimeIndex(hourly_data['datetime']).strftime('%Y-%m-%d %H:%M:%S')
    
    # 添加PV_power_rate列，值全为0
    hourly_data['PV_power_rate'] = 0
    
    # 显示处理后的数据样本
    print("处理后的数据样本:")
    print(hourly_data.head(3))
    print(f"总计生成{len(hourly_data)}小时的数据")
    
    # 保存到CSV
    hourly_data.to_csv(output_csv, index=False)
    print(f"已将数据保存到: {output_csv}")
    
    return True

def process_all_files():
    """处理data目录下所有的xlsx文件"""
    # 获取所有xlsx文件
    xlsx_files = glob.glob('data/2024_*.xlsx')
    
    if not xlsx_files:
        print("未找到任何xlsx文件")
        return
    
    # 确保输出目录存在
    os.makedirs('data/processed', exist_ok=True)
    
    # 首先显示第一个文件的结构
    if xlsx_files:
        print("分析Excel文件结构...")
        show_excel_structure(xlsx_files[0])
    
    # 询问用户是否确认继续处理
    confirm = input("是否继续处理所有文件? (y/n): ")
    if confirm.lower() != 'y':
        print("已取消处理")
        return
    
    for xlsx_file in xlsx_files:
        # 从文件名中提取ID
        file_id = os.path.basename(xlsx_file).replace('.xlsx', '').replace('2024_', '')
        output_csv = f"data/processed/load_{file_id}_hourly.csv"
        
        # 处理文件
        result = extract_load_data(xlsx_file, output_csv)
        if result:
            print(f"成功处理文件: {xlsx_file}")
        else:
            print(f"处理文件失败: {xlsx_file}")
        print("-" * 50)

if __name__ == "__main__":
    process_all_files()
    print("所有文件处理完成")
