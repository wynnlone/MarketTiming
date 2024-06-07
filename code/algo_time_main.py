import os
import sys

file_path = os.path.abspath(os.path.dirname(__file__))
sys.path.append(file_path)

import numpy as np
import pandas as pd
import itertools

from tqdm import tqdm
import matplotlib.pyplot as plt
import seaborn as sns

from algo_time_signal import *
from algo_time_perform import *


def timing_stra(ticker, pair = (175,225), start_date = '2013-01-01', end_date='2024-01-01', 
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

def get_max_pair(ticker, start = 5, stop = 251, step = 5, 
                 start_date = '2013-01-01', end_date='2024-01-01'):
    
    pairs = itertools.combinations(range(start, stop, step), 2)
    
    dict_returns = dict()
    
    for pair in tqdm(pairs, desc="Processing", unit="pairs"):
        
        df = timing_stra(ticker, pair=pair)
        dict_returns[pair] = df['equity_curve'].iloc[-1]
        
    sorted_items = sorted(dict_returns.items(), key=lambda x: x[1], reverse=True)

    return sorted_items[0][0], sorted_items


def get_max_ma1(ticker, start = 2, stop = 251, step = 1,
                start_date = '2013-01-01', end_date='2024-01-01'):
    
    pairs = itertools.product([1], range(start, stop, step))
    
    dict_returns = dict()
    
    for pair in tqdm(pairs, desc="Processing", unit="pairs"):
        
        df = timing_stra(ticker, pair=pair)
        dict_returns[pair] = df['equity_curve'].iloc[-1]
        
    sorted_items = sorted(dict_returns.items(), key=lambda x: x[1], reverse=True)

    return sorted_items[0][0], sorted_items


def get_max_ma2(ticker, start = 3, stop = 251, step = 1, 
                start_date = '2013-01-01', end_date='2024-01-01'):
    
    pairs = itertools.product([2], range(start, stop, step))
    
    dict_returns = dict()
    
    for pair in tqdm(pairs, desc="Processing", unit="pairs"):
        
        df = timing_stra(ticker, pair=pair)
        dict_returns[pair] = df['equity_curve'].iloc[-1]
        
    sorted_items = sorted(dict_returns.items(), key=lambda x: x[1], reverse=True)

    return sorted_items[0][0], sorted_items


def time_plot(df_timing):
    
    df_plot = df_timing[['formatted_date','equity_curve', 'equity_curve_base','mkt_curve']]
    df_plot.set_index('formatted_date', inplace=True)
    #df_plot.plot(xlabel='' )
    
    fig = plt.figure(figsize=(16, 9))
    
    plt.plot(df_plot['equity_curve_base'],label=ticker)
    plt.plot(df_plot['equity_curve'],label=f'MA2{pair}')
    plt.plot(df_plot['mkt_curve'],label='Index')
    plt.legend(loc='best')
    
    plt.title(f'{ticker} MA2{pair}', fontsize=20)
    plt.savefig(f'{ticker} MA2{pair}.png')
    
    return None


def pair_plot(all_pairs:list, base:tuple=None, top_num:int=20):  
    all_pairs = all_pairs.copy()
    total_pair_num = len(all_pairs)
    if_base = False
    
    if type(base) is tuple:
        if_base = True
        all_pairs.append(base)
        base_value = base[1]
    
    all_pairs = sorted(all_pairs, key=lambda x: x[1], reverse=True)
    top_pairs = all_pairs[:top_num]
    
    base_index = next((i for i, tup in enumerate(all_pairs) if isinstance(tup[0], str)), None)
    
    x_values = [f'{tup[0]}' for tup in top_pairs]
    y_values = [tup[1] for tup in top_pairs]
    pair_mean = np.mean(y_values)
    pair_std = np.std(y_values)
    
    colors = ['#069AF3' if i != base_index else 'orange' for i in range(len(x_values))]

    # Plot top 20
    plt.figure(figsize=(10, 10))
    plt.barh(x_values, y_values, color=colors)
    plt.xlabel('Terminal value')
    plt.ylabel('pairs')
    plt.title(f'Terminal value of {ticker} MA2 pairs (Top {top_num})', fontsize=20)
    plt.gca().invert_yaxis()  # Invert y-axis to have the highest value at the top
    plt.savefig(f'{ticker} MA2 pairs terminal value (Top {top_num})')
    
    # Plot pair_hist
    pair_hist = [pair[1] for pair in all_pairs]
    num_bins = 10
    bins = np.histogram_bin_edges(pair_hist, bins=num_bins, range=(min(pair_hist),max(pair_hist)*(1+1/100)))
    
    plt.figure(figsize=(10, 5))
    sns.histplot(pair_hist, kde=True, bins=num_bins, color='#069AF3')
   
    if if_base:
        bin_index = np.searchsorted(bins, base_value,side='left')
        plt.gca().patches[max(0,bin_index-1)].set_facecolor('orange')
 
    plt.suptitle(f'{ticker} MA2 pairs terminal value dist.',fontsize = 20)
    plt.title(f'n = {total_pair_num}, mean = {pair_mean:.4}, std = {pair_std:.2}', fontsize=12)
    plt.savefig(f'{ticker} MA2 pairs terminal value dist.png')
    
    return None
    


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
    
    
    # get pair of ma to max 
    all_pairs = []
    pair, all_pairs = get_max_pair(ticker,  start = 5, stop = 251, step = 5,
                                    start_date=start_date, end_date=end_date)
    
    # pair1, all_pairs1 = get_max_ma1(ticker, start = 2, stop = 251, step = 1,
    #                                 start_date=start_date, end_date=end_date)
    # all_pairs.extend(all_pairs1)
    
    # pair2, all_pairs2 = get_max_ma2(ticker, start = 3, stop = 251, step = 1,
    #                                 start_date=start_date, end_date=end_date)
    # all_pairs.extend(all_pairs2) 
    
    all_pairs = sorted(all_pairs, key=lambda x: x[1], reverse=True)
    
    pair = all_pairs[0][0]
    
    all_pairs_backup = all_pairs.copy()    
    

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

    
    save_name = f'{ticker} MA2{pair}'
    #save_name = f'{ticker} US10y.csv'
    
    df_timing.to_csv(save_name+'.csv', index=False) 
    return_base=df_timing['equity_curve_base'].iloc[-1]
    base=('Base',return_base)
    
    # Plot performance    
    time_plot(df_timing)
    
    # Plot pairs    
    pair_plot(all_pairs, base=base)
    
    print("\nend of code")
