from bs4 import BeautifulSoup
import requests

headers = {'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36'}

player_teammates_url = {
    # 'Kobe-Bryant':'https://basketball.realgm.com/player/Kobe-Bryant/Teammates/613',
    # 'Derrick-Rose':'https://basketball.realgm.com/player/Derrick-Rose/Teammates/756',
    # 'Giannis-Antetokounmpo':'https://basketball.realgm.com/player/Giannis-Antetokounmpo/Teammates/49629',
    # 'Dwight-Howard':'https://basketball.realgm.com/player/Dwight-Howard/Teammates/376',
    # 'Kyle-Lowry':'https://basketball.realgm.com/player/Kyle-Lowry/Teammates/78',
    # 'Kawhi-Leonard':'https://basketball.realgm.com/player/Kawhi-Leonard/Teammates/2256',
    'LeBron-James':'https://basketball.realgm.com/player/LeBron-James/Teammates/250',
    'Dwyane-Wade':'https://basketball.realgm.com/player/Dwyane-Wade/Teammates/450',
    # 'Kevin-Durant':'https://basketball.realgm.com/player/Kevin-Durant/Teammates/34',
    # 'Kevin-Garnett':'https://basketball.realgm.com/player/Kevin-Garnett/Teammates/644',
    'Chris-Paul':'https://basketball.realgm.com/player/Chris-Paul/Teammates/61',
    # 'Kyrie-Irving':'https://basketball.realgm.com/player/Kyrie-Irving/Teammates/7118',
    # 'Rajon-Rondo':'https://basketball.realgm.com/player/Rajon-Rondo/Teammates/93',
    # 'JR-Smith':'https://basketball.realgm.com/player/JR-Smith/Teammates/386',
    # 'Jason-Kidd':'https://basketball.realgm.com/player/Jason-Kidd/Teammates/302',
    # 'Chauncey-Billups':'https://basketball.realgm.com/player/Chauncey-Billups/Teammates/197',
    # 'Allen-Iverson':'https://basketball.realgm.com/player/Allen-Iverson/Teammates/603',
    # 'Shaquille-ONeal':'https://basketball.realgm.com/player/Shaquille-ONeal/Teammates/755',
    # 'Trevor-Ariza':'https://basketball.realgm.com/player/Trevor-Ariza/Teammates/398',
    # 'James-Harden':'https://basketball.realgm.com/player/James-Harden/Teammates/1598',
    # 'Stephen-Curry':'https://basketball.realgm.com/player/Stephen-Curry/Teammates/1600',
    # 'Russell-Westbrook':'https://basketball.realgm.com/player/Russell-Westbrook/Teammates/759',
    # 'Anthony-Davis':'https://basketball.realgm.com/player/Anthony-Davis/Teammates/13305',
    # 'Jimmy-Butler':'https://basketball.realgm.com/player/Jimmy-Butler/Teammates/6160',
    'Carmelo-Anthony':'https://basketball.realgm.com/player/Carmelo-Anthony/Teammates/452'
}

greens_teammates_url = {
    'Gerald-Green':'https://basketball.realgm.com/player/Gerald-Green/Teammates/354',
    'Danny-Green':'https://basketball.realgm.com/player/Danny-Green/Teammates/1642',
    # 'Draymond-Green':'https://basketball.realgm.com/player/Draymond-Green/Teammates/2369',
    'Jeff-Green':'https://basketball.realgm.com/player/Jeff-Green/Teammates/37'
}

sixth_man_teammates_url = {
    'Jordan-Clarkson':'https://basketball.realgm.com/player/Jordan-Clarkson/Teammates/22892',
    'Montrezl-Harrell':'https://basketball.realgm.com/player/Montrezl-Harrell/Teammates/24290',
    'Lou-Williams/':'https://basketball.realgm.com/player/Lou-Williams/Teammates/140',
    'Eric-Gordon':'https://basketball.realgm.com/player/Eric-Gordon/Teammates/762'
}

common_teammates = []

# for _, url in player_teammates_url.items():
# for _, url in greens_teammates_url.items():
for _, url in sixth_man_teammates_url.items():
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