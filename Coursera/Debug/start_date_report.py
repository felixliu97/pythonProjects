#!/usr/bin/env python3

import csv
import datetime
import requests

FILE_URL = "https://storage.googleapis.com/gwg-hol-assets/gic215/employees-with-date.csv"

def get_start_date():
    """Interactively get the start date to query for."""

    print()
    print('Getting the first start date to query for.')
    print()
    print('The date must be greater than Jan 1st, 2018')
    year = int(input('Enter a value for the year: '))
    month = int(input('Enter a value for the month: '))
    day = int(input('Enter a value for the day: '))
    print()

    return datetime.datetime(year, month, day)

def get_file_lines(url):
    """Returns the lines contained in the file at the given URL"""

    # Download the file over the internet
    response = requests.get(url, stream=True)
    lines = []

    for line in response.iter_lines():
        lines.append(line.decode("UTF-8"))
    return lines

def get_same_or_newer(start_date):
    """Returns the employees that started on the given date, or the closest one."""
    data = get_file_lines(FILE_URL)
    reader = csv.DictReader(data)
    date_dict = {}

    for raw in reader :
        raw_date = datetime.datetime.strptime(raw['Start Date'], '%Y-%m-%d')
        if raw_date > start_date :
            date_dict[raw_date.strftime("%b %d, %Y")] = [raw['Name'] + ' ' + raw['Surname']]
    date_dict_order = sorted(date_dict.items(), key=lambda x : x[0])
    for i in date_dict_order :
        print('Started on {}: {}'.format(i[0], i[1]))

def main():
    start_date = get_start_date()
    get_same_or_newer(start_date)

if __name__ == "__main__":
    main()