import pandas as pd
import numpy as np
import mplfinance as mpf
#plotly, echarts


ticker = 'AMZN'
pair = (1,197)
save_name = f'{ticker} MA2{pair}.csv'
#save_name = f'{ticker} US10y.csv'

df = pd.read_csv(save_name, parse_dates=['formatted_date'])


new_col = {'formatted_date': "Date"}

df.rename(columns=new_col, inplace=True)
df.set_index('Date', inplace=True)
df = df.loc['2013': ]


signal_buy = np.where(df['signal']==1, df['open'], np.nan)
signal_sell = np.where(df['signal']==0, df['open'], np.nan)


short = pair[0]
long = pair[1]

apds = [mpf.make_addplot(df[[f'ma_{short}',f'ma_{long}']])]

if not np.all(np.isnan(signal_buy)):
    apds.append(mpf.make_addplot(signal_buy,type='scatter',markersize=100,marker='^'))
    
if not np.all(np.isnan(signal_sell)):
    apds.append(mpf.make_addplot(signal_sell,type='scatter',markersize=100,marker='v'))
    

kwarg = {'type': 'line',
         'volume': False,
         'figscale': 2, 
         'figratio': (16, 9), 
         'style': 'yahoo', 
         'tight_layout': True, 
         #'mav': (155, 210), 
         'addplot': apds, 
         'title': save_name,
         'savefig': f'{save_name}_ta.png'         
    }

mpf.plot(df,**kwarg)


print("end of code")
