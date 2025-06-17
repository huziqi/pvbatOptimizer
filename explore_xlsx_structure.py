import pandas as pd
import os

# 查看一个xlsx文件的结构
xlsx_file = 'data/raw/2024_E13.xlsx'

print(f"正在查看文件: {xlsx_file}")
print("=" * 50)

# 读取xlsx文件
df = pd.read_excel(xlsx_file)

print("文件形状:", df.shape)
print("\n列名:")
print(df.columns.tolist())

print("\n前5行数据:")
print(df.head())

print("\n数据类型:")
print(df.dtypes)

print("\n如果有日期列，查看日期列的样本:")
if '日期' in df.columns:
    print("日期列样本:")
    print(df['日期'].head())
elif 'Date' in df.columns:
    print("Date列样本:")
    print(df['Date'].head())
elif '时间' in df.columns:
    print("时间列样本:")
    print(df['时间'].head())

print("\n查看所有包含时间的列名:")
time_columns = [col for col in df.columns if any(time_str in str(col) for time_str in [':', '00', '01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19', '20', '21', '22', '23'])]
print("可能的时间列:", time_columns[:10])  # 只显示前10个 