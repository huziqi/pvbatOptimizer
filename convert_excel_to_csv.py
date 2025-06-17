import pandas as pd
import os

# 设置输入和输出目录
input_dir = 'data/PV_raw_data/excel/roof_facade'
output_dir = 'data/PV_raw_data/roof_facade/15min'

# 创建输出目录（如果不存在）
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# 获取所有Excel文件
excel_files = [f for f in os.listdir(input_dir) if f.endswith('.xlsx')]

# 转换每个Excel文件
for excel_file in excel_files:
    # 构建完整的文件路径
    input_path = os.path.join(input_dir, excel_file)
    output_path = os.path.join(output_dir, excel_file.replace('.xlsx', '.csv'))
    
    # 读取Excel文件
    df = pd.read_excel(input_path)
    
    # 保存为CSV文件
    df.to_csv(output_path, index=False, encoding='utf-8')
    print(f'已转换: {excel_file} -> {os.path.basename(output_path)}')

print('所有文件转换完成！') 