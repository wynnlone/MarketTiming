'''
evaluate performance based on position
'''

import numpy as np
import pandas as pd
import os

import time

def run_time(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"Execution time of '{func.__name__}': {end_time - start_time} seconds")
        return result
    return wrapper


def get_trade_date(df):
    
    buy = df['signal'].shift() == 1 
    sell = df['signal'].shift() == 0 

    ## assign trade date for each holding period
    df.loc[buy, 'trade_date'] = df['formatted_date']
    df.loc[sell, 'trade_date'] = df['formatted_date']
    df['trade_date'].ffill(inplace=True)    

    return df, buy, sell

#@run_time
def get_time_perform(df, initial_cash = 1_000_000, # $ amount
                slippage = 0.01, # $ amount
                c_fee = 1, # $ amount
                c_rate = 0.005, # 0.5% of total trade
                c_share = 0.005, # $ per share cost
                ):
    '''
    This function uses adjclose as buy and sell price and 
    assumes can trade the same moment the signla is generated.
    It runs faster by runing simulation in groups.    
    '''
    
    ## group each trade holding period
    df, buy, sell = get_trade_date(df)
    
    ## initial all cash postion before first buy signal    
    first_buy_signal = df[df['signal'] == 1].index.min()
    df.loc[:first_buy_signal, ['cash','total_value']] = initial_cash
    df.loc[:first_buy_signal, ['stock_num','stock_value']] = 0
    df['trans_exp'] = 0.0
    
    grouped = df.iloc[first_buy_signal+1:].groupby('trade_date', group_keys=False)
    
    for date, frame in grouped:
        
        if (frame["position"] == 1).all():
            
            ## buy stock, total = cash + stock
            start_cash = df.at[frame.index[0]-1,'cash']
            buy_price = df.at[frame.index[0]-1,'adjclose']
            
            theoretical_stock_num = (start_cash - c_fee)/ ((buy_price + slippage) * (1 + c_rate) + c_share)
            stock_num = np.floor(theoretical_stock_num / 100) * 100  #buy stock at multiple of 100 or
            #stock_num = theoretical_stock_num
            
            trans_exp = c_fee + stock_num * ((buy_price + slippage) * c_rate + c_share)
            
            df.loc[frame.index[0],'trans_exp'] = trans_exp
            df.loc[frame.index[0]:frame.index[-1],'cash'] = start_cash - trans_exp - stock_num * (buy_price + slippage)
            df.loc[frame.index[0]:frame.index[-1],'stock_num'] = stock_num
            df.loc[frame.index[0]:frame.index[-1],'stock_value'] = stock_num * frame['adjclose']
            df.loc[frame.index[0]:frame.index[-1],'total_value'] = df.loc[frame.index[0]:frame.index[-1],'stock_value'] + df.loc[frame.index[0]:frame.index[-1],'cash']

            
        elif (frame["position"] == 0).all():
            
            ## sell stock to go back to all cash position
            start_cash = df.at[frame.index[0]-1,'cash']
            sell_price = df.at[frame.index[0]-1,'adjclose']
            stock_num = df.at[frame.index[0]-1,'stock_num']
            trans_exp = c_fee + stock_num * ((sell_price - slippage) * c_rate + c_share)
            total_value = start_cash - trans_exp + stock_num * (sell_price - slippage)  
            
            df.loc[frame.index[0],'trans_exp'] = trans_exp
            df.loc[frame.index[0]:frame.index[-1],['total_value','cash']] = total_value 
            df.loc[frame.index[0]:frame.index[-1],['stock_num','stock_value']] = 0 
               
        else:
            print("position calculation error, function terminated")
            return None
    
        
    df['equity_change'] = df['total_value'].pct_change()
    df['equity_curve'] = (1 + df['equity_change']).cumprod()
    df['equity_curve_base'] = (df['adjclose'] / df['adjclose'].shift()).cumprod()
    
    df.at[df.index[0],'equity_change'] = 0
    df.loc[df.index[0],['equity_curve','equity_curve_base']]= 1 

    return df

#@run_time
def get_time_performance(df, initial_cash = 1_000_000, # $ amount
                slippage = 0.01, # $ amount
                c_fee = 1, # $ amount
                c_rate = 0.005, # 0.5% of total trade
                c_share = 0.005, # $ per share cost
                ):
    
    '''
    This function assumes buy and sell at the next open price.
    Dividends are put into cash account.
    It runs simulation row by row and thus slower.
    '''
     
    ## initial all cash postion before first buy signal    
    first_buy_signal = df[df['signal'] == 1].index.min()
    df.loc[:first_buy_signal, ['cash','total_value']] = initial_cash
    df.loc[:first_buy_signal, ['stock_num','stock_value','div_pay']] = 0
    df['trans_exp'] = 0.0
    
    
    for ind in df.index[first_buy_signal+1:]:       
            
        if df.at[ind-1,'position'] == 0 and df.at[ind,'position'] == 1:
            ## buy stock
            start_cash = df.at[ind-1,'cash']
            buy_price = df.at[ind,'open']
            theoretical_stock_num = (start_cash - c_fee)/ ((buy_price + slippage) * (1 + c_rate) + c_share)
            stock_num = np.floor(theoretical_stock_num / 100) * 100 
            trans_exp = c_fee + stock_num * ((buy_price + slippage) * c_rate + c_share)
            
            df.at[ind,'trans_exp'] = trans_exp
            df.at[ind,'cash'] = start_cash - trans_exp - stock_num * (buy_price + slippage) 
            df.at[ind,'stock_num'] = stock_num
            df.at[ind,'stock_value'] = stock_num * df.at[ind,'close']
            df.at[ind,'total_value'] = df.at[ind,'stock_value'] + df.at[ind,'cash']
            df.at[ind,'div_pay'] = 0           

        
        elif df.at[ind-1,'position'] == 1 and df.at[ind,'position'] == 0:
            ## sell stock to go back to all cash position
            start_cash = df.at[ind-1,'cash']
            sell_price = df.at[ind,'open']
            stock_num = df.at[ind-1,'stock_num']
            div_pay = df.at[ind,'dividends']*stock_num
            trans_exp = c_fee + stock_num * ((sell_price - slippage) * c_rate + c_share) 
            total_value = start_cash + div_pay - trans_exp + stock_num * (sell_price - slippage)
            
            df.at[ind,'trans_exp'] = trans_exp
            df.loc[ind,['total_value','cash']] = total_value 
            df.loc[ind,['stock_num','stock_value']] = 0 
            df.at[ind,'div_pay'] = div_pay
        
        
        else:
            ## no transaction occur
            stock_num = df.at[ind-1,'stock_num']
            div_pay = df.at[ind,'dividends']*stock_num
            df.at[ind, 'cash'] = df.at[ind-1, 'cash'] + div_pay
            df.at[ind, 'stock_num'] = stock_num
            df.at[ind, 'stock_value'] = stock_num * df.at[ind, 'close']
            df.at[ind, 'total_value'] = df.at[ind, 'cash'] + df.at[ind, 'stock_value']
            df.at[ind,'div_pay'] = div_pay

    df['equity_change'] = df['total_value'].pct_change()   
    df['equity_curve'] = (1 + df['equity_change']).cumprod()
    df['equity_curve_base'] = (df['adjclose'] / df['adjclose'].shift()).cumprod()
    
    df.at[df.index[0],'equity_change'] = 0
    df.loc[df.index[0],['equity_curve','equity_curve_base']]= 1  
    
    return df




if __name__ == "__main__":

    print(os.getcwd())
    ticker = 'AMZN'
    pair = (195,225)

    df_position = pd.read_csv(f'{ticker} MA2{pair} position.csv', parse_dates=['formatted_date'])
    df_time_perform = get_time_perform(df_position)
    df_time_perform.to_csv(f'{ticker} MA2{pair} perform.csv', index=False)
          
    
    
    print("\nend of code")
