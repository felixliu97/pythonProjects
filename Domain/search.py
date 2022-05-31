from bs4 import BeautifulSoup
import requests
import pandas as pd

# Real Estates
# headers = {'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36'}
headers = {'Content-Type': 'application/json; charset=utf-8'}

base_url = 'https://www.realestate.com.au'
action = 'sale'
suburb = 'cherrybrook'
state = 'nsw'
postcode = '2126'
property_type = 'house'
query_string = '?bedrooms=4-any&excludeunderoffer=1&ssubs=0'

url = f"{base_url}/{action}/{suburb}-{state}-{postcode}/{query_string}"
print(url)

response = requests.get(url, headers = headers)

soup = BeautifulSoup(response.text, 'html.parser')

print(response.text)

# Properties div
properties_table = soup.find('div', attrs={'data-testid': 'results'})
print(properties_table)
# properties = properties_table.findAll('div', {"role":"presentation"})
# for property in properties:
# 	if property == None:
# 		continue
# 	else:
# 		address_h2 = property.find('h2', class_= 'residential-card__address-heading')
# 		if address_h2 == None:
# 			continue
# 		else:
# 			address = address_h2.find('span').getText()
# 			print(address)
