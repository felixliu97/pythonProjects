# we import the class that we need scraping our blog
import pandas as pd
import requests
from bs4 import BeautifulSoup

# we create a response variable

response = requests.get('https://blog.hlab.tech/')

# we initialize beautiful soup and pass in our response

soup = BeautifulSoup(response.text, 'html.parser')

# we create a variable called posts and we know that our all our blog posts are in a div called blog-entry-content

posts = soup.findAll(class_='blog-entry-content')

columns = ['Title', 'Link', 'Date']
df = pd.DataFrame(columns=columns)

#iterator
i = 1

for post in posts:
    title_class = post.find(class_='blog-entry-title entry-title')
    title = title_class.get_text().replace('\n', '')
    link = title_class.find('a')['href']
    date = post.select('.blog-entry-date.clr')[0].get_text()
    df.at[i, 'Title'] = title
    df.at[i, 'Link'] = link
    df.at[i, 'Date'] = date
    i += 1

print(df)