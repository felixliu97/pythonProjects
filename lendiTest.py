import pyodbc
import pandas as pd
import xlrd

conn = pyodbc.connect('Driver={SQL Server};'
						'Server=FELIX-PC;'
						'Database=TestDB;'
						'Trusted_Connection=yes;')

cursor = conn.cursor()

#read excel data
data = pd.read_excel("G:\\Employee Turnover - Insights Analyst test.xlsx")

# export
data.to_excel('Employees.xlsx', index=False)

# Open the workbook and define the worksheet
book = xlrd.open_workbook("Employees.xlsx")
sheet = book.sheet_by_name("Sheet1")

#create table
query = """
USE [tempdb];

DROP TABLE IF EXISTS [dbo].[Employees];

CREATE TABLE [dbo].[Employees] (
	[First_Name] VARCHAR(MAX),
	[Last_Name] VARCHAR(MAX),
	[Full_Name] VARCHAR(MAX),
	[Gender] VARCHAR(MAX),
	[Date_of_birth] DATETIME,
	[Primary_manager] VARCHAR(MAX),
	[Employment_start_date] DATETIME,
	[Termination_date] DATETIME,
	[Teams] VARCHAR(MAX),
	[Termination_type] VARCHAR(MAX),
	[Termination_reason] VARCHAR(MAX),
	[Termination_comment] VARCHAR(MAX),
	[Job_title] VARCHAR(MAX),
	[Performance_Rating] INT
);

"""

# execute create table query
cursor.execute(query)

query = """
INSERT INTO [dbo].[Employees] (
	[First_Name],
	[Last_Name],
	[Full_Name],
	[Gender],
	[Date_of_birth],
	[Primary_manager],
	[Employment_start_date],
	[Termination_date],
	[Teams],
	[Termination_type],
	[Termination_reason],
	[Termination_comment],
	[Job_title],
	[Performance_Rating]
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);"""

for r in range(1, sheet.nrows):
	First_Name = sheet.cell(r,0).value
	Last_Name = sheet.cell(r,1).value
	Full_Name = sheet.cell(r,2).value
	Gender = sheet.cell(r,3).value
	Date_of_birth = sheet.cell(r,4).value
	Primary_manager = sheet.cell(r,5).value
	Employment_start_date = sheet.cell(r,6).value
	Termination_date = sheet.cell(r,7).value
	Teams = sheet.cell(r,8).value
	Termination_type = sheet.cell(r,9).value
	Termination_reason = sheet.cell(r,10).value
	Termination_comment = sheet.cell(r,11).value
	Job_title = sheet.cell(r,12).value
	Performance_Rating = sheet.cell(r,13).value

	# Assign values from each row
	values = (First_Name, Last_Name, Full_Name, Gender, Date_of_birth,
				Primary_manager, Employment_start_date, Termination_date, Teams, Termination_type,
				Termination_reason, Termination_comment, Job_title, Performance_Rating)

	# Execute sql Query
	cursor.execute(query, values)

conn.commit()
