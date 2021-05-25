from bs4 import BeautifulSoup
import requests
import pandas as pd
from requests.models import Response

headers = {'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36'}

player_teammates_url = {
    'Kobe-Bryant':'https://basketball.realgm.com/player/Kobe-Bryant/Teammates/613',
    'Derrick-Rose':'https://basketball.realgm.com/player/Derrick-Rose/Teammates/756',
    'Giannis-Antetokounmpo':'https://basketball.realgm.com/player/Giannis-Antetokounmpo/Teammates/49629',
    'Dwight-Howard':'https://basketball.realgm.com/player/Dwight-Howard/Teammates/376',
    'Kyle-Lowry':'https://basketball.realgm.com/player/Kyle-Lowry/Teammates/78',
    'Kawhi-Leonard':'https://basketball.realgm.com/player/Kawhi-Leonard/Teammates/2256'
}

common_teammates = []

for player, url in player_teammates_url.items():
    response = requests.get(url, headers=headers)
    page = BeautifulSoup(response.text, 'html.parser')
    teammates_table = page.find('tbody')
    teammates = teammates_table.find_all('tr')
    teammates_list = []
    for player in teammates:
        teammate = player.find('td').find('a').getText()
        teammates_list.append(teammate)
    # print(teammates_list)

    if len(common_teammates) == 0:
        common_teammates = teammates_list
    else:
        common_teammates = set(common_teammates).intersection(teammates_list)

print(common_teammates)