import pandas as pd
import numpy as np

# 读取CSV文件
df = pd.read_csv('Caxec_FY24.csv')

# 将Date列转换为datetime格式
df['Date'] = pd.to_datetime(df['Date'])

# 添加Category列
def set_category(row):
    if row['Credit Amount'] > 0:
        if row['Narrative'] == 'INTEREST PAID':
            return 'GST Free Income'
        elif ('salary' in row['Narrative'].lower()):
            return 'GST On Income'
        else:
            return 'Not reportable'
    elif row['Debit Amount'] > 0:
        if not any(keyword in row['Narrative'].lower() for keyword in ['tax office', 'pymt electronic payment','superchoice','salary','suqing liu ubank','anz offset','tfr westpac bus']):
            return 'GST On Cost'
        elif any(keyword in row['Narrative'].lower() for keyword in ['pymt electronic payment','superchoice','salary']):
            return 'Salary/Super Payment'
        else:
            return 'Not reportable'
    else:
        return ''

def calculate_income_gst(row):
    if row['Category'] == 'GST On Income':
        return round(row['Credit Amount'] / 11, 2)
    return None

def calculate_cost_gst(row):
    if row['Category'] == 'GST On Cost':
        return round(row['Debit Amount'] / 11, 2)
    return None

def calculate_net_income(row):
    if row['Category'] in ['GST On Income', 'GST Free Income']:
        return row['Credit Amount'] - row['Income GST']
    return None

def calculate_net_cost(row):
    if row['Category'] == 'GST On Cost':
        return row['Debit Amount'] - row['Cost GST']
    elif row['Category'] == 'Salary/Super Payment':
        return row['Debit Amount']
    return None

df['Category'] = df.apply(set_category, axis=1)
df['Income GST'] = df.apply(calculate_income_gst, axis=1)
df['Cost GST'] = df.apply(calculate_cost_gst, axis=1)
df['Net Income'] = df.apply(calculate_net_income, axis=1)
df['Net Cost'] = df.apply(calculate_net_cost, axis=1)

# 按日期排序
df = df.sort_values('Date')

# 创建汇总行
summary_row = pd.DataFrame({
    'Date': ['Total'],
    'Narrative': ['Summary'],
    'Debit Amount': [df['Debit Amount'].sum()],
    'Credit Amount': [df['Credit Amount'].sum()],
    'Balance': [df['Balance'].iloc[-1]],  # 使用最后一个余额
    'Categories': [''],
    'Category': [''],
    'Income GST': [df['Income GST'].sum()],
    'Cost GST': [df['Cost GST'].sum()],
    'Net Income': [df['Net Income'].sum()],
    'Net Cost': [df['Net Cost'].sum()]
})

# 将汇总行添加到DataFrame末尾
df = pd.concat([df, summary_row], ignore_index=True)

# 保存到新的CSV文件
df.to_csv('Caxec_FY24_updated.csv', index=False)

# 显示前几行和最后一行数据以验证
print("\n前5行数据（按日期排序）:")
print(df.head())
print("\n汇总行:")
print(df.tail(1))

# 显示Category统计信息
print("\nCategory统计信息:")
print(df['Category'].value_counts())

