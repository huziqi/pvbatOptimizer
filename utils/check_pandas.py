#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
使用pandas读取Excel文件
"""

import os
import sys
import pandas as pd

def check_excel_file(file_path):
    """
    使用pandas读取Excel文件并显示其结构
    
    Args:
        file_path: Excel文件路径
    """
    if not os.path.exists(file_path):
        print(f"文件不存在: {file_path}")
        return
    
    try:
        # 读取Excel文件
        print(f"正在读取Excel文件: {file_path}")
        df = pd.read_excel(file_path)
        
        # 显示基本信息
        print("\n文件基本信息:")
        print(f"行数: {len(df)}")
        print(f"列数: {len(df.columns)}")
        print(f"列名: {df.columns.tolist()}")
        
        # 显示数据类型
        print("\n数据类型:")
        print(df.dtypes)
        
        # 显示前几行数据
        print("\n前5行数据:")
        print(df.head(5))
        
        # 检查是否有日期时间列
        date_columns = []
        for col in df.columns:
            # 尝试将列转换为日期时间类型
            try:
                if pd.api.types.is_datetime64_any_dtype(df[col]):
                    date_columns.append(col)
                elif pd.api.types.is_object_dtype(df[col]):
                    # 尝试转换
                    test = pd.to_datetime(df[col], errors='coerce')
                    if not test.isna().all():
                        date_columns.append(col)
            except:
                continue
        
        # 如果找到了日期时间列，显示日期范围
        if date_columns:
            print("\n找到可能的日期时间列:")
            for col in date_columns:
                try:
                    temp_dates = pd.to_datetime(df[col], errors='coerce')
                    min_date = temp_dates.min()
                    max_date = temp_dates.max()
                    print(f"列: {col}, 日期范围: {min_date} 至 {max_date}")
                except:
                    print(f"列: {col}, 无法确定日期范围")
        
    except Exception as e:
        print(f"处理Excel文件时出错: {e}")

def main():
    # 检查命令行参数
    if len(sys.argv) < 2:
        print("使用方法: python3 check_pandas.py <excel文件路径>")
        return
    
    file_path = sys.argv[1]
    check_excel_file(file_path)

if __name__ == "__main__":
    main() 