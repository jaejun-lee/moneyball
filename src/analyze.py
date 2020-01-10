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
plt.style.use('ggplot')
#%matplotlib inline
import seaborn as sns
sns.set()

from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error

from scipy import stats



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
    '''
    generate columns to be analized based on the initial columns    
    
    INPUT:
        df: DataFrame
       
    OUTPUT
        DataFrame
    '''
    #win, loss, draw
    df['a_win'] = df.goal_a > df.goal_b
    df['b_win'] = df.goal_a < df.goal_b
    df['draw'] = df.goal_a == df.goal_b
    
    #point 3, 0, 1
    df['a_point'] = df.apply(f_point_squad_a, axis=1)
    df['b_point'] = df.apply(f_point_squad_b, axis=1)

    #salary delta
    df['a_salary_delta'] = df['squad_a_salary'] - df['squad_b_salary']
    df['b_salary_delta'] = df['squad_b_salary'] - df['squad_a_salary']
    df = df.astype({'squad_a_salary':'int64', 'squad_b_salary':'int64', 'a_salary_delta':'int64', 'b_salary_delta':'int64'})

    #goal delta
    df['a_goal_delta'] = df['goal_a'] - df['goal_b']
    df['b_goal_delta'] = df['goal_b'] - df['goal_a']

    return df


def fold_df(df):
    '''
    For team analysis, concat home team and away team  
    
    INPUT:
        df: DataFrame
    
    OUTPUT
        DataFrame
    '''

    df_a = df[["date", "squad_a", "squad_a_salary", "a_salary_delta",  "goal_a", "goal_b", "a_goal_delta", "a_point", 'season']]
    df_b = df[["date", "squad_b", "squad_b_salary", "b_salary_delta",  "goal_b", "goal_a", "b_goal_delta", "b_point", 'season']]

    df_a = df_a.rename(columns = {"squad_a": "squad", "squad_a_salary": "salary", "a_salary_delta": "salary_delta", "goal_a": "goal_win", "goal_b": "goal_loss", "a_goal_delta": "goal_delta", "a_point":"point"})
    df_b = df_b.rename(columns = {"squad_b": "squad", "squad_b_salary": "salary", "b_salary_delta": "salary_delta", "goal_b": "goal_win", "goal_a": "goal_loss", "b_goal_delta": "goal_delta", "b_point":"point"})

    df_a['home'] = True
    df_b['home'] = False

    return pd.concat([df_a, df_b])


def groupby_team(df):
    '''
    INPUT:
        df: DataFrame
       
    OUTPUT
        DataFrame
    '''

    df_team = df.groupby("squad").agg(
        mean_salary=pd.NamedAgg(column='salary', aggfunc=np.mean),
        mean_salary_delta=pd.NamedAgg(column='salary_delta', aggfunc=np.mean),
        total_goal_win=pd.NamedAgg(column='goal_win', aggfunc=np.sum),
        total_goal_loss=pd.NamedAgg(column='goal_loss', aggfunc=np.sum),
        mean_goal_delta=pd.NamedAgg(column="goal_delta", aggfunc=np.mean),
        total_point=pd.NamedAgg(column='point', aggfunc=np.sum)
        )
    
    return df_team

def correlation_salary_point(season, df):
    '''    
    INPUT:
        season: string
        df: DataFrame
       
    OUTPUT
        None
    '''
    with sns.axes_style('white'):
        plot = sns.jointplot("mean_salary", "total_point", df, kind='reg')
        plot.savefig(f"../images/pairplot_team_salary_point_season_{season}")
    
    corr_val = df.mean_salary.corr(df.total_point)
    print(f"for the season '{season}', The correlation between Average Salary and Total Point earned is {corr_val:0.2f}")

def correlation_salary_goal(season, df):
    '''    
    INPUT:
        season: string
        df: DataFrame
       
    OUTPUT
        None
    '''
    with sns.axes_style('white'):
        plot = sns.jointplot("mean_salary", "mean_goal_delta", df, kind='reg')
        plot.savefig(f"../images/pairplot_team_salary_goal_delta_season_{season}")

    corr_val = df.mean_salary.corr(df.mean_goal_delta)
    print(f"for the season '{season}', The correlation between Average Salary and Average Goal Delta is {corr_val:0.2f}")

def display_top_5_salary(season, df):
    '''    
    INPUT:
        season: string
        df: DataFrame
       
    OUTPUT
        None
    '''
    df_sorted = df.sort_values(by="mean_salary", ascending=False)
    print(df_sorted[['mean_salary', 'mean_goal_delta', 'total_point']].head(5))

    ax = df_sorted.head(5).plot.barh(y="mean_salary")
    fig = ax.figure
    fig.set_size_inches(8, 5)
    fig.tight_layout(pad=1)
    fig.savefig(f"../images/Bar_the_top5_team_salary_{season}")

def display_top_5_point(season, df):
    '''    
    INPUT:
        season: string
        df: DataFrame
       
    OUTPUT
        None
    '''
    df_sorted = df.sort_values(by="total_point", ascending=False)
    print(df_sorted[['mean_salary', 'mean_goal_delta', 'total_point']].head(5))

    ax = df_sorted.head(5).plot.barh(y="total_point")
    fig = ax.figure
    fig.set_size_inches(8, 5)
    fig.tight_layout(pad=1)
    fig.savefig(f"../images/Bar_the_top5_team_point_{season}")

def analyze_by_team(df):
    '''
    Analyze teams performance for each season based on the team salary.
    INPUT:
        - df: DataFrame
    '''

    groupd = df.groupby("season")
    df_2018 = groupd.get_group("2018_2019")
    df_2017 = groupd.get_group("2017_2018")
    df_2016 = groupd.get_group("2016_2017")
    df_2015 = groupd.get_group("2015_2016")

    dict_df = {"all": df, "2018_2019": df_2018, "2017_2018": df_2017, "2016_2017": df_2016, "2015_2016": df_2015}

    for key, value in dict_df.items():
        dict_df[key] = fold_df(value)
    
    for key, value in dict_df.items():
        dict_df[key] = groupby_team(value)

    for key, value in dict_df.items():
        correlation_salary_point(key, value)

    for key, value in dict_df.items():
        correlation_salary_goal(key, value)
    
    for key, value in dict_df.items():
        display_top_5_salary(key, value)
    
    for key, value in dict_df.items():
        display_top_5_point(key, value)

    analyze_by_team_season_2015(dict_df["2015_2016"])

    return dict_df["all"]

def analyze_by_team_season_2015(df):
    pass


def analyze_salary_delta_with_goal_delta(df):
    '''
    INPUT:
        - df: DataFrame
    '''
    #analyze only home side, otherwise, it is duplicate
    df = fold_df(df).groupby('home').get_group(True)
    df['salary_delta'] = df['salary_delta'] - 1000

    ax = df.boxplot(column='salary_delta', by="goal_delta", vert=False)
    ax.set_title('Distribution of Salary Delta per Goal Delta')
    ax.set_xlabel('Salary Delta')
    ax.set_ylabel('Goal Delta')

    fig = ax.figure
    #fig.set_size_inches(5,5)
    fig.tight_layout(pad=1)
    fig.suptitle('')
    fig.savefig('../images/boxplot_goal_delta_salary_delta')  
    
    with sns.axes_style('white'):
        plot = sns.jointplot("salary_delta", "goal_delta", df, kind='reg')
        plot.savefig(f"../images/pair_plot_salary_delta_goal_delta")

    corr_val = df.salary_delta.corr(df.goal_delta)
    print(f"The correlation between Salary Delta and Goal Delta is {corr_val:0.2f}")

def analyze_salary_delta_with_point(df):
    '''
    INPUT:
        - df: DataFrame
    '''
    df = fold_df(df)
    df['salary_delta'] = df['salary_delta'] - 1000
    ax = df.boxplot(column='salary_delta', by="point", vert=False)
    ax.set_title('Distribution of Salary Delta per Point')
    ax.set_xlabel('Salary Delta')
    ax.set_ylabel('Point')

    fig = ax.figure
    #fig.set_size_inches(5,5)
    fig.tight_layout(pad=1)
    fig.suptitle('')
    fig.savefig('../images/boxplot_salary_delta_point')  
    
    with sns.axes_style('white'):
        plot = sns.jointplot("salary_delta", "point", df, kind='reg')
        plot.savefig(f"../images/pair_plot_salary_delta_point")

    corr_val = df.salary_delta.corr(df.point)
    print(f"The correlation between Salary Delta and Point is {corr_val:0.2f}")

def predict_goal(df, X, y):
    '''
    predict goal for 2018_2019 season base on the previous 3 years
    
    INPUT:
        df: DataFrame
        X: list of features
        y: target
    OUTPUT
        numpy.ndarray: prediction
    '''
    grouped = df.groupby('season')
    groups = ['2015_2016','2016_2017', '2017_2018']    
    train = pd.concat([grouped.get_group(name) for name in groups])
    test = grouped.get_group('2018_2019')

    X_train = train[X]
    y_train = train[y]
    model = LinearRegression()
    model.fit(X_train, y_train)

    X_test = test[X]
    y_test = test[y]
    y_hat = model.predict(X_test)

    print(mean_squared_error(y_test, y_hat))
    #TODO: should print based on condition Home or Away
    print(mean_squared_error(test.goal_a, test.xg_a))
    print(mean_squared_error(test.goal_b, test.xg_b))

    return y_hat.flatten()

def analyze_goal_prediction(df):
    '''
    compare error distribution between statsbomb and salary_delta prediction
    
    INPUT:
        df: DataFrame
        
    OUTPUT
        tuple(square error distribution of statsbomb, square error distribution of salary_delta)
    '''

    sr_xg_err = get_series_error(df.goal_a, df.xg_a, df.goal_b, df.xg_b)
    sr_pr_err = get_series_error(df.goal_a, df.pr_a, df.goal_b, df.pr_b)
    
    ax = sns.kdeplot(sr_xg_err, color='b', shade=True, legend=True)
    ax = sns.kdeplot(sr_pr_err, color='r', shade=True, legend=True)
    ax.legend(['StatsBomb', 'Salary Only'])
    ax.figure.suptitle("Error Distribution Comparison", fontsize = 24)
    ax.set_xlabel('Error')
    ax.set_ylabel('Error Density')
    ax.figure.savefig('../images/error_distribution_comparision.png')
    plt.cla()


    print(sr_xg_err.describe())
    print(sr_pr_err.describe())
    print(np.sqrt(sr_xg_err.mean()))
    print(np.sqrt(sr_pr_err.mean()))

    return (sr_xg_err, sr_pr_err)

def analyze_error_distribution(a, b):
    '''
    Ananlyze more about error distribution:    
    INPUT:
        a: series of statsbomn error
        b: series of salary delta error
        
    OUTPUT
    '''
    c = np.sqrt((a - b).abs())

    ax = c.plot.kde()
    ax.legend(['Difference Squrerooted'])
    ax.figure.suptitle("Difference Distribution", fontsize = 24)
    ax.set_xlabel('Error Difference')
    ax.set_ylabel('Probability Density')
    ax.figure.savefig('../images/error_difference_distribution.png')

    c = c.to_numpy()

    mu = c.mean()
    sigma = c.std()
    count = c.size

    ci_skew = stats.skewnorm.interval(0.95, stats.skew(c), loc=mu, scale=sigma)
    ci_norm = stats.norm.interval(0.95, loc=mu, scale=sigma)

    ci_95_high = mu + 1.96*sigma/math.sqrt(count)
    ci_95_low = mu - 1.96*sigma/math.sqrt(count)

    print((mu, sigma, count))
    print(ci_skew)
    print(ci_norm)
    print((ci_95_high, ci_95_low))

def get_series_error(a, a_hat, b, b_hat):
    
    sr_SE = ((a - b) - (a_hat - b_hat))**2
    
    return sr_SE
    
if __name__=='__main__':

    # #df = fixturedata.build_fixture_dataframe("2018")
    df = pd.read_pickle('../data/fixture.pkl')
    df = populate_column(df)

    

    # #First, teams performance for overall season based on salary.
    df_team = analyze_by_team(df)

    #Second, how the team salary affect the peformance in each match.
    analyze_salary_delta_with_goal_delta(df)
    analyze_salary_delta_with_point(df)
    
    #Goal Prediction Analyze
    groupd = df.groupby('season')
    df_2018 = groupd.get_group("2018_2019")
    pr_a = predict_goal(df, ['a_salary_delta'], 'goal_a')
    pr_b = predict_goal(df, ['b_salary_delta'], 'goal_b')
    df_2018['pr_a'] = pd.Series(pr_a, index=df_2018.index)
    df_2018['pr_b'] = pd.Series(pr_b, index=df_2018.index)
    a_err, b_err = analyze_goal_prediction(df_2018)

    #Do more analyze on the error
    analyze_error_distribution(a_err, b_err)

    # #for Debug
    # groupd = df.groupby('season')
    # df_2018 = groupd.get_group("2018_2019")
    # df_2017 = groupd.get_group("2017_2018")
    # folded = fold_df(df)