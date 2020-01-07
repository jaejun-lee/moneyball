#!/usr/bin/env python
# encoding: utf-8

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
    capcluate average salary for team squad actually played for the match.

    INPUT:
        - lst_squad: list of squad roll
        - col_salary: mongo collection for salary
    OUPUT:
        - float
    '''

    dict_names = namematch.load_names()
    dict_notfound = namematch.load_notfound()
    lst_notfound = dict_notfound.keys()

    total_salary = 0
    for player in lst_squad:
        minutes = player['Min']
        if math.isnan(minutes):
            # fix Nan value for some players minutes. close to 0 minutes played.
            minutes = 0
        
        try:
            if player['Player'] not in lst_notfound:
                #salary = df_salary[df_salary.name == dict_names[player['Player']]].salary[0]
                salary = df_salary.loc[df_salary['name'] == dict_names[player['Player']], 'salary'].iloc[0]
                if salary == 0:
                    salary = 100000.0
            else:
                salary = dict_notfound[player['Player']]
        except KeyError:
            print(f"keyError: {player['Player']}")
        except IndexError:
            print(f"IndexError: {player['Player']}")
        except:
            raise

        total_salary += (minutes/90) * salary
    
    return total_salary/11

def build_salary_dataframe():

    client = MongoClient('localhost', 27017)
    db = client.premier_league

    tbl_salary = db.salary_2018
    lst_salary = list(tbl_salary.find())
    df_salary = pd.DataFrame(lst_salary)

    lst_tbl_salary = [db.salary_2018, db.salary_2017, db.salary_2016, db.salary_2015, db.salary_2014]

    for tbl in lst_tbl_salary:
        lst = list(tbl.find())
        df = pd.DataFrame(lst)
        df_only = df[df.name.isin(df_salary.name) == False]
        df_salary = df_salary.append(df_only, ignore_index=True)

    df_salary.loc[df_salary.salary.isna(), ['salary']] = 0 # set 0 for null value in column.
    df_salary.loc[df_salary.transfer.isna(), ['transfer']] = 0
    
    return df_salary

def build_fixture_dataframe():

    client = MongoClient('localhost', 27017)
    db = client.premier_league
    tbl_fixture = db.fixture_2018

    lst_fixture = list(tbl_fixture.find({}, {'squad_a_report': 0, 'squad_b_report': 0}))  
        

    df_salary = build_salary_dataframe()

    for match in lst_fixture:
        result = tbl_fixture.find_one({'_id':ObjectId(match['_id'])}, {'_id':0, 'squad_a_report': 1, 'squad_b_report': 1})
        lst_squad_a = result['squad_a_report']
        lst_squad_b = result['squad_b_report']
        
        match['squad_a_salary'] =  calculate_average_salary(lst_squad_a, df_salary)
        match['squad_b_salary'] =  calculate_average_salary(lst_squad_b, df_salary)

    df_fixture = pd.DataFrame(lst_fixture)

    df_fixture['squad_a_win'] = df_fixture.goal_a > df_fixture.goal_b
    df_fixture['squad_b_win'] = df_fixture.goal_a < df_fixture.goal_b
    df_fixture['squad_draw'] = df_fixture.goal_a == df_fixture.goal_b

    return df_fixture


if __name__ == "__main__":
    pass