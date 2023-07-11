import yfinance as yf
import pandas as pd
from datetime import date
import os
import sqlite3

####----------initiate db --------------------------##

con = sqlite3.connect("historic_database.db")
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
    new1.rename({'Adj Close':'Adj_Close'}, axis=1, inplace=True)
    new1.to_sql(table_name, con, if_exists='append', index=False)

def insertToDbUpdate_new(table_name, currency_name):
    ## get data from databse and get date from database
    ## Check data is there or not in table
    ## data = cur.fetchall()
    ## if not data:
    old_data = cur.execute('SELECT * FROM {0}'.format(table_name)) # table name = BTC_GBP
    data = cur.fetchone()
    if data:
        start_date = data[0][0:10]
        #stock = yf.download(tickers=currency_name, start=start_date, end="2023-06-12") # yf.download(tickers=currency_name, start=start_date)
        stock = yf.download(tickers=currency_name, start=start_date)
        stock.reset_index(inplace=True)
        stock.sort_index(ascending=False,inplace=True, ignore_index=True)
        stock.to_sql(name= table_name, con= con, if_exists='append', index=False)
        #old_data_df = pd.DataFrame(old_data, columns=['Date', 'Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume'])
        #concat_data = pd.concat([stock, old_data_df], axis=0)
        #concat_data.to_sql(name= table_name, con= con, if_exists='replace', index=False, chunksize= 100)
        # add new data to old data
        #pass
    if not data:
        stock = yf.download(tickers=currency_name, period="max") # download all data using stock = yf.download(tickers=currency_name, period="max") and add to sql
        stock.reset_index(inplace=True)
        stock.sort_index(ascending=False,inplace=True, ignore_index=True)
        stock.to_sql(name= table_name, con=con, if_exists='replace', index=False, chunksize= 100)


def historicToDb(table_name, currency):
    stock = yf.download(tickers=currency, period="max")
    stock = stock.sort_index(ascending = False)
    stock.to_sql(name=table_name, con=con, if_exists='replace', index=False)

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
                insertToDbUpdate_new(table_name= table, currency_name=currency)
                count += 1
                print(currency, count)
        return False

updater()

