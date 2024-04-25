import pandas as pd
import os
import re
from tqdm import tqdm


df_SP500 = pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')[0]
df_N100 = pd.read_html('https://en.wikipedia.org/wiki/Nasdaq-100#External_links')[4]

df_500 = df_SP500[['Symbol','GICS Sector']]
df_500 = df_500.rename(columns={'Symbol':'ticker', 'GICS Sector':'sector'})

df_100 = df_N100[['Ticker','GICS Sector']]
df_100 = df_100.rename(columns={'Ticker':'ticker', 'GICS Sector':'sector'})

df = pd.concat([df_500, df_100], ignore_index=True)
df = df.drop_duplicates()
df = df.sort_values(by='ticker')


# new_df = pd.DataFrame([{'ticker': 'VFC', 'sector': 'Consumer Discretionary'},
#                         {'ticker': 'XRAY', 'sector': 'Health Care'}])

# df = pd.concat([df, new_df], ignore_index=True)


folder_path = 'yf' # Replace to the folder containing .csv fata files

file_names = os.listdir(folder_path)

pbar = tqdm(file_names, unit="ticker")
#pbar = tqdm(['VFC.csv','XRAY.csv'], unit="ticker")

for file_name in pbar:
    
    if file_name.endswith('.csv'):
        
        file_path = os.path.join(folder_path, file_name)
        df_file = pd.read_csv(file_path)
        
        ticker = file_name[:-4]
        ticker = re.sub('-', '.', ticker)
        sector_value = df.loc[df['ticker'] == ticker, 'sector']
        
        if len(sector_value) == 0:
            df_file['sector'] = None
            print(f'Cannot find sector value for {ticker}.')
        else:
            df_file['sector'] = sector_value.values[0]

        df_file.to_csv(file_path, index=False)
        pbar.set_description(f"Processed  {ticker}\t")


