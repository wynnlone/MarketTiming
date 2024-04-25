'''
generate signal based on stock data
'''


import numpy as np
import pandas as pd
import os


def get_data(ticker: str, index_name:str = '^GSPC', rf_name:str = 'DGS1',
             start_date='2013-01-01', end_date='2023-01-01'):
    '''  

    Parameters
    ----------
    ticker : str
        security to be traded.
    start_date : str, optional
        start date. The default is '2013-01-01'.
    end_date : TYPE, optional
        end date. The default is '2023-01-01'.

    Returns
    -------
    df : DataFrame
        Security price info.

    '''
    
    ## load data
    df = pd.read_csv(f'../data/yf/selection/{ticker}.csv', parse_dates=['formatted_date'])
    df.drop_duplicates(subset=['formatted_date'], inplace=True)
    
    df_index = pd.read_csv(f'../data/yf/index/{index_name}.csv', parse_dates=['formatted_date'])
    df_rf = pd.read_csv(f'../data/FRED/{rf_name}.csv', parse_dates=['DATE'])
        
    ## handle stock missing value
    fill_list = ['high','low','open','close']
    df[fill_list] = df[fill_list].replace(0, np.nan)
    df.replace('None', np.nan, inplace=True)
    df.sort_values(by=['formatted_date'], inplace=True)
    
    ## merge index and stock
    df_index.drop_duplicates(subset=['formatted_date'], inplace=True)
    df_index.rename(columns = {'adjclose':'index_level'},inplace=True)
    df_index.sort_values(by=['formatted_date'], inplace=True)
    df = pd.merge(df_index[['formatted_date','index_level']], df, on='formatted_date', how='left', indicator=True)
    
    ## remove pre ipo data
    df['ticker'] = df['ticker'].ffill()
    df = df[df['ticker'].notnull()]
    
    # handling missing data
    df['trading'] = np.where(df['_merge'] == 'both', 1, 0)
    df['adjclose'].ffill(inplace=True)
    df['close'].ffill(inplace=True)
    
    fill_dict = {c: df['close'] for c in fill_list}
    df.fillna(value=fill_dict, inplace=True)
    
    fill_0_columns = ['volume']
    df.fillna(value={c: 0 for c in fill_0_columns}, inplace=True)
    
    #df.ffill(inplace=True)
        
    df.drop(columns=['_merge'], inplace=True)
    df.reset_index(drop=True, inplace=True)
    
    ## append rf
    df_rf.rename(columns = {'DATE':'formatted_date', f'{rf_name}':'rf_rate'}, inplace=True)
    df_rf['rf_rate'] = df_rf['rf_rate'].replace('.', np.nan)
    df_rf['rf_rate'] = df_rf['rf_rate'].ffill()
    df_rf['rf_rate'] = df_rf['rf_rate'].astype(float)  
    df = pd.merge(df, df_rf[['formatted_date','rf_rate']], on='formatted_date', how='left')
    
    ## truncate date
    df = df.loc[df['formatted_date'] > pd.to_datetime(start_date)]
    df = df.loc[df['formatted_date'] < pd.to_datetime(end_date)]
    df.reset_index(inplace=True, drop=True)
    
    ## calculate stats
    df['rf_return'] = df['rf_rate'].apply(lambda x: (1+x/100) ** (1/252)-1)
    df['mkt_return'] = df['index_level']/df['index_level'].shift() - 1
    #df.loc[0,'mkt_return'] = 0
    df['mkt_curve'] = df['index_level']/df['index_level'].iloc[0]  
    
    df['h2l_range'] =  df['high'] - df['low']
    df['o2c_range'] = df['close'] - df['open']
    df['range'] = df['high'] / df['low'] - 1
    df['o2c_return'] = df['close'] / df['open'] - 1
    df['c2c_return'] = (df['close'] + df['dividends'])/ df['close'].shift() - 1  

    return df



def get_ma2_signal(df, pair=(170, 195)):
    '''
    A classic double moving average stratege.
    A golden cross is when MA short cross MA long from belwo to above, long signal (1).
    A dead cross is when MA short cross  MA long from above to below, short signal (0).

    Parameters
    ----------
    df : Dataframe
        security price info
        
    params : tuple of int, optional
        MA short and long. The default is (175, 225).

    Returns
    -------
    df : Dataframe
        date and signal generated with 1, 0 or nan.

    '''
    short = pair[0]
    long = pair[1]
    
    df_signal = df.copy()

    ma_short = pair[0]
    ma_long = pair[1]
    
    ## calculate MA
    df_signal[f'ma_{short}'] = df_signal['close'].rolling(ma_short, min_periods=1).mean() 
    df_signal[f'ma_{long}'] = df_signal['close'].rolling(ma_long, min_periods=1).mean()
    
    ## generate buy signal
    condition1 = df_signal[f'ma_{short}'] > df_signal[f'ma_{long}']
    condition2 = df_signal[f'ma_{short}'].shift(1) <= df_signal[f'ma_{long}'].shift(1)
    df_signal.loc[condition1 & condition2, 'signal'] = 1
    
    ## generate sell signal
    condition1 = df_signal[f'ma_{short}'] < df_signal[f'ma_{long}']
    condition2 = df_signal[f'ma_{short}'].shift(1) >= df_signal[f'ma_{long}'].shift(1)
    df_signal.loc[condition1 & condition2, 'signal'] = 0
    
    # include the following if long first (comment out if until signal is generated)
    
    first_signal_index = df_signal['signal'].first_valid_index()
    if df_signal.loc[first_signal_index, 'signal'] == 1:
        df_signal.loc[first_signal_index, 'signal'] = np.nan
    df_signal.loc[0, 'signal'] = 1
    

    return df_signal

def get_us10y_signal(df, window=10, freq='W'):
    '''
    Assume an inverse correlation between the 10 year yield and stock return due to money flow.
    when yield < MA(yield), long (1)
    when yield > MA(yield), short (0)

    Parameters
    ----------
    df : Dataframe
        Prepared security data.
    window : int, optional
        window length i.e., number of data points, used to calculate moving average. The default is 10.
    freq : str, optional
        resample parameter for decision frequency, D, W, M, Q, Y, etc. The default is 'W'.

    Returns
    -------
    df: Dataframe
        date and signal generated with 1, 0 or nan

    '''
    # prep yeld data
    df_y = pd.read_csv('../data/FRED/DGS10.csv')    
    df_y['formatted_date'] = pd.to_datetime(df_y['DATE'])
    df_y.drop(columns=['DATE'], inplace=True)
    
    df_y['DGS10'] = df_y['DGS10'].replace('.', np.nan)
    df_y['DGS10'] = df_y['DGS10'].ffill()
    df_y['DGS10'] = df_y['DGS10'].astype(float)  
    
    df_signal = pd.merge(df, df_y, on="formatted_date", how="left")
    
    # set window to calculate MA
    df_signal["DGS10_MA"] = df_signal["DGS10"].rolling(window).mean()
    df_signal["period_last_date"] = df_signal["formatted_date"]
    df_signal.set_index(keys="formatted_date", inplace=True)
    
    # set decision frequency
    df_period = df_signal.resample(rule=freq).agg({"DGS10": "last","DGS10_MA": "last","period_last_date": "last"})
    df_period["DGS10_diff"] = df_period["DGS10"] - df_period["DGS10_MA"]
    
    # generate trading signal
    df_period.loc[(df_period["DGS10_diff"] < 0) & (df_period["DGS10_diff"].shift(1) > 0), "signal"] = 1  
    df_period.loc[(df_period["DGS10_diff"] > 0) & (df_period["DGS10_diff"].shift(1) < 0), "signal"] = 0  
    
    # merge period signals into output
    df_signal.drop(columns=["period_last_date"], inplace=True)
    df_signal.reset_index(inplace=True)
    df_signal = pd.merge(df_signal, df_period[["period_last_date", "signal","DGS10_diff"]],
                         left_on="formatted_date", right_on="period_last_date", how="left")

    # drop no longer needed columns
    df_signal.drop(columns=['DGS10', 'DGS10_MA', "DGS10_diff", "period_last_date"], inplace=True)
    
    # include the following if long first (comment out if until signal is generated)
    '''
    first_signal_index = df_signal['signal'].first_valid_index()
    if df_signal.loc[first_signal_index, 'signal'] == 1:
        df_signal.loc[first_signal_index, 'signal'] = np.nan
    df_signal.loc[0, 'signal'] = 1
    '''
    return df_signal


def get_position(df):
    
    ## buy or sell after the signal is generated
    df.loc[(df['signal'].shift()==1), 'position'] = 1
    df.loc[(df['signal'].shift()==0), 'position'] = 0
    df['position'].ffill(inplace=True)
    df['position'].fillna(0, inplace=True)
    
    return df    
    

if __name__ == '__main__':
    
    print(os.getcwd())
    
    ticker = 'AMZN'
    start_date='2013-01-01'
    end_date='2023-01-01'
    pair = (195,225)

    df_data = get_data(ticker, start_date=start_date, end_date=end_date)
    df_signal = get_ma2_signal(df_data, pair=pair)
    #df_signal.to_csv(f'{ticker} MA2 {pair} signal.csv', index=False)
    
    #df_signal = get_us10y_signal(df, window=10, freq='W')
    #df_signal.to_csv(f'{ticker} US10y signal.csv', index=False)
    
    #df_signal = pd.read_csv(f'{ticker} MA2 {pair} signal.csv', parse_dates=['formatted_date'])
    df_position = get_position(df_signal)
    df_position.to_csv(f'{ticker} MA2{pair} position.csv', index=False)
    
    
    print("\nend of code")