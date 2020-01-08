import os
import pandas as pd
import numpy as np
import re
from decimal import Decimal
from collections import defaultdict

from tool import fixturedata
from tool import namematch

import importlib
importlib.reload(fixturedata)

import matplotlib.pyplot as plt
plt.style.use('classic')
%matplotlib inline
import seaborn as sns
sns.set()


def f_point_squad_a(row):
    if row['goal_a'] > row['goal_b']:
        val = 3
    elif row['goal_a'] < row['goal_b']:
        val = 0
    else:
        val = 1
    return val

def f_point_squad_b(row):
    if row['goal_a'] < row['goal_b']:
        val = 3
    elif row['goal_a'] > row['goal_b']:
        val = 0
    else:
        val = 1
    return val

def populate_column(df):
    #win, loss, draw
    df['squad_a_win'] = df.goal_a > df.goal_b
    df['squad_b_win'] = df.goal_a < df.goal_b
    df['squad_draw'] = df.goal_a == df.goal_b
    
    #point 3, 0, 1
    df['squad_a_point'] = df.apply(f_point_squad_a, axis=1)
    df['squad_b_point'] = df.apply(f_point_squad_b, axis=1)

    #salary delta
    df['squad_a_delta'] = df['squad_a_salary'] - df['squad_b_salary']
    df['squad_b_delta'] = df['squad_b_salary'] - df['squad_a_salary']

    #change salary column to int
    df = df.astype({'squad_a_salary':'int64', 'squad_b_salary':'int64', 'squad_a_delta':'int64', 'squad_b_delta':'int64'})

    return df


def fold_df(df):

    df_a = df[["date", "squad_a", "squad_a_salary", "squad_a_delta",  "goal_a", "goal_b", "squad_a_point"]]
    df_b = df[["date", "squad_b", "squad_b_salary", "squad_b_delta",  "goal_b", "goal_a", "squad_b_point"]]

    df_a = df_a.rename(columns = {"squad_a": "squad_name", "squad_a_salary": "squad_salary", "squad_a_delta": "squad_delta", "goal_a": "goal_win", "goal_b": "goal_loss", "squad_a_point":"squad_point"})
    df_b = df_b.rename(columns = {"squad_b": "squad_name", "squad_b_salary": "squad_salary", "squad_b_delta": "squad_delta", "goal_b": "goal_win", "goal_a": "goal_loss", "squad_b_point":"squad_point"})

    return df_a.append(df_b)

def analyze_by_team(df):

    df = fold_df(df)

    df_team = df.groupby("squad_name").agg(
        average_salary=pd.NamedAgg(column='squad_salary', aggfunc=np.mean),
        average_delta=pd.NamedAgg(column='squad_delta', aggfunc=np.mean),
        average_goal_win=pd.NamedAgg(column='goal_win', aggfunc=np.mean),
        average_goal_loss=pd.NamedAgg(column='goal_loss', aggfunc=np.mean),
        total_squad_point=pd.NamedAgg(column='squad_point', aggfunc=np.sum)
        )
    
    print(df_team.corr())



    #KDE plot between salary and point
    with sns.axes_style('white'):
        sns.jointplot("average_salary", "total_squad_point", df_team, kind='kde')

    #Regression Analysis
    with sns.axes_style('white'):
        sns.jointplot("average_salary", "total_squad_point", df_team, kind='reg')

    #correlation
    corr_salary_point = df_team['average_salary'].corr(df_team['total_squad_point'])
    print(f"correlation between Salary and Point: {corr_salary_point}")

    return df_team

    


if __name__=='__main__':

    df = fixturedata.build_fixture_dataframe()
    #df = pd.read_pickle('./data/fixture.pkl')

    df = populate_column(df)

    df_team = analyze_by_team(df)
    print(df_team.sort_values(by="average_salary").head(5))
    

    # df = fold_df(df)

    # #Manchester City
    # df_man = df[df.squad_name == "Manchester City"]    
    
    # #histogram of salary
    # plt.hist(df_man.squad_salary)



    # df_man_salary_point = df_man[["squad_salary", "squad_point"]]
    

    # #KDE plot for salary and point
    # with sns.axes_style('white'):
    # sns.jointplot("squad_salary", "squad_point", df_man, kind='kde');
    
    # #KDE plot for delta and point
    # with sns.axes_style('white'):
    # sns.jointplot("squad_delta", "squad_point", df_man, kind='hex')

    # sns.pairplot(df, size=2.5)

    # #why squad_delta strictly normaly distributed
    # with sns.axes_style('white'):
    # sns.jointplot("squad_delta", "squad_point", df, kind='reg')

    # #time series
    # df_man.set_index('date', inplace=True)

#df_c = df[['goal_a', 'goal_b', 'squad_a_win', 'squad_b_win', 'squad_draw', 'squad_a_salary', 'squad_b_salary']]