import os
import sys

file_path = os.path.abspath(os.path.dirname(__file__))
sys.path.append(file_path)

import numpy as np
import pandas as pd
import itertools

from tqdm import tqdm
import matplotlib.pyplot as plt

from algo_time_signal import *
from algo_time_perform import *


def timing_stra(ticker, pair = (175,225), start_date = '2013-01-01', end_date='2023-01-01', 
                     initial_cash = 1_000_000,
                     slippage = 0.01, # $ amount
                     c_fee = 1, # $ amount
                     c_rate = 0.005, # 0.5% of total trade
                     c_share = 0.005, # $ per share cost
                     ):
    
    df = get_data(ticker, start_date = start_date, end_date = end_date)
    df_signal = get_ma2_signal(df, pair=pair)
    #df_signal = get_us10y_signal(df, window=10, freq='W')
    df_position = get_position(df_signal)
    df_time_perform = get_time_perform(df_position, initial_cash = initial_cash, # $ amount
                            slippage = slippage, # $ amount
                            c_fee = c_fee, # $ amount
                            c_rate = c_rate, # % of total trade
                            c_share = c_share, # $ per share cost
                            )
    
    return df_time_perform

def get_max_pair(ticker, start = 5, stop = 251, step = 5):
    
    pairs = itertools.combinations(range(start, stop, step), 2)
    
    dict_returns = dict()
    
    for pair in tqdm(pairs, desc="Processing", unit="pairs"):
        
        df = timing_stra(ticker, pair=pair)
        dict_returns[pair] = df['equity_curve'].iloc[-1]
        
    sorted_items = sorted(dict_returns.items(), key=lambda x: x[1], reverse=True)

    return sorted_items[0][0], sorted_items

def get_max_ma(ticker, start = 2, stop = 251, step = 5):
    
    pairs = itertools.product([1], range(start, stop, step))
    
    dict_returns = dict()
    
    for pair in tqdm(pairs, desc="Processing", unit="pairs"):
        
        df = timing_stra(ticker, pair=pair)
        dict_returns[pair] = df['equity_curve'].iloc[-1]
        
    sorted_items = sorted(dict_returns.items(), key=lambda x: x[1], reverse=True)

    return sorted_items[0][0], sorted_items



if __name__ == '__main__':
    
    print(os.getcwd()) 
    
    ticker = 'AMZN'
    pair = (195,225)
    start_date = '2013-01-01' 
    end_date='2024-01-01' 
    
    initial_cash = 1_000_000
    slippage = 0.01 # $ amount
    c_fee = 1 # $ per trade
    c_rate = 0.005 # 0.5% of total trade
    c_share = 0.005 # $ per share
    
    save_name = f'{ticker} MA2{pair}'
    #save_name = f'{ticker} US10y.csv'
    
    # get pair of ma to max 
    #pair, all_pairs = get_max_ma(ticker)
        
    # run strategy
    df_timing = timing_stra(ticker, pair = pair, 
                     start_date = start_date, 
                     end_date=end_date,
                     initial_cash = initial_cash,
                     slippage = slippage,
                     c_fee = c_fee,
                     c_rate = c_rate,
                     c_share = c_share,
                     )
    
    df_timing.to_csv(save_name+'.csv', index=False) 
    
    
    # Plot performance
    
    df_plot = df_timing[['formatted_date','equity_curve', 'equity_curve_base','mkt_curve']]
    df_plot.set_index('formatted_date', inplace=True)
    #df_plot.plot(xlabel='' )
    
    fig = plt.figure(figsize=(16, 9))
    
    plt.plot(df_plot['equity_curve_base'],label=ticker)
    plt.plot(df_plot['equity_curve'],label=f'MA2{pair}')
    plt.plot(df_plot['mkt_curve'],label='Index')
    plt.legend(loc='best')
    
    plt.title(save_name, fontsize=20)
    plt.savefig(save_name+'.png')
    
    
    print("\nend of code")
