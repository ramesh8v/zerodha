#! c:\python27\python.exe

from bs4 import BeautifulSoup
import requests
from HTMLParser import HTMLParser
from htmlentitydefs import name2codepoint
from datetime import date,time,timedelta
import datetime
from decimal import *
import json
from broker import Broker, Order

LOGIN_URL = 'https://kite.zerodha.com/'
BASE_REFERER = LOGIN_URL
CHART_REFERER = 'https://kite.zerodha.com/advanced-chart'
LOGIN_SUBMIT_URL = 'https://kite.zerodha.com/?next='
ORDER_SUBMIT_URL = 'https://kite.zerodha.com/api/orders'
AMO_URL = 'https://kite.zerodha.com/api/amo' #after market orders
SESSION_URL = 'https://kite.zerodha.com/api/session'
TXN_PASSWORD_SUBMIT_URL = 'https://kite.zerodha.com/api/profile'
DASHBOARD_URL = 'https://kite.zerodha.com/dashboard/'
MARKET_WATCH_URL = 'https://kite.zerodha.com/marketwatch/'
MARKET_WATCH_API_URL = 'https://kite.zerodha.com/api/marketwatch'
CASH_MARGIN_URL = 'https://kite.zerodha.com/api/margins'
ORDER_CANCEL_URL = 'https://kite.zerodha.com/api/orders/'
TIME_SERIES_URL = 'https://kite.zerodha.com/ohlc/%s/%s' #https://kite.zerodha.com/ohlc/738561/3minute
ORDER_MODIFY_URL = ORDER_CANCEL_URL
USER_AGENT_STR = "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36"

requests.packages.urllib3.disable_warnings()


# Over-ride this if necessary 
Order.Type._to_str = {Order.Type.LIMIT: "LIMIT",
                    Order.Type.MARKET: "MARKET",
                    Order.Type.STOP: "SL-M",
                    Order.Type.STOP_LIMIT: "SL",
                     }
class Zerodha(Broker):
    __login_retries = 0
    __max_retries = 3
    def __init__(self, auth, prefs = {'default_product': 'MIS','max_retries':3}): #set username password and bdate here
        # Login Var
        self.auth = auth
        self.prefs = prefs
        if prefs.get('max_retries'):
            self.__max_retries = prefs['max_retries']
            
        self.headers_normal = {
                                'user-agent': USER_AGENT_STR,
                                'Host': 'kite.zerodha.com',
                                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                                'Accept-Encoding': 'gzip, deflate, sdch',
                                'Referer': BASE_REFERER
                                }
        self.headers_json = {'user-agent': USER_AGENT_STR,
                             'Host': 'kite.zerodha.com',
                             'Referer': 'https://kite.zerodha.com/',
                             'Accept': 'application/json, text/plain, */*',
                             'Origin': 'https://kite.zerodha.com',
                             'Referer': BASE_REFERER,
                             'Connection': 'keep-alive',
                             'Content-Type': 'application/json;charset=UTF-8',
                             'Accept-Language': 'en-US,en;q=0.8',
                             }
        self.session = requests.Session()
        '''self.proxy = {"https":"proxy1.wipro.com:8080",
                      #"http":"proxy1.wipro.com:8080"
                      }'''
        self.proxy = prefs.get('proxy')
    def connect(self):      
        
        params = dict(user_id=self.auth['user_id'], password=self.auth['password'])
        
        self.resp = self.session.post(LOGIN_SUBMIT_URL,
                                      proxies = self.proxy,
                                      data = params, 
                                      headers = self.headers_normal,
                                      verify = False)
        
        params = dict()
        self.soup = BeautifulSoup(self.resp.text, 'html.parser')
        form = self.soup.find_all('form')[0]
        hidden_ips = form.find_all(attrs={'type': 'hidden'})
        for hidden_ip in hidden_ips:
            params[str(hidden_ip['name'])] = str(hidden_ip['value'])
        key = str(form.find_all('span')[0].contents[0])
        params['answer1'] = self.auth[key]
        key = str(form.find_all('span')[1].contents[0])
        params['answer2'] = self.auth[key]
        params['questions'] = ''
        self.resp = self.session.post(LOGIN_SUBMIT_URL,
                                      proxies = self.proxy,
                                      data = params, 
                                      headers = self.headers_normal,
                                      verify = False)

        self.soup = BeautifulSoup(self.resp.text, 'html.parser')
        
        
        params = dict(password = self.auth['txn_password'])
        self.headers_json['Referer'] = MARKET_WATCH_URL
        self.resp = self.session.post(TXN_PASSWORD_SUBMIT_URL,
                                    json = params, 
                                    headers = self.headers_json,
                                    proxies = self.proxy,
                                    verify = False)
        return json.loads(self.resp.text)['data'] == True
        

    def place_order(self, order):
        param = {
                'disclosed_quantity': 0, 
                'tradingsymbol': order.security,
                'quantity': order.quantity,
                'exchange': order.exchange,
                'order_type': Order.Type.to_str(order.type),
                'price': order.price,
                'product': order.extra['product'],
                'transaction_type': Order.Action.to_str(order.action),
                'validity': Order.Validiy.to_str(order.validity),
                'trigger_price': order.stop_price,
                 }
        
        self.resp = self.session.post(ORDER_SUBMIT_URL, 
                                      json = param, 
                                      headers = self.headers_json,
                                      proxies = self.proxy,
                                      verify = False)
        try:
            return json.loads(self.resp.text)['data']['order_id']
        except KeyError:
            raise ValueError, json.loads(self.resp.text)['message'] + "\n" + str(param)
    
    # precision of pricing at NSE is 0.05          
    @classmethod
    def __round_5(cls,num):
        return (100*round(num,2) - 100*round(num,2) % 5)/100
    
    # buy stocks for delivery (default exchange is set NSE for Zerodha)
    def buy_cash(self,
                security,
                quantity,
                price = 0,
                stop_price = 0,
                fill_strategy = "",
                exchange = 'NSE'):
        extra = {'product':'CNC'}
        if exchange in ['NSE','NFO']:
            price = Zerodha.__round_5(price)
            stop_price = Zerodha.__round_5(stop_price)
        elif exchange in ['BSE']:
            price = round(price,2)
            stop_price = round(stop_price,2)
        order = self.build_buy_order(security = security,
                                    quantity = quantity,
                                    price = price,
                                    stop_price = stop_price,
                                    exchange = exchange,
                                    fill_strategy = "",
                                    extra = extra)
        return self.place_order(order)        
    
    def sell_cash(self,
                security,
                quantity,
                price = 0,
                stop_price = 0,
                fill_strategy = "",
                exchange = 'NSE'):
                    
        extra = {'product':'CNC'}
        if exchange in ['NSE','NFO']:
            price = Zerodha.__round_5(price)
            stop_price = Zerodha.__round_5(stop_price)
        elif exchange in ['BSE']:
            price = round(price,2)
            stop_price = round(stop_price,2)
        order = self.build_sell_order(security = security,
                                    quantity = quantity,
                                    price = Zerodha.__round_5(price),
                                    stop_price = Zerodha.__round_5(stop_price),
                                    exchange = exchange,
                                    fill_strategy = "",
                                    extra = extra)
        return self.place_order(order)            
    
    #currently supports only NSE exchange all security including fno
    def buy_margin(self,
                security,
                quantity,
                price = 0,
                stop_price = 0,
                fill_strategy = "",
                exchange = 'NSE'):
        #Zerodha uses NSE and NFO as exchange field to distinguish stock and FnO
        #All stock symbols have -EQ suffix which can be used to decide whether to 
        #select NSE or NFO when user selects NSE
        if exchange == 'NSE' and not security.find('-EQ') >= 0:
            exchange = "NFO"
        extra = {'product':'MIS'}
        if exchange in ['NSE','NFO']:
            price = Zerodha.__round_5(price)
            stop_price = Zerodha.__round_5(stop_price)
        elif exchange in ['BSE']:
            price = round(price,2)
            stop_price = round(stop_price,2)
        order = self.build_buy_order(security = security,
                                    quantity = quantity,
                                    price = Zerodha.__round_5(price),
                                    stop_price = Zerodha.__round_5(stop_price),
                                    exchange = exchange,
                                    fill_strategy = "",
                                    extra = extra)
        return self.place_order(order)            
    
    #currently supports only NSE exchange all security including fno
    def sell_margin(self,
                security,
                quantity,
                price = 0,
                stop_price = 0,
                fill_strategy = "",
                exchange = 'NSE'):
        #Zerodha uses NSE and NFO as exchange field to distinguish stock and FnO
        #All stock symbols have -EQ suffix which can be used to decide whether to 
        #select NSE or NFO when user selects NSE
        if exchange == 'NSE' and not security.find('-EQ') >= 0:
            exchange = "NFO"
        extra = {'product':'MIS'}
        if exchange in ['NSE','NFO']:
            price = Zerodha.__round_5(price)
            stop_price = Zerodha.__round_5(stop_price)
        elif exchange in ['BSE']:
            price = round(price,2)
            stop_price = round(stop_price,2)
        order = self.build_sell_order(security = security,
                                    quantity = quantity,
                                    price = Zerodha.__round_5(price),
                                    stop_price = Zerodha.__round_5(stop_price),
                                    exchange = exchange,
                                    fill_strategy = "",
                                    extra = extra)
        return self.place_order(order)

    def buy_fno(self,
                security,
                quantity,
                price = 0,
                stop_price = 0,
                fill_strategy = "",
                exchange = 'NFO'):
        extra = {'product':'NRML'}
        if exchange in ['NSE','NFO']:
            price = Zerodha.__round_5(price)
            stop_price = Zerodha.__round_5(stop_price)
        elif exchange in ['BSE']:
            price = round(price,2)
            stop_price = round(stop_price,2)
        order = self.build_buy_order(security = security,
                                    quantity = quantity,
                                    price = Zerodha.__round_5(price),
                                    stop_price = Zerodha.__round_5(stop_price),
                                    exchange = exchange,
                                    fill_strategy = "",
                                    extra = extra)
        return self.place_order(order)
    
    def sell_fno(self,
                security,
                quantity,
                price = 0,
                stop_price = 0,
                fill_strategy = "",
                exchange = 'NFO'):
        extra = {'product':'NRML'}
        if exchange in ['NSE','NFO']:
            price = Zerodha.__round_5(price)
            stop_price = Zerodha.__round_5(stop_price)
        elif exchange in ['BSE']:
            price = round(price,2)
            stop_price = round(stop_price,2)
        order = self.build_sell_order(security = security,
                                    quantity = quantity,
                                    price = Zerodha.__round_5(price),
                                    stop_price = Zerodha.__round_5(stop_price),
                                    exchange = exchange,
                                    fill_strategy = "",
                                    extra = extra)
        return self.place_order(order)                        
    
    def buy(self,
                security,
                quantity,
                price = 0,
                stop_price = 0,
                fill_strategy = "",
                exchange = 'NSE'):
        
        if exchange == 'NSE' and not security.find('-EQ') >= 0:
            exchange = "NFO"
        
        if self.prefs['default_product'] == 'MIS':
            extra = {'product': 'MIS'}
        elif exchange == 'NFO':
            extra = {'product': 'NRML'}
        else:
            extra = {'product': 'CNC'}
        
        if exchange in ['NSE','NFO']:
            price = Zerodha.__round_5(price)
            stop_price = Zerodha.__round_5(stop_price)
        elif exchange in ['BSE']:
            price = round(price,2)
            stop_price = round(stop_price,2)
        order = self.build_buy_order(security = security,
                                    quantity = quantity,
                                    price = Zerodha.__round_5(price),
                                    stop_price = Zerodha.__round_5(stop_price),
                                    exchange = exchange,
                                    fill_strategy = "",
                                    extra = extra)
        return self.place_order(order)                        

    def sell(self,
                security,
                quantity,
                price = 0,
                stop_price = 0,
                fill_strategy = "",
                exchange = 'NSE'):
        
        if exchange == 'NSE' and not security.find('-EQ') >= 0:
            exchange = "NFO"
        
        if self.prefs['default_product'] == 'MIS':
            extra = {'product': 'MIS'}
        elif exchange == 'NFO':
            extra = {'product': 'NRML'}
        else:
            extra = {'product': 'CNC'}
        
        if exchange in ['NSE','NFO']:
            price = Zerodha.__round_5(price)
            stop_price = Zerodha.__round_5(stop_price)
        elif exchange in ['BSE']:
            price = round(price,2)
            stop_price = round(stop_price,2)
        order = self.build_sell_order(security = security,
                                    quantity = quantity,
                                    price = Zerodha.__round_5(price),
                                    stop_price = Zerodha.__round_5(stop_price),
                                    exchange = exchange,
                                    fill_strategy = "",
                                    extra = extra)
        return self.place_order(order)
    
    def modify_order(self, order_id,
                    quantity,
                    price = 0,
                    stop_price = 0,
                    fill_strategy = ""):
        order = self.get_order_info(order_id)
        order.quantity = quantity
        order.price = price
        order.stop_price = stop_price
        param = {
                'disclosed_quantity': 0, 
                'tradingsymbol': order.security,
                'quantity': order.quantity,
                'exchange': order.exchange,
                'order_type': Order.Type.to_str(order.type),
                'price': order.price,
                'product': order.extra['product'],
                'transaction_type': Order.Action.to_str(order.action),
                'validity': Order.Validiy.to_str(order.validity),
                'trigger_price': order.stop_price,
                 }
        
        self.resp = self.session.post(ORDER_MODIFY_URL + order_id,
                                    json = param, headers = self.headers_json,
                                    verify = False)
        try:
            return json.loads(self.resp.text)['data']['order_id']
        except KeyError:
            raise ValueError, json.loads(self.resp.text)['message'] + "\n" + str(param)
        
    def cancel_order(self,order_id):
        cancel_url = ORDER_CANCEL_URL + order_id
        self.resp = self.session.delete(cancel_url, 
                                   headers = self.headers_json,
                                   verify = False)
        return json.loads(self.resp.text)['message'] == "success"
    
    def get_order_status(self,order_id):
        return self.get_order_info(order_id).state
    
        
    def get_open_orders(self):
        self.resp = self.session.get(ORDER_SUBMIT_URL,
                                      headers = self.headers_json,
                                      verify = False)
        json_text = str(self.resp.text).replace('null','""')
        
        try:
            zorders = json.loads(json_text)['data']
            
        except KeyError:
            raise ValueError,json.loads(json_text)['message']
        
        orders = []
        for zorder in zorders:
            orders.append(self._zorder_to_order(zorder))
        return orders
    
    def __type_str_to_num(self, type_str):
        if type_str == 'MARKET':
            order_type = Order.Type.MARKET
        elif type_str == 'LIMIT':
            order_type = Order.Type.LIMIT
        elif type_str == 'SL':
            order_type = Order.Type.STOP_LIMIT
        else: order_type = Order.Type.STOP
        return order_type
                   
    def __status_str_to_num(self, status_str):
        str_to_num = {'PENDING': Order.State.SUBMITTED,
                      'TRIGGER PENDING': Order.State.SUBMITTED,
                     'OPEN': Order.State.ACCEPTED,
                     'REJECTED': Order.State.REJECTED,
                     'CANCELLED': Order.State.CANCELED,
                     'COMPLETE': Order.State.FILLED,                     
                     }
        if not str_to_num.get(status_str): print status_str
        return str_to_num.get(status_str)
    #takes order information in json format and returns order
    def _zorder_to_order(self,zorder):
        order_type = self.__type_str_to_num(zorder['order_type'])
        if zorder['transaction_type'] == 'BUY':
            action = Order.Action.BUY
        else: action = Order.Action.SELL
        o = Order(order_type = order_type,
                action = action,
                security = zorder['tradingsymbol'],
                quantity = zorder['quantity'],
                price = zorder['price'],
                stop_price = zorder['trigger_price'],
                exchange = zorder['exchange'],
                extra = {'product':zorder['product']}
                    )
        o.id = zorder['order_id']
        o.filled = zorder['filled_quantity']
        o.state = self.__status_str_to_num(zorder['status'])
        o.avg_fill_price = zorder['average_price']
        o.exchange_order_id = zorder['exchange_order_id']
        if zorder['exchange_timestamp']:
            o.submit_datetime = datetime.datetime.strptime(zorder['exchange_timestamp'],"%Y-%m-%d %H:%M:%S")
        return o
    
    def get_order_info(self, order_id):
        orders = self.get_open_orders()
        for order in orders:
            if order.id == order_id:
                return order
                
    def __get_market_watch(self):
        self.resp = self.session.get(MARKET_WATCH_API_URL,
                                     headers = self.headers_json, verify = False)
        m_watch = json.loads(self.resp.text.replace('null','""'))['data'][0]
        self.m_watch_id = m_watch['id']
        self.m_watch_list = m_watch['items']
   
    def get_watch_list(self):
        self.__get_market_watch()

    def get_time_series(self, stock, frequency = 'day'):
        self.get_watch_list();
        stock_id = None
        stock = stock.replace('-EQ','')
        for item in self.m_watch_list:
            if item['tradingsymbol'] == stock:
                stock_token = item['token']
                break
        
        url = TIME_SERIES_URL%(stock_token, frequency)
      
        self.resp = self.session.get(url,
                                     headers = self.headers_normal,
                                     verify = False)
    
        return self.resp.text
                
            
    
    def _add_to_market_watch(self, security):
        self.__get_market_watch()
        l = len(self.m_watch_list) 
        url = MARKET_WATCH_API_URL + '/' + str(self.m_watch_id) + '/items'
        param = {}
        if security.find('-EQ') > 0:
            param['segment'] = 'NSE'
        else: param['segment'] ='NFO'
        param['tradingsymbol'] = security.replace('-EQ','')
        param['watch_id'] = self.m_watch_id
        param['weight'] = l + 1
        self.resp = self.session.post(url,
                                     json = param,
                                     headers = self.headers_json)
        return self.resp.text
        #return json.loads(self.resp.text.replace('null','""'))['message'] == 'success'
                            
    def _remove_from_market_watch(self, security):
        self.__get_market_watch()
        stock_token = None
        security = security.replace('-EQ','')
        for item in self.m_watch_list:
            if item['tradingsymbol'] == security:
                stock_token = item['id']
                break
        if stock_token == None:
            return                
        url = MARKET_WATCH_API_URL + '/' + str(self.m_watch_id) + '/' + str(stock_token)
        self.resp = self.session.delete(url, 
                                   headers = self.headers_json)
    
        return json.loads(self.resp.text)['message'] == "success"
        
    def get_current_price(self, security):
        self.__get_market_watch()
        for item in self.m_watch_list:
            if item['tradingsymbol'] == security:
                return item['last_price']
        self._add_to_market_watch(security)
        return self.get_current_price( security)
    
    def get_cash(self):
        self.resp = self.session.get(CASH_MARGIN_URL,
                                     headers = self.headers_json)
        jresp = json.loads(self.resp.text)
        if jresp['message'] != "success": raise ValueError, jresp['message']
        return jresp['data']['equity']['available']['cash']
    
    def get_margin_available(self):
        self.resp = self.session.get(CASH_MARGIN_URL,
                                     headers = self.headers_json)
        jresp = json.loads(self.resp.text)
        if jresp['message'] != "success": raise ValueError, jresp['message']
        return jresp['data']['equity']['available']['adhoc_margin']
    
    @classmethod
    def estimate_intraday_cost(cls, price, quantity, action = 'BUY'):
        if price * quantity * 0.1/100 > 20:
            brokerage = 20
        else: brokerage = price * quantity * 0.1/100 > 20
        stt = 0.1 * price * quantity / 100
        turnover_charge = 0.00325 * price * quantity / 100
        service_tax = 14.0 * (brokerage + stt) / 100.0
        sebi_charge = 20 / 1000000 * price * quantity
        return brokerage + stt + turnover_charge + service_tax + sebi_charge
        
