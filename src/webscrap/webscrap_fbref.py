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

def find_match_report_paths(soup):
    '''
    find all paths to match report. 
    INPUT:
        - soup: soup object in node
    OUTPUT: list of tuple(path, name)
    '''
    td_paths = soup.find_all("td", attrs={"data-stat": "match_report"})
    dic_paths = {}

    for elem in td_paths:
        a_path = elem.select("a")
        if len(a_path):
            val = a_path[0]["href"]
            key = val.split('/')[-2]
            dic_paths[key] = val

    return dic_paths

def save_html_from_paths(paths, save_dir):
    '''
    retrieve html from paths and save to the designated directory
    INPUT:
        - paths: dictionary of key and url
        - save_dir: string of directory
    OUTPUP:
        None
    '''

    for key, url in paths.items():
        try:
            response = requests.get(url)
            cur_path = '{}/{}.html'.format(save_dir, key)
            
            # if not os.path.exists(os.path.dirname(filename)):
            #     try:
            #         os.makedirs(os.path.dirname(filename))
            #     except OSError as exc: # Guard against race condition
            #         if exc.errno != errno.EEXIST:
            #             raise
            with open(cur_path, 'w') as f:
                f.write(response.text)
                
        except HTTPError as http_err:
            print(f'HTTP error occured: {http_err}')
        except Exception as err:
            print(f'other error occured: {err}')
        else:
            pass

def procedure_to_retrieve_matchdata():
    '''
    explain procedure to retrieve all matchdata
    for each game in premier league from 2014 - 2019
    '''
    #1. save score&fixture html file for season 2014/2015 - 2018/2019
    #   https://fbref.com/en/comps/9/1889/schedule/2018-2019-Premier-League-Fixtures    
    
    #2. open a html file and load it to BeautifulSoup   
    path = './data/html/2014-2015 Premier League Scores & Fixtures | FBref.com.html'
    with open(path) as f:
        html_str = f.read()
    soup = BeautifulSoup(html_str, 'lxml')
    
    #3. find all url paths to match data and pair with keycode
    #   This site use unique keycode for each html/data
    dic_urls = find_match_report_paths(soup)


    #4. check number of dictionary. There are total 380 games each year.
    print(dic_urls, len(dic_urls))
    
    #5. retrieve all matchdata html and save to matchdata{year} directory.
    # 
    save_html_from_paths(dic_urls, './data/html/matchdata1415')

    #6. 'ls | wc' in the directory to count total html files. 380


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

def scrape_fixture_html(soup):
    '''
    build list of fixture from Premier Score&Fixture html.

    INPUT:
        - soup: BeautifulSoup object contains Premier Score&Fixture html
    OUTPUP:
        - list of dictionary
    '''
    
    tables = soup.find_all("table", class_="min_width sortable stats_table now_sortable")
    tbody = tables[0].find_all("tbody")
    trs = tbody[0].find_all("tr")

    lst_matchtable = []
    for tr in trs:
        #find a th and a td to check empty row
        th = tr.find_all("th", attrs={"data-stat": "gameweek"})
        td = tr.find_all("td", attrs={"data-stat": "match_report"})
        if th[0].text and td:
            dic_matchrow = {}
            key = td[0].a["href"].split('/')[-2]
            #set key here again in case of load into mongo
            dic_matchrow['datakey'] = key
            dic_matchrow['gameweek'] = th[0].text
            dic_matchrow['dayofweek'] = tr.find_all("td", attrs={"data-stat": "dayofweek"})[0].text
            dic_matchrow['date'] = tr.find_all("td", attrs={"data-stat": "date"})[0].text
            dic_matchrow['time'] = tr.find_all("td", attrs={"data-stat": "time"})[0].text
            dic_matchrow['squad_a'] = tr.find_all("td", attrs={"data-stat": "squad_a"})[0].text
            dic_matchrow['squad_b'] = tr.find_all("td", attrs={"data-stat": "squad_b"})[0].text
            #dic_matchrow['xg_a'] = tr.find_all("td", attrs={"data-stat": "xg_a"})[0].text
            #dic_matchrow['xg_b'] = tr.find_all("td", attrs={"data-stat": "xg_b"})[0].text

            lst_score = tr.find_all("td", attrs={"data-stat": "score"})[0].text.split('–')
            dic_matchrow['goal_a'] = lst_score[0]
            dic_matchrow['goal_b'] = lst_score[1]
            
            dic_matchrow['attendance'] = tr.find_all("td", attrs={"data-stat": "attendance"})[0].text
            dic_matchrow['venue'] = tr.find_all("td", attrs={"data-stat": "venue"})[0].text
            dic_matchrow['referee'] = tr.find_all("td", attrs={"data-stat": "referee"})[0].text
            lst_matchtable.append(dic_matchrow)

    return lst_matchtable

def scrap_matchreport(matchrow, save_dir):
    '''
    build two list of dictionary from matchreport html
    It does not include all columns.
    ? Do I have to include match datakey?
    INPUT:
        - matchrow: dictionary of match
    OUTPUP:
        - tuple of list of dictionary for both team
    '''
    cur_path = '{}/{}.html'.format(save_dir, matchrow['datakey'])

    soup = get_soup(cur_path)
    tables = soup.find_all("table", id=re.compile('^player_stats'))
    
    squad_a_datakey = tables[0]['id'].split('_')[-1]
    trs = tables[0].tbody.find_all('tr')
    lst_squad_a = []
    for tr in trs:
        dic_player = {}
        dic_player['squad_datakey'] = squad_a_datakey
        dic_player['name'] = tr.find_all('th')[0].text.strip()
        dic_player['shirtnumber'] = tr.find_all('td', attrs={"data-stat": "shirtnumber"})[0].text
        dic_player['minutes'] = tr.find_all('td', attrs={"data-stat": "minutes"})[0].text
        dic_player['goals'] = tr.find_all('td', attrs={"data-stat": "goals"})[0].text
        dic_player['assists'] = tr.find_all('td', attrs={"data-stat": "assists"})[0].text
        lst_squad_a.append(dic_player)
    
    squad_b_datakey = tables[1]['id'].split('_')[-1]
    trs = tables[1].tbody.find_all('tr')
    lst_squad_b = []
    for tr in trs:
        dic_player = {}
        dic_player['squad_datakey'] = squad_b_datakey
        dic_player['name'] = tr.find_all('th')[0].text.strip()
        dic_player['shirtnumber'] = tr.find_all('td', attrs={"data-stat": "shirtnumber"})[0].text
        dic_player['minutes'] = tr.find_all('td', attrs={"data-stat": "minutes"})[0].text
        dic_player['goals'] = tr.find_all('td', attrs={"data-stat": "goals"})[0].text
        dic_player['assists'] = tr.find_all('td', attrs={"data-stat": "assists"})[0].text
        lst_squad_b.append(dic_player)

    return (lst_squad_a, lst_squad_b)

def get_player_minutes_for_match(lst_squad):
    '''
    extract {players: minutes} from match report for a team in the match
    INPUT:
        - lst_squad: match report for a team
    OUTPUP:
        - dictionary of {players: played minutes}
    '''

    return {elem["name"] : elem["minutes"] for elem in lst_squad}

def scrap_matchreport_by_pandas(matchrow, save_dir):
    '''
    use pandas.read_html to retrieve two squad table
    This dfs can be used for embedded table into mongo

    INPUT:
        - matchrow: dictionary of match
        - save_dir: string for the location of match report htmls
    OUTPUP:
        - tuple of pandas dataframes for both team
    '''
    cur_path = '{}/{}.html'.format(save_dir, matchrow['datakey'])
    with open(cur_path) as f:
        html_str = f.read()


    dfs = pd.read_html(html_str, attrs={'id': re.compile('^player_stats')})
    if len(dfs) != 2:
        raise ValueError("pandas read html return list of dataframes other than 2")
    return tuple(dfs)

def convert_list_fixture_to_dataframe(lst_fixture):
    '''
    convert datatypes in match dataframe
    INPUT:
        - lst_matchtable: list of dictionary for match table
    OUTPUP:
        - DataFrame: with appropriate datatypes
    '''

    df_fixture = pd.DataFrame(lst_fixture)
    df_fixture = df_fixture.astype({'gameweek': np.int64,
                            'goal_a': np.int64, 
                            'goal_b': np.int64,
                            #'xg_a': np.double,
                            #'xg_b': np.double
    })
    df_fixture['date'] = pd.to_datetime(df_fixture['date'])
    df_fixture['attendance'] = df_fixture.attendance.str.replace(',','').astype(np.int64)

    return df_fixture

def build_fixture_matchreport_directory(soup, save_dir):
    '''
    build directory for fixture embedding match report.
    May be used for Mongo database

    INPUT:
        - soup: BeutifulSoup object for fixture&score html
        - save_dir: string for match report directory
    OUTPUP:
        - list of dictionary
    '''    
    lst_fixture = scrape_fixture_html(soup)
    df_fixture = convert_list_fixture_to_dataframe(lst_fixture)
    lst_fixture = df_fixture.to_dict('records')
    for match in lst_fixture:
        squad_a, squad_b = scrap_matchreport_by_pandas(match, save_dir)
        lst_squad_a = squad_a.to_dict('records')
        lst_squad_b = squad_b.to_dict('records')
        match['squad_a_report'] = lst_squad_a
        match['squad_b_report'] = lst_squad_b
    return lst_fixture

def procedure_to_dump_fixturedata_to_mongo():

    #1. load scores and fixture html
    soup = get_soup('./data/html/2014-2015 Premier League Scores & Fixtures | FBref.com.html')
    matchreport_dir = "./data/html/matchdata1415"

    #2. build list of dictionary data structure for mongo
    lst_fixture = build_fixture_matchreport_directory(soup, matchreport_dir)
    
    #3. open connection and insert the list
    client = MongoClient('localhost', 27017)
    db = client.premier_league
    collection = db.fixture_2014
    result = collection.insert_many(lst_fixture)
    print(len(result.inserted_ids))


if __name__=='__main__':

    #procedure_to_retrieve_matchdata()
    procedure_to_dump_fixturedata_to_mongo()



    


#matchtable[0]["squad_a_datakey"] = squad_a[0]["squad_datakey"]
#matchtable[0]["squad_b_datakey"] = squad_b[0]["squad_datakey"]


    


