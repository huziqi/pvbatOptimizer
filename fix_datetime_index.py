import pandas as pd
import os
from datetime import datetime, timedelta

# 设置输入目录
input_dir = 'data/PV_raw_data/1h'

# 获取所有CSV文件
csv_files = [f for f in os.listdir(input_dir) if f.endswith('.csv')]

# 处理每个CSV文件
for csv_file in csv_files:
    input_path = os.path.join(input_dir, csv_file)
    
    # 读取CSV文件
    df = pd.read_csv(input_path)
    
    # 获取数据总行数
    total_rows = len(df)
    
    # 创建新的日期时间索引
    # 从1990-01-01 00:00:00开始，按小时递增
    start_date = datetime(1990, 1, 1, 0, 0, 0)
    new_datetimes = []
    
    for i in range(total_rows):
        new_datetime = start_date + timedelta(hours=i)
        new_datetimes.append(new_datetime.strftime('%Y-%m-%d %H:%M:%S'))
    
    # 替换DateTime列
    df['DateTime'] = new_datetimes
    
    # 保存回原文件
    df.to_csv(input_path, index=False)
    print(f'已修复: {csv_file} (共{total_rows}行数据)')

print('所有文件的日期索引已修复完成！')
print('新的日期格式: yyyy-mm-dd hh:mm:ss')
print('日期从1990-01-01 00:00:00开始按小时连续递增') 