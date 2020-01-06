import os
import pandas as pd
import numpy as np
from pymongo import MongoClient
import difflib
from collections import defaultdict
from fuzzywuzzy import process
from fuzzywuzzy import fuzz
import csv
import unidecode
from bson.objectid import ObjectId

def fixture_player_names(lst_fixture, col_fixture):
    '''
    build list of tuple: (name, position) from fixture data
    INPUT:
        - lst_fixture: list of fixture data
        - col_fixture: mongo collection for fixture
    OUPUT:
        - list of tuple
    '''

    lst_names = []

    for match in lst_fixture:
        result = col_fixture.find_one({'_id':ObjectId(match['_id'])}, {'_id':0, 'squad_a_report': 1, 'squad_b_report': 1})
        lst_squad_a = result['squad_a_report']
        lst_squad_b = result['squad_b_report']
        for player in lst_squad_a:
            if (player['Player'], player['Pos']) not in lst_names:
                lst_names.append((player['Player'], player['Pos']))
        for player in lst_squad_b:
            if (player['Player'], player['Pos']) not in lst_names:
                lst_names.append((player['Player'], player['Pos']))
    
    return lst_names

def salary_player_names(df_salary):
    '''
    build list of tuple: (name, position) from salary data
    INPUT:
        - df_salary: pandas Dataframe of salary data
    
    OUTPUT
        - list of tuple
    '''
    
    a = df_salary.name.tolist()
    b = df_salary.position.tolist()
    #c = df_salary._id.tolist()

    return [ (a[i], b[i]) for i in range(len(a)) ]

def match_names_fixture_salary(lst_A, lst_B, dict_names = {}, cutoff=0.9):
    '''
    build names map by using difflib
    INPUT:
        - lst_A: list of name
        - lst_B: list of name
        - dict_names
        - cutoff: float 
    
    OUTPUT
        - None
    '''

    for name_a in lst_A:
        if name_a not in dict_names.keys():
            name_b = difflib.get_close_matches(unidecode.unidecode(name_a), lst_B, n=1, cutoff=cutoff)
            if name_b:
                dict_names[name_a] = name_b

    return None

def match_names_fixture_salary_fuzzywuzzy(lst_A, lst_B, dict_names = {}, cutoff=89):
    '''
    build names map by using fuzzywuzzy. takes time.
    INPUT:
        - lst_A: list of name
        - lst_B: list of name
        - dict_names
        - cutoff: float 
    
    OUTPUT
        - None
    '''
    for name_a in lst_A:
        if name_a not in dict_names.keys():
            name_b = process.extractOne(unidecode.unidecode(name_a), lst_B, scorer=fuzz.partial_token_sort_ratio, score_cutoff=cutoff)
            if name_b:
                dict_names[name_a] = name_b[0] #tuple(name, score)
    return None

def load_names(path = "./src/tool/names.csv"):
    '''
    load name mapping into dictionary
    INPUT:
        - path: string
    OUTPUT
        - dictionary
    '''

    dict_names = {}
    with open(path, 'r') as f:
        for line in f:
            key, value = line.rstrip().split(',')
            dict_names[key] = value
    return dict_names

def save_names(dict_names, path = "./src/tool/names.csv"):
    '''
    same name mapping dictionary
    INPUT:
        - dict_names: dictionary {fixture player name: salary player name}
        - path: string
    OUTPUT
        - None
    '''
    with open(path, 'w') as f:
        for key, value in dict_names.items():
            f.write(f"{key},{value}\n")

    return None

def save_notfound(lst_notfound, path = "./src/tool/notfound.csv"):
    '''
    save player names not found
    INPUT:
        - lst_notfound: list of string
        - path: string
    OUTPUT
        - None
    '''
    with open(path, 'w') as f:
        for name in dict_names
            f.write(f"{name}\n")

    return None



if __name__=='__main__':

    total_notfound = set()
    dict_names = load_names()

    client = MongoClient('localhost', 27017)
    db = client.premier_league
    
    col_fixtures = [db.fixture_2018, db.fixture_2017, db.fixture_2016. db.fixture_2015. db.fixture_2014]
    col_salaries = [db.salary_2018, db.salary_2017, db.salary_2016, db.salary_2015, db.salary_2014]

    for col_fixture in col_fixtures:
        lst_fixture = list(col_fixture.find({}, {'squad_a_report': 0, 'squad_b_report': 0}))
        #df_fixture = pd.DataFrame(lst_fixture)
        lst_names_fixture = fixture_player_names(lst_fixture, col_fixture)
        lst_A_names = [lst_names_fixture[i][0] for i in range(len(lst_names_fixture))]

        for salary in col_salaries:
            lst_salary = list(salary.find())
            df_salary = pd.DataFrame(lst_salary)
            lst_names_salary = salary_player_names(df_salary)
            lst_B_names = [lst_names_salary[i][0] for i in range(len(lst_names_salary))]

            #match_names_fixture_salary(lst_A_names, lst_B_names, dict_names)
            match_names_fixture_salary_fuzzywuzzy(lst_A_names, lst_B_names, dict_names)
        
        notfound = set(lst_A_names) - set(dict_names.keys())
        total_notfound = total_notfound.union(notfound)
    
    save_names(dict_names)
    save_notfound(total_notfound)
    
   