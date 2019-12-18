import pandas as pd
import numpy as np
import seaborn as sns
import scipy.stats as stats
import matplotlib.pyplot as plt

import pandas.io.sql
import pyodbc

import xlrd
server = 'XXXXX'
db = 'XXXXXdb'

# create Connection and Cursor objects
conn = pyodbc.connect('DRIVER={SQL Server};SERVER=' + server + ';DATABASE=' + db + ';Trusted_Connection=yes')
cursor = conn.cursor()

# read data
data = pd.read_excel('Flash Daily Apps through 070918.xls')

# rename columns
data = data.rename(columns={'Lease Number': 'Lease_Number',
                            'Start Date': 'Start_Date',
                            'Report Status': 'Report_Status',
                            'Status Date': 'Status_Date',
                            'Current Status': 'Current_Status',
                            'Sales Rep': 'Sales_Rep',
                            'Customer Name': 'Customer_Name',
                            'Total Financed': 'Total_Financed',
                            'Rate Class': 'Rate_Class',
                            'Supplier Name': 'Supplier_Name'})

# export
data.to_excel('Daily Flash.xlsx', index=False)

# Open the workbook and define the worksheet
book = xlrd.open_workbook("Daily Flash.xlsx")
sheet = book.sheet_by_name("Sheet1")

query1 = """
CREATE TABLE [LEAF].[ZZZ] (
    Lease_Number varchar(255),
    Start_Date varchar(255),
    Report_Status varchar(255),
    Status_Date varchar(255),
    Current_Status varchar(255),
    Sales_Rep varchar(255),
    Customer_Name varchar(255),
    Total_Finance varchar(255),
    Rate_Class varchar(255),
    Supplier_Name varchar(255),
    DecisionStatus varchar(255)
)"""

query = """
INSERT INTO [LEAF].[ZZZ] (
    Lease_Number,
    Start_Date,
    Report_Status,
    Status_Date,
    Current_Status,
    Sales_Rep,
    Customer_Name,
    Total_Finance,
    Rate_Class,
    Supplier_Name,
    DecisionStatus
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""

# execute create table
try:
    cursor.execute(query1)
    conn.commit()
except pyodbc.ProgrammingError:
    pass

# grab existing row count in the database for validation later
cursor.execute("SELECT count(*) FROM LEAF.ZZZ")
before_import = cursor.fetchone()

for r in range(1, sheet.nrows):
    Lease_Number = sheet.cell(r,0).value
    Start_Date = sheet.cell(r,1).value
    Report_Status = sheet.cell(r,2).value
    Status_Date = sheet.cell(r,3).value
    Current_Status= sheet.cell(r,4).value
    Sales_Rep = sheet.cell(r,5).value
    Customer_Name = sheet.cell(r,6).value
    Total_Financed= sheet.cell(r,7).value
    Rate_Class = sheet.cell(r,8).value
    Supplier_Name = sheet.cell(r,9).value
    DecisionStatus= sheet.cell(r,10).value

    # Assign values from each row
    values = (Lease_Number, Start_Date, Report_Status, Status_Date, Current_Status,
              Sales_Rep, Customer_Name, Total_Financed, Rate_Class, Supplier_Name,
              DecisionStatus)

    # Execute sql Query
    cursor.execute(query, values)

# Commit the transaction
conn.commit()

# If you want to check if all rows are imported
cursor.execute("SELECT count(*) FROM LEAF.ZZZ")
result = cursor.fetchone()

print((result[0] - before_import[0]) == len(data.index))  # should be True

# Close the database connection
conn.close()