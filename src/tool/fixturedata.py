import os
import pandas as pd
import numpy as np
import re
from pymongo import MongoClient
from decimal import Decimal
from bson.objectid import ObjectId
from collections import defaultdict

from tool import namematch

import importlib
importlib.reload(namematch)
import math



def calculate_average_salary(lst_squad, df_salary):
    '''
    cacluate the team squad value for players at the match.

    INPUT:
        - lst_squad: list of player
        - col_salary: mongo collection for salary data
    OUPUT:
        - float
    '''

    dict_names = namematch.load_names()
    #dict_notfound = namematch.load_notfound()

    total_salary = 0
    total_minute = 0
    for player in lst_squad:
        minutes = player['Min']
        if math.isnan(minutes):
            # fix Nan value for some players minutes. close to 0 minutes played.
            minutes = 0

        name = dict_names.get(player['Player'])
        if name is None:
            pass # no added salary, no added minute for the player
        else:
            salary = df_salary.loc[df_salary['name'] == name, 'salary'].iloc[0]
            if salary > 0:
                total_salary += (salary * minutes)
                total_minute += minutes
            else:
                pass
    
    return total_salary/total_minute

def build_salary_dataframe(salary_year):
    '''
    
    INPUT: salary_year: string
    '''

    client = MongoClient('localhost', 27017)
    db = client.premier_league


    #try dictionary get function.
    if salary_year == '2018':
        lst_tbl_salary = [db.salary_2018, db.salary_2019, db.salary_2017, db.salary_2016, db.salary_2015, db.salary_2014]
    elif salary_year == '2017':
        lst_tbl_salary = [db.salary_2017, db.salary_2018, db.salary_2016, db.salary_2015, db.salary_2014, db.salary_2019]
    elif salary_year == '2016':
        lst_tbl_salary = [db.salary_2016, db.salary_2017, db.salary_2015, db.salary_2014, db.salary_2018, db.salary_2019]
    elif salary_year == '2015':
        lst_tbl_salary = [db.salary_2015, db.salary_2016, db.salary_2014, db.salary_2017, db.salary_2018, db.salary_2019]
    elif salary_year == '2014':
        lst_tbl_salary = [db.salary_2014, db.salary_2015, db.salary_2016, db.salary_2017, db.salary_2018, db.salary_2019]


    lst_salary = list(lst_tbl_salary.pop(0).find())
    df_salary = pd.DataFrame(lst_salary)

    for tbl in lst_tbl_salary:
        lst = list(tbl.find())
        df = pd.DataFrame(lst)
        df_only = df[df.name.isin(df_salary.name) == False]
        df_salary = df_salary.append(df_only, ignore_index=True)

    df_salary.loc[df_salary.salary.isna(), ['salary']] = 0 # set 0 for null value in column.
    df_salary.loc[df_salary.transfer.isna(), ['transfer']] = 0
    
    return df_salary

def build_fixture_dataframe(fixture_year):

    client = MongoClient('localhost', 27017)
    db = client.premier_league

    #try dictionary get function
    dict_tables = {
        '2018': db.fixture_2018,
        '2017': db.fixture_2017,
        '2016': db.fixture_2016,
        '2015': db.fixture_2015,
        '2014': db.fixture_2014
    }

    lst_fixture = list(dict_tables[fixture_year].find({}, {'squad_a_report': 0, 'squad_b_report': 0}))  
        
    df_salary = build_salary_dataframe(fixture_year)

    for match in lst_fixture:
        result = dict_tables[fixture_year].find_one({'_id':ObjectId(match['_id'])}, {'_id':0, 'squad_a_report': 1, 'squad_b_report': 1})
        lst_squad_a = result['squad_a_report']
        lst_squad_b = result['squad_b_report']
        
        match['squad_a_salary'] =  calculate_average_salary(lst_squad_a, df_salary)
        match['squad_b_salary'] =  calculate_average_salary(lst_squad_b, df_salary)

    df_fixture = pd.DataFrame(lst_fixture)

    return df_fixture

if __name__ == "__main__":

    df_2018 = build_fixture_dataframe('2018')
    df_2017 = build_fixture_dataframe('2017')
    df_2016 = build_fixture_dataframe('2016')
    df_2015 = build_fixture_dataframe('2015')
    #df_2014 = build_fixture_dataframe('2014') #failed to load





