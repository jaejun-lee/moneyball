from bs4 import BeautifulSoup
import os
import requests
from requests.exceptions import HTTPError
import os
import errno
import pandas as pd
import numpy as np
import re
from pymongo import MongoClient
from decimal import Decimal


def get_soup(path):
    '''
    get soup from the designated html file
    INPUT: 
        - path: string
    OUTPUT: 
        - BeautifulSoup object
    '''
    with open(path) as f:
        html_str = f.read()
    return BeautifulSoup(html_str, 'lxml')

def scrape_salary_html(soup):
    '''
    scrape salary table
    INPUT: 
        - soup: BeautifulSoup object for salary html
    OUTPUT: 
        - list of dictionary
    '''

    table = soup.find_all('table', class_="datatable noborder tablesorter tablesorter-default")[0]
    trs = table.tbody.find_all('tr')
    lst_players = []
    for tr in trs:
        dict_player = {}
        dict_player['name'] = tr.select(".team-name")[0].text.strip()
        dict_player['position'] = tr.select(".rank-position")[0].text.strip()
        salary = tr.select(".rank-value")[0].text.strip()
        dict_player['salary'] = int(salary.replace(',', '').replace('£', ''))
        #value = Decimal(sub(r'[^\d.]', '', money))
        #value = float(money.replace(',', '').replace('£', ''))
        lst_players.append(dict_player)
    
    return lst_players

def scrape_transfer_html(soup):
    '''
    scrape transfer value table
    INPUT: 
        - soup: BeautifulSoup object for transfer html
    OUTPUT: 
        - list of dictionary
    '''

    table = soup.find_all('table', class_="datatable noborder tablesorter tablesorter-default")[0]
    trs = table.tbody.find_all('tr')
    lst_players = []
    for tr in trs:
        dict_player = {}
        dict_player['name'] = tr.select(".team-name")[0].text.strip()
        dict_player['position'] = tr.select(".rank-position")[0].text.strip()
        transfer = tr.select(".rank-value")[0].text.strip()
        dict_player['transfer'] = int(transfer.replace(',', '').replace('£', ''))
        #value = Decimal(sub(r'[^\d.]', '', money))
        #value = float(money.replace(',', '').replace('£', ''))
        lst_players.append(dict_player)
    
    return lst_players


if __name__=='__main__':

     #1. scrape salary and transfer htmls
    soup_salary = get_soup("./data/html/salary/EPL_Salary_Rankings_Spotrac_20182019.html")
    soup_transfer = get_soup("./data/html/salary/EPL_Transfer_Rankings_Spotrac_20182019.html")
    salaries = scrape_salary_html(soup_salary)
    transfers = scrape_transfer_html(soup_transfer)

    #2. build list of dictionary data structure for mongo
    df_salaries = pd.DataFrame(salaries)
    df_transfers = pd.DataFrame(transfers)
    df = pd.merge(left=df_salaries, right=df_transfers, on=['name', 'position'], how='outer')
    lst = df.to_dict('records')
    
    # #3. open connection and insert the list
    # client = MongoClient('localhost', 27017)
    # db = client.premier_league
    # collection = db.salary_2014
    # result = collection.insert_many(lst)
    # print(len(result.inserted_ids))

    
    
    

