from bs4 import BeautifulSoup
import requests
import pandas as pd

# Real Estates
headers = {'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36'}
url = 'https://www.realestate.com.au/buy/in-mascot,+nsw+2020%3b/list-1?includeSurrounding=false'
response = requests.get(url, headers = headers)

soup = BeautifulSoup(response.text, 'html.parser')

# Properties div
properties_table = soup.find('div', class_= 'tiered-results tiered-results--exact')
properties = properties_table.findAll('div', {"role":"presentation"})
for property in properties:
    if property == None:
        continue
    else:
        address_h2 = property.find('h2', class_= 'residential-card__address-heading')
        if address_h2 == None:
            continue
        else:
            address = address_h2.find('span').getText()
            print(address)