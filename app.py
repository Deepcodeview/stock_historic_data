from flask import Flask, render_template, request, redirect, session, url_for, jsonify
from data_to_db_live import live_click, updater
#from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine

app = Flask(__name__)
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///historic.db'
# app.config['SQLALCHEMY_BINDS'] = {
#      'hist_db' : 'sqlite:///historic_database.db',
#      'live_db': 'sqlite:///live_database.db'
# }

#db = SQLAlchemy(app)
engine = create_engine('sqlite:///historic.db')
conn = engine.connect()




if __name__ == "__main__":
   app.run(host='0.0.0.0', port=80, debug=True)

import sqlite3

###-------- for historic data ----------##
conn=sqlite3.connect('historic_database.db', check_same_thread=False)
curs=conn.cursor()

global numSamples
numSamples = 10

def getHistData (numSamples, table_name):
    curs.execute("SELECT * FROM {0} ORDER BY Date DESC LIMIT ".format(table_name) + str(10) )#str(numSamples))
    data = curs.fetchall()
    #conn.close()
    dates = []
    close = []
    # conn.commit()
    # conn.close()
    for row in reversed(data):
        dates.append(row[0])
        close.append(row[4])
    return dates, close

# def maxRowsTable():
# 	for row in conn.execute("select COUNT(*) from  BTC_GBP"):
# 		maxNumberRows=row[0]
# 	return maxNumberRows

# define and initialize global variables


#tables = ["BTC_GBP", "ETH_GBP", "BNB_GBP"]
tables = [] # list
          
def histroicDataControl():
    with open('currency_list/1.txt') as f:
        for line in f:
            tables.append(line.strip().replace('-', '_').replace('1', '_'))
        return tables
histroicDataControl()

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "GET":
        dates, close = getHistData(numSamples, table_name='BTC_GBP')
        return render_template(
            template_name_or_list='chart.html',
            data=close,
            labels=dates, 
            table_name='BTC_GBP',
            )
    elif request.method == "POST":
        table = request.form.get('cars')
        print(table, "in index")
        dates, close = getHistData(numSamples, table_name=table)
        return render_template(template_name_or_list='chart.html',
                        data=close,
                        labels=dates, 
                        table_name=table,)
            
conn_live=sqlite3.connect('live_database.db', check_same_thread=False)
curs_live=conn_live.cursor()

def getHistDataLive (table_nameLive):
    curs_live.execute("SELECT * FROM {0} ORDER BY Date DESC LIMIT ".format(table_nameLive) + str(10))
    data_live = curs_live.fetchall()
    dates__live = []
    close_live = []
    # conn_live.commit()
    # conn_live.close()
    for row in reversed(data_live):
        dates__live.append(row[0])
        close_live.append(row[4])
    return dates__live, close_live

##--- for live data ---------##
@app.route("/live", methods=["GET", "POST"])
def live():
    #curs.close()
    #updater()
    #sample = 2
    if request.method == "GET":
        dates_live, close_live = getHistDataLive(table_nameLive='BTC_GBP')
        #dates_live, close_live = 
        live_click(table = 'BTC_GBP', currency='BTC-GBP')
        #updater()
        return render_template(
                template_name_or_list='chart_live.html',
                                close_live= close_live,
                                dates_live= dates_live, 
                                table_live='BTC_GBP',)
    elif request.method =="POST":
            table_live = request.form.get('currency')
            currency = table_live.replace('_', '-').replace('_', '1')
            print(table_live, currency)
            #live_click(table = table_live, currency=currency)
            #updater()
            dates_live, close_live = getHistDataLive(table_nameLive=table_live)
            return render_template(template_name_or_list='chart_live.html',
                            close_live= close_live,
                            dates_live= dates_live, 
                            table_live= table_live,)     




# @app.route("/refresh")
# def refresh():
#     return redirect(url_for("live"))

from data_to_db_live import live_price_only
from flask import render_template, jsonify, request

@app.route("/onlylive", methods=["GET", "POST"])
def onlylive():
    if request.method == "GET":
        dates_live, close_live = live_price_only('BTC-GBP')
        return render_template(
            template_name_or_list='chart_only_live.html',
            close_live=close_live,
            dates_live=dates_live,
            table_live='BTC_GBP',
        )
    elif request.method == "POST":
        table_live = request.form.get('currency')
        
        # Check if 'currency' form field is not present, use a default value
        if table_live is None:
            table_live = 'BTC_GBP'
        else:
            table_live = table_live.replace('_', '-')
        
        dates_live, close_live = live_price_only(table_live)
        data = {'dates_live': dates_live, 'close_live': close_live}
        return jsonify(data), render_template('chart_only_live.html', close_live=close_live, dates_live=dates_live, table_live=table_live)