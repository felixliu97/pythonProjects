from bs4 import BeautifulSoup
import requests
import pandas as pd

# Top 250 movies IMDB
url = 'https://www.imdb.com/chart/top/?ref_=nv_mv_250'
response = requests.get(url)

soup = BeautifulSoup(response.text, 'html.parser')

# DataFrame
columns = ['Name', 'Title', 'URL', 'Year', 'Rating', 'Reviewers']
df = pd.DataFrame(columns=columns)

# Get movies table
table = soup.find('table', class_ = 'chart full-width')

# Iterator
i = 1

# Title td
title_td = table.findAll('td', class_ = 'titleColumn')
for movie in title_td:
	link = movie.find('a')
	url = 'https://www.imdb.com/' + link.get('href')
	title = link.get('title')
	name = link.getText()
	year = int(movie.find('span').getText().strip("()"))

	df.at[i, 'Name'] = name
	df.at[i, 'Title'] = title
	df.at[i, 'URL'] = url
	df.at[i, 'Year'] = year
	i += 1

# Reset Iterator
i = 1

# Rating td
rating_td = table.findAll('td', class_ = 'ratingColumn imdbRating')
for movie in rating_td:
	review = movie.find('strong')
	rating = float(review.getText())
	reviewText = review.get('title')
	reviewers = int(reviewText.split()[3].replace(',',''))

	df.at[i, 'Rating'] = rating
	df.at[i, 'Reviewers'] = reviewers
	i += 1

df.to_csv('Top_250_Movies.csv', index=False, encoding='utf-8')