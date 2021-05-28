from bs4 import BeautifulSoup
import requests

headers = {'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36'}

player_teammates_url = {
    'cristiano-ronaldo':'https://www.transfermarkt.com/cristiano-ronaldo/gemeinsamespiele/spieler/8198',
    'lionel-messi':'https://www.transfermarkt.com/lionel-messi/gemeinsameSpiele/spieler/28003',
    'zlatan-ibrahimovic':'https://www.transfermarkt.com/zlatan-ibrahimovic/gemeinsameSpiele/spieler/3455'
}

common_teammates = []

for _, url in player_teammates_url.items():
    response = requests.get(url, headers=headers)
    page = BeautifulSoup(response.text, 'html.parser')
    body = page.find('tbody')
    teamates_div = body.find('div')
    teammates = teamates_div.find_all('option')
    teammates_list = []

    for player in teammates:
        teammate = player.getText()
        if teammate != 'All teammates':
            teammates_list.append(teammate)
    # print(teammates_list)

    if len(common_teammates) == 0:
        common_teammates = teammates_list
    else:
        common_teammates = set(common_teammates).intersection(teammates_list)

print(common_teammates)