import requests
from bs4 import BeautifulSoup

url = 'https://www.realestate.com.au/buy/'
suburb = 'mascot'
state = 'nsw'
postcode = '2020'

url = url + 'in-' + suburb + ',+' + state + '+' + postcode + '/list-1'
print(url)