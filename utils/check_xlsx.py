#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
检查Excel文件的结构
"""

import os
import sys
import subprocess

def check_xlsx_file(file_path):
    """
    检查Excel文件的结构
    
    Args:
        file_path: Excel文件路径
    """
    if not os.path.exists(file_path):
        print(f"文件不存在: {file_path}")
        return
    
    # 文件基本信息
    file_size = os.path.getsize(file_path) / 1024  # 转换为KB
    print(f"文件: {file_path}")
    print(f"大小: {file_size:.2f} KB")
    
    # 尝试使用file命令获取文件类型信息
    try:
        file_type = subprocess.check_output(['file', file_path], universal_newlines=True)
        print(f"文件类型: {file_type.strip()}")
    except:
        print("无法获取文件类型信息")
    
    # 尝试使用strings命令提取可读文本
    try:
        print("\n尝试提取Excel文件中的可读文本...")
        # 使用strings命令提取可读文本，并通过grep过滤可能包含日期、时间或数字的行
        strings_output = subprocess.check_output(
            f"strings {file_path} | grep -E '[0-9]{{2}}:[0-9]{{2}}|[0-9]{{4}}-[0-9]{{2}}|^[0-9]+\\.[0-9]+$' | head -n 30",
            shell=True,
            universal_newlines=True
        )
        print("可能的数据样本:")
        print(strings_output)
    except:
        print("无法提取文件中的可读文本")

def main():
    # 检查命令行参数
    if len(sys.argv) < 2:
        print("使用方法: python3 check_xlsx.py <excel文件路径>")
        return
    
    file_path = sys.argv[1]
    check_xlsx_file(file_path)

if __name__ == "__main__":
    main() 