import pandas as pd
import os
from datetime import datetime, timedelta

# 设置输入和输出目录
input_dir = 'data/raw'
output_dir = 'data/PV_raw_data/15min'

# 确保输出目录存在
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# 获取所有xlsx文件
xlsx_files = [f for f in os.listdir(input_dir) if f.endswith('.xlsx')]

# 生成15分钟间隔的时间列表（一天96个间隔）
time_columns = []
for hour in range(24):
    for minute in [0, 15, 30, 45]:
        time_str = f"{hour:02d}:{minute:02d}"
        time_columns.append(time_str)

print(f"找到{len(xlsx_files)}个xlsx文件")
print(f"时间列数量: {len(time_columns)}")

# 处理每个xlsx文件
for xlsx_file in xlsx_files:
    print(f"\n处理文件: {xlsx_file}")
    
    # 读取xlsx文件
    input_path = os.path.join(input_dir, xlsx_file)
    df = pd.read_excel(input_path)
    
    # 创建输出文件名（去掉2024_前缀，添加.csv后缀）
    if xlsx_file.startswith('2024_'):
        output_filename = 'load_' + xlsx_file[5:].replace('.xlsx', '.csv')
    else:
        output_filename = 'load_' + xlsx_file.replace('.xlsx', '.csv')
    
    output_path = os.path.join(output_dir, output_filename)
    
    # 存储转换后的数据
    new_times = []
    new_values = []
    
    # 处理每一行（每一天）
    for idx, row in df.iterrows():
        # 解析日期
        date_str = str(int(row['日期']))  # 转换为字符串，去掉可能的小数点
        date_obj = datetime.strptime(date_str, '%Y%m%d')
        
        # 处理每个15分钟间隔
        for time_col in time_columns:
            if time_col in df.columns:
                # 创建完整的datetime
                hour, minute = map(int, time_col.split(':'))
                full_datetime = date_obj + timedelta(hours=hour, minutes=minute)
                
                # 获取负荷值
                load_value = row[time_col]
                if pd.isna(load_value):
                    load_value = 0.0
                
                new_times.append(full_datetime.strftime('%Y-%m-%d %H:%M:%S'))
                new_values.append(load_value)
            else:
                print(f"警告: 时间列 {time_col} 不存在于文件中")
    
    # 创建新的DataFrame
    new_df = pd.DataFrame({
        'DateTime': new_times,
        'Total Power (kW)': new_values
    })
    
    # 按时间排序
    new_df = new_df.sort_values('DateTime')
    
    # 保存为CSV文件
    new_df.to_csv(output_path, index=False)
    print(f"已转换: {xlsx_file} -> {output_filename}")
    print(f"数据点数量: {len(new_df)}")

print('\n所有负荷文件转换完成！')
print('输出格式: DateTime, Total Power (kW)')
print('时间粒度: 15分钟')
print(f'输出目录: {output_dir}') 