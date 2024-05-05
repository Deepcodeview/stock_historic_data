import datetime
import os
import sqlite3
from flask import Flask, render_template, request, jsonify
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from sqlalchemy import create_engine

app = Flask(__name__)



##-------- for historic data ----------##
conn=sqlite3.connect('historic_database.db', check_same_thread=False)
curs=conn.cursor()

def get_hist_data(num_samples, table_name):
    curs.execute("SELECT * FROM {0} ORDER BY Date DESC LIMIT ".format(table_name) + str(10))
    data = curs.fetchall()
    dates = []
    close = []
    for row in reversed(data):
        dates.append(row[0])
        close.append(row[4])
    return dates, close

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "GET":
        dates, close = get_hist_data(num_samples=10, table_name='BTC_GBP')
        return render_template('chart.html', data=close, labels=dates, table_name='BTC_GBP')
    elif request.method == "POST":
        table = request.form.get('cars')
        dates, close = get_hist_data(num_samples=10, table_name=table)
        return render_template('chart.html', data=close, labels=dates, table_name=table)
    








############################# Live ##########################
conn_live=sqlite3.connect('live_database.db', check_same_thread=False)
curs_live=conn_live.cursor()
## Engine to insert to SQL
engine = create_engine('sqlite:///live_database.db')

def get_hist_data_live(table_name):
    print(table_name)
    curs_live.execute("SELECT * FROM {0} ORDER BY Date DESC LIMIT ".format(table_name) + str(10))
    data_live = curs_live.fetchall()
    dates_live = []
    close_live = []
    for row in reversed(data_live):
        dates_live.append(row[0])
        close_live.append(row[4])
    return dates_live, close_live

def insert_to_db_update(table_name, currency_name):
    curs_live.execute('SELECT * FROM {0}'.format(table_name))
    data = curs_live.fetchall()
    df = pd.DataFrame(data)
    today = datetime.date.today()
    stock = yf.download(tickers=currency_name, period="max")
    stock = stock.reset_index()
    new_data = pd.concat([df, stock], axis=0)
    new_data.drop_duplicates(subset=['Date'], inplace=True)
    new_data.sort_values(by=['Date'], ascending=False, inplace=True)
    new_data.to_sql(table_name, curs_live, if_exists='replace', index=False)

def updater():
    while True:
        with open('currency_list/1.txt') as f:
            for line in f:
                table = line.strip().replace('-', '_').replace('1', '_')
                currency = line.strip()
                insert_to_db_update(table_name=table, currency_name=currency)
        return False
    

def live_price(table_name, currency_name):
    x = yf.Ticker(currency_name).history()
    x.reset_index(inplace=True)
    x['Date'] = datetime.now()  # Use datetime.now() instead of datetime.datetime.now()
    x.rename(columns={'Stock Splits': 'Stock_Splits'}, inplace=True)
    y = x[::-1]
    y.to_sql(table_name, engine, if_exists='append', index=False, chunksize=1)


def live_click(table, currency):
    return live_price(table_name=table, currency_name=currency)

@app.route("/live", methods=["GET", "POST"])
def live():
    if request.method == "GET":
        dates_live, close_live = get_hist_data_live('BTC_GBP')
        live_click('BTC_GBP', currency='BTC-GBP')
        # return render_template('chart.html', close_live=close_live, dates_live=dates_live)
        return render_template('chart_live.html', data=close_live, labels=dates_live, table_name='BTC_GBP')
    elif request.method == "POST":
        table_live = request.form.get('currency')
        currency = table_live.replace('_', '-').replace('_', '1')
        print(table_live, currency)
        dates_live, close_live = get_hist_data_live(table_live)
        live_click(table_live, currency)
        # data = {'dates_live': dates_live, 'close_live': close_live, 'table_live': currency}
        # return jsonify(data)
        return render_template('chart_live.html', data=close_live, labels=dates_live, table_name=currency)













###################### only live ########################


def live_price_only(currency):
    x = yf.Ticker(currency).history()
    print("step1: {0}".format(currency))

    if x.empty:
        print("step2: {0}".format(currency))
        print("Error: DataFrame is empty.")
        return None, None
    x.reset_index(inplace=True)
    x['Date'] = datetime.now() 
    print("step3: {0}".format(currency))
    x.rename(columns={'Stock Splits': 'Stock_Splits'}, inplace=True)           
    if 'Date' not in x.columns or 'Close' not in x.columns:
        print("step4: {0}".format(currency))
        print("Error: DataFrame is missing 'Date' or 'Close' columns.")
        return None, None
    y = x.iloc[-1]
    date_value = y['Date']
    close_value = y['Close']
    print("step5: {0}".format(currency))
    print("step6: Date:{0} Close: {1}".format(date_value, close_value))
    print(type(date_value), type(close_value))
    return date_value, close_value


@app.route("/onlylive", methods=["GET", "POST"])
def onlylive():
    if request.method == "GET":
        date_value, close_value = live_price_only('BTC-GBP')
        dates_live = str(date_value)
        close_live = str(close_value)
        data = {'dates_live': dates_live, 'close_live': close_live}
        json_data = jsonify(data)
        return json_data, render_template('chart_only_live.html',dates_live=dates_live, close_live=close_live,  table_live='BTC_GBP')
    elif request.method == "POST":
        table_live = request.form.get('currency')
        if table_live is None:
            table_live = 'BTC-GBP'
        else:
            table_live = table_live.replace('_', '-')
        date_value, close_value = live_price_only(table_live)
        dates_live = str(date_value)
        close_live = str(close_value)
        data = {'dates_live': dates_live, 'close_live': close_live}
        json_data = jsonify(data)
        return json_data, render_template('chart_only_live.html', dates_live=dates_live, close_live=close_live,  table_live=table_live)



@app.route('/get_dates')
def get_dates():
    days = request.args.get('days', type=int)
    if days is None:
        days = 30  # Default value if 'days' parameter is not provided
    dates = []
    for i in range(days):
        date = datetime.now() - timedelta(days=i)
        dates.append(date.strftime("%Y-%m-%d"))
    return jsonify({'date_range': dates})

@app.route('/get_currencies')
def get_currencies():
    currencies = [
        "BTC-GBP", "ETH-GBP", "USDT-GBP", "BNB-GBP", "USDC-GBP", "XRP-GBP", "ADA-GBP", "SOL-GBP", "DOGE-GBP",
        "MATIC-GBP", "HEX-GBP", "DOT-GBP", "DAI-GBP", "SHIB-GBP", "TRX-GBP", "UNI7083-GBP", "AVAX-GBP",
        "LTC-GBP", "ATOM-GBP", "ETC-GBP", "LINK-GBP", "FTT-GBP", "XLM-GBP", "CRO-GBP", "XMR-GBP", "ALGO-GBP",
        "BCH-GBP", "QNT-GBP", "FLOW-GBP", "VET-GBP", "FIL-GBP", "LUNC-GBP", "ICP-GBP", "HBAR-GBP", "EGLD-GBP",
        "XTZ-GBP", "MANA-GBP", "SAND-GBP", "CHZ-GBP", "AAVE-GBP", "EOS-GBP", "THETA-GBP", "BSV-GBP", "MKR-GBP",
        "AXS-GBP", "ZEC-GBP", "TUSD-GBP", "BTTOLD-GBP", "SNX-GBP", "MIOTA-GBP", "CAKE-GBP", "NEO-GBP",
        "GRT6719-GBP", "FTM-GBP", "HNT-GBP", "OMI-GBP", "RUNE-GBP", "CRV-GBP", "TWT-GBP", "DASH-GBP",
        "KAVA-GBP", "ENJ-GBP", "BAT-GBP", "STX4847-GBP", "ZIL-GBP", "DCR-GBP", "XDC-GBP", "1INCH-GBP",
        "COMP5692-GBP", "RVN-GBP", "LRC-GBP", "WAVES-GBP", "XEM-GBP", "HOT2682-GBP", "AR-GBP", "CELO-GBP",
        "DFI-GBP", "GNO-GBP", "CCXX-GBP", "ROSE-GBP", "BTG-GBP", "BAL-GBP", "KSM-GBP", "YFI-GBP", "QTUM-GBP",
        "TFUEL-GBP", "ANKR-GBP", "GLM-GBP", "IOTX-GBP", "RSR-GBP", "KDA-GBP", "OMG-GBP", "ONE3945-GBP",
        "ZRX-GBP", "HIVE-GBP", "SUSHI-GBP", "IOST-GBP", "ICX-GBP", "AMP-GBP", "SRM-GBP", "ABBC-GBP", "FLUX-GBP",
        "MCO-GBP", "ONT-GBP", "WAXP-GBP", "STORJ-GBP", "ZEN-GBP", "XCH-GBP", "SC-GBP", "SXP-GBP", "UMA-GBP",
        "SKL-GBP", "DGB-GBP", "LSK-GBP", "EWT-GBP", "CVC-GBP", "ERG-GBP", "CKB-GBP", "COTI-GBP", "MED-GBP",
        "VGX-GBP", "CELR-GBP", "VERI-GBP", "NU-GBP", "SYS-GBP", "WIN-GBP", "VLX-GBP", "SNT-GBP", "XNO-GBP",
        "ARDR-GBP", "RLC-GBP", "STEEM-GBP", "BNT-GBP", "DAG-GBP", "NMR-GBP", "CTSI-GBP", "FUN-GBP", "CTC-GBP",
        "ARRR-GBP", "REP-GBP", "STRAX-GBP", "ANT-GBP", "PHA-GBP", "RAY-GBP", "C98-GBP", "STMX-GBP", "MTL-GBP",
        "RBTC-GBP", "OXT-GBP", "ACH-GBP", "NKN-GBP", "FET-GBP", "MAID-GBP", "VTHO-GBP", "DERO-GBP", "WOZX-GBP",
        "ARK-GBP", "XWC-GBP", "MLN-GBP", "XVG-GBP", "DIVI-GBP", "ETN-GBP", "META-GBP", "AXEL-GBP", "TT-GBP",
        "VRA-GBP", "NEBL-GBP", "BAND-GBP", "TOMO-GBP", "CLV-GBP", "AVA-GBP", "GXC-GBP", "WAN-GBP", "KMD-GBP",
        "CET-GBP", "AE-GBP", "BCD-GBP", "MONA-GBP", "SBD-GBP", "ELA-GBP", "GRS-GBP", "FIO-GBP", "FIRO-GBP",
        "IRIS-GBP", "SERO-GBP", "NULS-GBP", "ADX-GBP", "GAS-GBP", "FRONT-GBP", "KIN-GBP", "KRT-GBP", "WTC-GBP",
        "CTXC-GBP", "BEAM-GBP", "HNS-GBP", "AION-GBP", "PIVX-GBP", "VITE-GBP", "CUDOS-GBP", "SOLVE-GBP",
        "MARO-GBP", "MWC-GBP", "DNT-GBP", "FSN-GBP", "BTM-GBP", "RSTR-GBP", "NMC-GBP", "XNC-GBP", "AMB-GBP",
        "NIM-GBP", "APL-GBP", "MIR7857-GBP", "PPC-GBP", "GBYTE-GBP", "OXEN-GBP", "WICC-GBP", "LBC-GBP", "VTC-GBP",
        "XHV-GBP", "QRL-GBP", "DMD-GBP", "WABI-GBP", "BTC2-GBP", "XCP-GBP", "SCP-GBP", "INSTAR-GBP", "NRG-GBP",
        "GO-GBP", "PZM-GBP", "QASH-GBP", "ZNN-GBP", "VAL-GBP", "NYE-GBP", "DIME-GBP", "PCX-GBP", "OBSR-GBP",
        "PART-GBP", "CRU-GBP", "DGD-GBP", "BEPRO-GBP", "RDD-GBP", "XMC-GBP", "ZYN-GBP", "ILC-GBP", "ATRI-GBP",
        "EDG-GBP", "MHC-GBP", "CHI-GBP", "POA-GBP", "GRIN-GBP", "NXS-GBP", "FCT-GBP", "BCN-GBP", "HC-GBP",
        "ZANO-GBP", "NAV-GBP", "SALT-GBP", "BIP-GBP", "NVT-GBP", "DTEP-GBP", "PPT-GBP", "NXT-GBP", "ADK-GBP",
        "PAY-GBP", "PAC-GBP", "OTO-GBP", "VSYS-GBP", "BHP-GBP", "PI-GBP", "GHOST-GBP", "SRK-GBP", "GRC-GBP",
        "SKY-GBP", "COLX-GBP", "SFT-GBP", "GAME-GBP", "REV-GBP", "XLT-GBP", "NLG-GBP", "ETP-GBP", "LCC-GBP",
        "SCC3986-GBP", "EMC2-GBP", "NAS-GBP", "DCN-GBP", "ACT-GBP", "DMCH-GBP", "UBQ-GBP", "WGR-GBP", "MIR-GBP",
        "AEON-GBP", "FTC-GBP", "INT-GBP", "BLOCK-GBP", "MAN-GBP", "VIN-GBP", "MRX-GBP", "FO-GBP", "OWC-GBP",
        "CMT2246-GBP", "GHOST5475-GBP", "BCA-GBP", "TRUE-GBP", "GLEEC-GBP", "DNA5234-GBP", "VEX-GBP", "HPB-GBP",
        "QRK-GBP", "IDNA-GBP", "MASS-GBP", "PLC-GBP", "BTX-GBP", "XSN-GBP", "BLK-GBP", "YOYOW-GBP", "HTML-GBP",
        "BHD-GBP", "SMART-GBP", "DYN-GBP", "MGO-GBP", "XMY-GBP", "LEDU-GBP", "PAI-GBP", "CUT-GBP", "XST-GBP",
        "FTX-GBP", "FAIR-GBP", "CURE-GBP", "WINGS-GBP", "SUB-GBP", "TRTL-GBP", "AYA-GBP", "POLIS-GBP", "HYC-GBP",
        "XRC-GBP", "HTDF-GBP", "GCC1531-GBP", "BPS-GBP", "NIX-GBP", "IOC-GBP", "PIN-GBP", "NYZO-GBP", "XBY-GBP",
        "TUBE-GBP", "PHR-GBP", "TERA-GBP", "XAS-GBP", "RINGX-GBP", "ERK-GBP", "MBC-GBP", "DDK-GBP", "USNBT-GBP",
        "ATB-GBP", "TNS-GBP", "FRST-GBP", "BPC-GBP", "COMP-GBP", "BST3997-GBP", "CCA-GBP", "SLS-GBP", "SPHR-GBP",
        "FLASH-GBP", "MIDAS-GBP", "ALIAS-GBP", "BONO-GBP", "AIB-GBP", "BONFIRE-GBP", "BDX-GBP", "ECC-GBP",
        "UNO-GBP", "CSC-GBP", "DUN-GBP", "RBY-GBP", "MTC6498-GBP", "JDC-GBP", "GRN-GBP", "BRC-GBP", "XUC-GBP",
        "LKK-GBP", "MINT-GBP", "DACC-GBP", "HNC-GBP", "ECA-GBP", "MOAC-GBP"
    ]
    return jsonify(currencies=currencies)

    # return jsonify({'currencies': currencies})



if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80, debug=True)