from __init__ import QuoteInfo,MarketDepth
import cookielib
from urllib2 import HTTPHandler,HTTPSHandler,HTTPErrorProcessor,HTTPRedirectHandler,HTTPCookieProcessor
import urllib2
import datetime
import requests
import time

ICICI_QUOTE_URL = 'https://secure.icicidirect.com/TradeRacerWeb/trading/equity/Ri_GetQuote.asp'
ICICI_FNO_QUOTE_URL = 'https://secure.icicidirect.com/NewSiteTrading/trading/fno/Includes/GetQuote.asp'
""" QUOTE params
m_RequestType:
Page:
FRMQTYCAL:
FFO_XCHNG_CD:NFO
FFO_PRDCT_TYP:O
PrdctTyp:O
FFO_UNDRLYNG:NIFTY
FFO_EXPRY_DT:24-Sep-2015
FFO_OPT_TYP_new:C,E
FFO_STRK_PRC:750000
FFO_MIN_LOT_QTY:25
FFO_OPT_TYP:C
FFO_EXER_TYP:E
FFO_UNDRLYNG_PRE:NIFTY
"""
ICICI_FNO_DEPTH_URL = 'https://secure.icicidirect.com/NewSiteTrading/trading/fno/Includes/Bestbid.asp?Page=&FFO_UNDRLYNG=NIFTY&FFO_XCHNG_CD=NFO&FFO_PRDCT_TYP=O&FFO_OPT_TYP=C&FFO_EXPRY_DT=24-Sep-2015&FFO_EXER_TYP=E&FFO_RQST_TYP=*&FFO_STRK_PRC=750000&FFO_MIN_LOT_QTY=25'
""" QUOTE params
FFO_UNDRLYNG:NIFTY
FFO_XCHNG_CD:NFO
FFO_PRDCT_TYP:O
FFO_OPT_TYP:C
FFO_EXPRY_DT:24-Sep-2015
FFO_EXER_TYP:E
FFO_RQST_TYP:*
FFO_STRK_PRC:750000
FFO_MIN_LOT_QTY:25
"""

def get_quote(symbol,exchange = 'NSE'):
    session = requests.Session()
    post_data = symbol +  '|^ALL|^Q|^|$'
    resp = session.post(ICICI_QUOTE_URL, data = post_data)
    q_resp = resp.text.replace('0|$','').replace('|$','').split('|^')
    #print q_resp
    q_NSE = QuoteInfo()
    q_BSE = QuoteInfo()
    now = datetime.datetime.now()
    q_NSE.symbol = symbol
    q_NSE.exchange = 'NSE'    
    q_NSE.date = now.date()
    q_NSE.local_time = now.time()
    q_NSE.price = float(q_resp[19])
    q_NSE.volume = int(q_resp[31])
    q_NSE.changepct = float(q_resp[20])
    dt = time.strptime(q_resp[22],'%d-%b-%Y %H:%M:%S')
    q_NSE.time = datetime.time(hour=dt.tm_hour,minute=dt.tm_min,second=dt.tm_sec)
    
    q_BSE.symbol = symbol
    q_BSE.exchange = 'BSE'    
    q_BSE.date = now.date()
    q_BSE.local_time = now.time()
    q_BSE.price = float(q_resp[2])
    q_BSE.volume = int(q_resp[14])
    q_BSE.changepct = float(q_resp[3])
    dt = time.strptime(q_resp[5],'%d-%b-%Y %H:%M:%S')
    q_BSE.time = datetime.time(hour=dt.tm_hour,minute=dt.tm_min,second=dt.tm_sec)
      
    if exchange == 'NSE':
        return [q_NSE]
    elif exchange == 'BSE':
        return [q_BSE]
    elif exchange == 'ALL':
        return [q_NSE,q_BSE]



def get_market_depth(symbol,exchange='NSE'):
    session = requests.Session()
    post_data = symbol +  '|^ALL|^M|^|$'
    resp = session.post(ICICI_QUOTE_URL,data = post_data)
    md_resp = resp.text.replace('0|$','').replace('|$','').split('|^')
    md_NSE = MarketDepth()
    md_BSE = MarketDepth()
    now = datetime.datetime.now()
    '''
    self.symbol = str()
        self.exchange = str()
        self.date = None
        self.time = None
        self.local_time = None
        self.bid_q = []
        self.bid_qty_q = []
        self.ask_q = []
        self.ask_qty_q = []
    '''
    # BSE stuff
    md_BSE.symbol = symbol
    md_BSE.exchange = 'BSE'
    md_BSE.date = now.date()
    md_BSE.local_time = now.time()
    dt = time.strptime(md_resp[3],'%d-%b-%Y %H:%M:%S')
    md_BSE.time = datetime.time(hour=dt.tm_hour,minute=dt.tm_min,second=dt.tm_sec)
    for i in range(0,5):
        md_BSE.bid_q.append(float(md_resp[5+i*4]))
    
    for i in range(0,5):
        md_BSE.bid_qty_q.append(int(md_resp[4+i*4]))
    
    for i in range(0,5):
        md_BSE.ask_q.append(float(md_resp[7+i*4]))
    
    for i in range(0,5):
        md_BSE.ask_qty_q.append(int(md_resp[6+i*4]))
    
    
    # NSE stuff
    md_NSE.symbol = symbol
    md_NSE.exchange = 'NSE'
    md_NSE.date = now.date()
    md_NSE.local_time = now.time()
    dt = time.strptime(md_resp[29],'%d-%b-%Y %H:%M:%S')
    md_NSE.time = datetime.time(hour=dt.tm_hour,minute=dt.tm_min,second=dt.tm_sec)
    for i in range(0,5):
        md_NSE.bid_q.append(float(md_resp[31+i*4]))
    
    for i in range(0,5):
        md_NSE.bid_qty_q.append(int(md_resp[30+i*4]))
    
    for i in range(0,5):
        md_NSE.ask_q.append(float(md_resp[33+i*4]))
    
    for i in range(0,5):
        md_NSE.ask_qty_q.append(int(md_resp[32+i*4]))
       
    if exchange == 'NSE':
        return [md_NSE]
    elif exchange == 'BSE':
        return [md_BSE]
    elif exchange == 'ALL':
        return [md_NSE,md_BSE]
