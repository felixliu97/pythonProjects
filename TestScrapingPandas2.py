import requests
from bs4 import BeautifulSoup

url = "https://www.imdb.com/chart/top"
page = requests.get(url)
html_status = page.status_code

if int(html_status) == 200:
    soup = BeautifulSoup(page.content, 'html.parser')
    table = soup.find("table", {"class":"chart full-width"})
    rows = table.find_all("tr")
    for tr in rows:
        cols = tr.find("td", {"class":"titleColumn"})
        if cols == None:
            continue
        # text = cols.renderContents().strip()
        # print(text)
        name = cols.find('a').get_text()
        title = cols.find('a')['title']
        print(name + ' | ' + title)
        # name = movie.find('a href').string
        # print(name)
    
    # CVE_Information = soup.find(class_ ="col-lg-9 col-md-7 col-sm-12")

    # allEle=[elm['data-testid'] for elm in CVE_Information.find_all(attrs={"data-testid": True})] #storing 'data-testid' attribute values in the array

    # for i in allEle:
    #   print(CVE_Information.find(attrs={'data-testid': i}).get_text().strip())
else:
    print("Error in connection or wrong URL")