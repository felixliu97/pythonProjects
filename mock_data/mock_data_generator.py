import csv
import random
from datetime import datetime, timedelta

departments = ["Electronics", "Clothing", "Home Appliances", "Books", "Toys"]
items = [
    {"code": "A001", "description": "Smartphone"},
    {"code": "B002", "description": "T-shirt"},
    {"code": "C003", "description": "Refrigerator"},
    {"code": "D004", "description": "Novel"},
    {"code": "E005", "description": "Action Figure"},
    {"code": "F006", "description": "Laptop"},
    {"code": "G007", "description": "Jeans"},
    {"code": "H008", "description": "Microwave"},
    {"code": "I009", "description": "Cookbook"},
    {"code": "J010", "description": "Board Game"},
    {"code": "K011", "description": "Headphones"},
    {"code": "L012", "description": "Dress"},
    {"code": "M013", "description": "Vacuum Cleaner"},
    {"code": "N014", "description": "Art Book"},
    {"code": "O015", "description": "Puzzle"}
]
salespersons = ["John", "Jane", "Alex", "Emily", "Michael", "David", "Sarah", "Daniel", "Olivia", "Andrew"]

def generate_mock_sales_data(num_records):
    sales_data = []
    current_date = datetime.now()

    for _ in range(num_records):
        department = random.choice(departments)
        sale_date = current_date - timedelta(days=random.randint(0, 1095))  # 3 years = 1095 days
        item = random.choice(items)
        amount = round(random.uniform(100, 1000), 2)
        quantity = random.randint(1, 10)
        item_code = item["code"]
        item_description = item["description"]
        salesperson = random.choice(salespersons)

        record = {
            "Department": department,
            "SaleDate": sale_date.strftime("%Y-%m-%d"),
            "Amount": amount,
            "Quantity": quantity,
            "ItemCode": item_code,
            "ItemDescription": item_description,
            "Salesperson": salesperson
        }

        sales_data.append(record)

    return sales_data

def save_sales_data_to_csv(sales_data, file_name):
    keys = sales_data[0].keys()
    with open(file_name, "w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=keys)
        writer.writeheader()
        writer.writerows(sales_data)

# Generate 4000 mock sales records
num_records = 4000
sales_data = generate_mock_sales_data(num_records)

# Save sales data to a CSV file
file_name = "sales_data.csv"
save_sales_data_to_csv(sales_data, file_name)

print(f"Sales data saved to {file_name} successfully.")
