
class QuoteInfo:
    def __init__(self):
        self.symbol = str()
        self.exchange = str()
        self.date = None
        self.time = None
        self.local_time = None
        self.price = float()
        self.volume = int()
        self.changepct = float()
    
    def __repr__(self):
        d = []
        d.append(self.symbol+',')
        d.append(self.exchange+',')
        d.append(str(self.time)+',')
        d.append(str(self.price)+',')
        d.append(str(self.volume)+',')
        d.append(str(self.changepct)+'%,')
        return str().join(d)

class QuoteArray:
    def __init__(self):
        self.symbol = str()
        self.exchange = str()
        self.date = None
        self.time_arr = []
        self.price_arr = []
        self.volume_arr = []

    def append(self,q):
        self.symbol = q.symbol
        self.exchange = q.exchange
        self.date = q.date
        self.price_arr.append(q.price)
        self.time_arr.append(q.time)
        self.volume_arr.append(q.volume)

            
class MarketDepth:
            
    def __init__(self):
        self.symbol = str()
        self.exchange = str()
        self.date = None
        self.time = None
        self.local_time = None
        self.bid_q = []
        self.bid_qty_q = []
        self.ask_q = []
        self.ask_qty_q = []
    
    def __repr__(self):
        d = []
        d.append(self.symbol+',')
        d.append(self.exchange+',')
        d.append(str(self.time)+',')
        for bid in self.bid_q:
            d.append(str(bid)+',')
        
        for bid_qty in self.bid_qty_q:
            d.append(str(bid_qty)+',')
        
        for ask in self.ask_q:
            d.append(str(ask)+',')
        
        for ask_qty in self.ask_qty_q:
            d.append(str(ask_qty)+',')
        
        return str().join(d)
    


class MarketDepthArray:
    def __init__(self):
        self.symbol = str()
        self.exchange = str()
        self.date = None
        self.time_arr = []
        self.bid_q_arr = []
        self.bid_qty_q_arr = []
        self.ask_q_arr = []
        self.ask_qty_q_arr = []
        
        
        
        
    