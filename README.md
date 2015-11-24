# zerodha
Automation of zerodha for HFT (currently tested with Python2.7)
```python
from broker.module import Zerodha, Order
auth = dict()
auth['user_id'] = 'UDI'
auth['password'] = 'PASS1'
auth['txn_password'] = 'PASS2'
#question array
q_arr = [
    'What was the name of the college from which you graduated? (e.g. Xavier, Symbosis etc)',
    'Which year did you complete your graduation? (e.g. 2000, 1990 etc)',
    "What is your mother's name?",
    'Which floor of the building do you live on?',
    'What is your height in feet? (e.g. 5.4 4.8 etc)',
    'What is you birth place?',
    ]
#answer array
a_arr = [
    "ans1",
    "ans2",
    "ans3",
    "ans4",
    "ans5",
    "ans6"
    ]
for r in range(0,len(q_arr)):
    auth[q_arr[r]] = a_arr[r]
"""
  MIS- margin intraday square-off, 
  CNC - cash (buy for delivery, sell existing shares)
"""
zerodha = Zerodha(auth, prefs = {'default_product' : 'MIS',})
if zerodha.connect():
  print('Logged in to Zerodha')
else:
  print('Check credentials')
#CAUTION- This will actually place orders in your zerodha account
buy_id = zerodha.buy(security="SBIN-EQ",
                                quantity=1,
                                price=230)

buy_id = zerodha.sell(security="SBIN-EQ",
                                quantity = 1,
                                price = 230)

order = zerodha.get_order_info(buy_id)
if order.state == order.State.FILLED:
  print("Buy exectuted")
```

To Do:
- Addition of Test casees
- Support for F&O
- Integration with data vendors
- Integration with a broader library like Zipline to include simulation and several brokers
- Support for Python 3

Please log issues here if you find any.

site: www.xerxys.in
