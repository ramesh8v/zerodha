
from broker.module import Zerodha, Order
from quotelib import icici, nsetoicici
#import nsetoicici
import time
import datetime
auth = dict()

auth['user_id'] = 'DJ9843'
auth['password'] = 'asdf&890'
auth['txn_password'] = 'ASDF&890'

q_arr = [
    'What was the name of the college from which you graduated? (e.g. Xavier, Symbosis etc)',
    'Which year did you complete your graduation? (e.g. 2000, 1990 etc)',
    "What is your mother's name?",
    'Which floor of the building do you live on?',
    'What is your height in feet? (e.g. 5.4 4.8 etc)',
    'What is you birth place?',
    ]
a_arr = [
    "geca",
    "2008",
    "megha",
    "first",
    "180",
    "aurangabad"
    ]
for r in range(0,len(q_arr)):
    auth[q_arr[r]] = a_arr[r]


def get_quote(security):
    sym = nsetoicici.nse_to_icici[security]
    q = icici.get_quote(sym)
    q[0].security = q[0].symbol
    return q[0]


zerodha = Zerodha(auth, prefs = {'default_product' : 'MIS'})
zerodha.connect()
security = 'ITC-EQ'
quantity = int(2000 / get_quote(security).price) - 1    

buy_id = zerodha.buy(security=security,
                                quantity = quantity,
                                price = get_quote(security).price - 1)
input ('dd')
zerodha = Zerodha(auth, prefs = {'default_product' : 'MIS'})
zerodha.connect()
buy_id = zerodha.order_modify(security=security,
                                quantity = quantity,
                                price = get_quote(security).price - 2)


