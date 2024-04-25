#pip install yahoofinancials
#pip install yfinance

from tqdm import tqdm
import re
import pandas as pd

list_SP500 = pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')[0]['Symbol'].to_list()
list_Nasdaq100 = pd.read_html('https://en.wikipedia.org/wiki/Nasdaq-100#External_links')[4]["Ticker"].to_list()

from yahoofinancials import YahooFinancials

etf = ['SPY','SSO','UPRO','SH','SDS','SPXU','SPXS',
           'DIA','DDM','UDOW','DOG','DXD','SDOW',
           'QQQ','QLD','TQQQ','PSQ','QID','SQQQ',
           'IWM','UWM','TNA','RWM','TWM','TZA']

Diff = ['AZN','MELI', 'ASML', 'DDOG', 'CCEP', 'WDAY', 'MDB', 'SIRI',
           'ZS', 'GFS', 'MRVL', 'TTD', 'TEAM', 'CRWD', 'DASH', 'PDD']


index = ['^DJI','^GSPC','^IXIC']




tickers = 

pbar = tqdm(tickers, unit="ticker")

for ticker in pbar:
    ticker = re.sub(r'\.', '-', ticker)
    df_s = pd.DataFrame()
    
    try:   
        ## download data
        yahoo_financials = YahooFinancials(ticker)
        data = yahoo_financials.get_historical_price_data(start_date='2004-01-01', 
                                                          end_date='2024-04-01',
                                                          time_interval='daily')
        ## get price data
        df_s = pd.DataFrame(data[ticker]['prices'])
    
        ## get dividends data then merger with price data
        df_d = pd.DataFrame.from_dict(data[ticker]['eventsData']['dividends'], orient='index')
        df_d.rename(columns={'amount': 'dividends'}, inplace=True)
        df = pd.merge(df_s, df_d[['dividends','date']], on='date', how='left').fillna(0)
        
    except Exception as e:
        #normally error message either no price data or no dividend data       
        print(f"\nError: {ticker}", e)
        if df_s.empty:
            print(f"No price data {ticker}")
            continue
        else:
            print(f"No dividend data {ticker}")
            df = df_s
            df['dividends'] = 0 

    df['ticker'] = ticker
    df.to_csv(f'yf/SP500/{ticker}.csv', index = False)    
    pbar.set_description(f"Processed  {ticker}\t")
    
    
print("\nend of code") 