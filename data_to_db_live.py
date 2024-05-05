import yfinance as yf
import pandas as pd
#from datetime import date
import datetime
import os
import sqlite3

####----------initiate db --------------------------##

con = sqlite3.connect("live_database.db", check_same_thread=False)
cur = con.cursor()

##-----------------Insert to DB ---------------------##
def insertToDbUpdate(table_name, currency_name):
    cur.execute('SELECT * FROM {0}'.format(table_name))
    data = cur.fetchall()
    df = pd.DataFrame(data)
    #df['Date'] = pd.to_datetime(df['Date'], format='%Y-%m-%d %H:%M:%S.%f')
    today = date.today()
    stock = yf.download(tickers=currency_name, period="max")        #,start=df["Date"][0], end=today)
    stock = stock.reset_index()
    new1 = pd.concat([df, stock], axis=0)
    new1.drop_duplicates(subset=['Date'], inplace=True) # Important
    new1.sort_index(ascending=False, inplace=True, ignore_index=True)
    new1.sort_values(by=['Date'], ascending=False, inplace=True) # Important
    new1.to_sql(table_name, con, if_exists='append', index=False)

def historicToDb(table_name, currency):
    stock = yf.download(tickers=currency, period="max")
    stock = stock.sort_index(ascending = False)
    stock.to_sql(table_name, con, if_exists='replace', index=False)

list_of_currency = []
count = 0
def updater():
    while True:
        with open('currency_list/1.txt') as f:
            for line in f:
                global count
                table = line.strip().replace('-', '_').replace('1', '_')
                currency = line.strip()
                #list_of_currency.append(line.strip())
                insertToDbUpdate(table_name= table, currency_name=currency)
                count += 1
                print(currency, count)
        return False

def live_price(table_name, currency_name): #(table_name, currency_name):
    x = yf.Ticker(currency_name).history() #currency_name) # ('BTC-GBP').history()
    #cur.execute('SELECT * FROM {0}'.format(table_name))
    #stock = x.sort_index(ascending = False)
    x.reset_index(inplace=True)
    x['Date'] = datetime.datetime.now()
    x.rename({'Stock Splits':'Stock_Splits'}, axis=1, inplace=True)
    #x['Stock_Splits'] = x['Stock Splits']
    #print(x.iloc[-1])
    y = x[:: -1]
    #print( x.iloc[-1])
    #print(y)
    y.to_sql(table_name, con, if_exists='append', index=False, chunksize=1)


# while True:
#     live_price('BTC_GBP', 'BTC-GBP')

def updater():
    while True:
        with open('currency_list/1.txt') as f:
            for line in f:
                global count
                table = line.strip().replace('-', '_').replace('1', '_')
                currency = line.strip()
                #list_of_currency.append(line.strip())
                live_price(table_name= table, currency_name=currency)
                count += 1
                #print(currency, count)

#updater()

def live_click(table, currency):
    return live_price(table_name= table, currency_name=currency)


# def live_price_only( currency):
#     x = yf.Ticker(currency).history() #currency_name) # ('BTC-GBP').history()
#     #cur.execute('SELECT * FROM {0}'.format(table_name))
#     #stock = x.sort_index(ascending = False)
#     x.reset_index(inplace=True)
#     x['Date'] = datetime.datetime.now()
#     x.rename({'Stock Splits':'Stock_Splits'}, axis=1, inplace=True)
#     #x['Stock_Splits'] = x['Stock Splits']
#     #print(x.iloc[-1])
#     # y = x[:: -1]#x.iloc[-1]
#     y = x.iloc[-1]
#     print( y.Date)
#     print( y.Close)
#     return y.Date, y.Close

#live_price_only('BTC-GBP')


def live_price_only(currency):
    x = yf.Ticker(currency).history()

    # Check if the DataFrame is empty
    if x.empty:
        print("Error: DataFrame is empty.")
        return None, None

    x.reset_index(inplace=True)
    x['Date'] = datetime.datetime.now()
    x.rename({'Stock Splits': 'Stock_Splits'}, axis=1, inplace=True)

    # Check if the DataFrame has 'Date' and 'Close' columns
    if 'Date' not in x.columns or 'Close' not in x.columns:
        print("Error: DataFrame is missing 'Date' or 'Close' columns.")
        return None, None

    # Obtain the last row as a Pandas Series
    y = x.iloc[-1]

    # Access 'Date' and 'Close' using dictionary-style indexing
    date_value = y['Date']
    close_value = y['Close']

    print(date_value)
    print(close_value)

    return date_value, close_value


    