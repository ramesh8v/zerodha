import abc


# This class is used to prevent bugs like the one triggered in testcases.bitstamp_test:TestCase.testRoundingBug.
# Why not use decimal.Decimal instead ?
# 1: I'd have to expose this to users. They'd have to deal with decimal.Decimal and it'll break existing users.
# 2: numpy arrays built using decimal.Decimal instances have dtype=object.


######################################################################
# Orders
# http://stocks.about.com/od/tradingbasics/a/markords.htm
# http://www.interactivebrokers.com/en/software/tws/usersguidebook/ordertypes/basic_order_types.htm
#
# State chart:
# INITIAL           -> SUBMITTED
# INITIAL           -> CANCELED
# SUBMITTED         -> ACCEPTED
# SUBMITTED         -> CANCELED
# ACCEPTED          -> FILLED
# ACCEPTED          -> PARTIALLY_FILLED
# ACCEPTED          -> CANCELED
# PARTIALLY_FILLED  -> PARTIALLY_FILLED
# PARTIALLY_FILLED  -> FILLED
# PARTIALLY_FILLED  -> CANCELED

class Order(object):
    """Base class for orders.
    :param order_type: The order type
    :type order_type: :class:`Order.Type`
    :param action: The order action.
    :type action: :class:`Order.Action`
    :param security: Security identifier.
    :type security: string.
    :param quantity: Order quantity.
    :type quantity: int/float.
    :param price: Limit Price (for limit orders only)
    :type price: int/float
    :param stop_price: Trigger Price for Stop Orders
    :type stop_price: int/float
    :param validity: Order validity (DAY, Good Till Cancelled, Good Till Date)
    :type validity: :class:'Order.Validity'
    :param fill_strategy: Immediate or Cancel, Fill or Kill, All or None
    :type fill_strategy: :class:'Order.FillStrategy
    :param extra: Extra Parameters to provide additional information
    :type extra: dict()
    
    .. note::
        This is a base class and should not be used directly.
        Valid **type** parameter values are:
         * Order.Type.MARKET
         * Order.Type.LIMIT
         * Order.Type.STOP
         * Order.Type.STOP_LIMIT
        Valid **action** parameter values are:
         * Order.Action.BUY
         * Order.Action.BUY_TO_COVER
         * Order.Action.SELL
         * Order.Action.SELL_SHORT
    """

    class Action(object):
        BUY = 1
        BUY_TO_COVER = 2
        SELL = 3
        SELL_SHORT = 4
        _to_str = {BUY: 'BUY',
                  BUY_TO_COVER: 'BUY TO COVER',
                  SELL: 'SELL',
                  SELL_SHORT: 'SELL SHORT'
                  }
        
        def __init__(self, value):
            self.value = value
        def __str__(self):
            return self._to_str[self.value]
        def __repr__(self):
            return self._to_str[self.value]
        def __eq__(self, val):
            if type(val) == type(str()):
                return self._to_str[self.value] == val
            elif type(val) == type(int()):
                return self.value == val
            elif type(val) == type(Order.Action(1)):
                return self.value == val.value
            else: raise ValueError('Incompatible types')
        @classmethod
        def to_str(cls, val):
            return cls._to_str[val]
                

    class State(object):
        INITIAL = 1  # Initial state.
        SUBMITTED = 2  # Order has been submitted.
        ACCEPTED = 3  # Order has been acknowledged by the broker.
        CANCELED = 4  # Order has been canceled.
        PARTIALLY_FILLED = 5  # Order has been partially filled.
        FILLED = 6  # Order has been completely filled.
        EXPIRED = 7 # Order has expired
        REJECTED = 8 # Order has been rejected

        @classmethod
        def to_str(cls, state):
            if state == cls.INITIAL:
                return "INITIAL"
            elif state == cls.SUBMITTED:
                return "SUBMITTED"
            elif state == cls.ACCEPTED:
                return "ACCEPTED"
            elif state == cls.CANCELED:
                return "CANCELED"
            elif state == cls.PARTIALLY_FILLED:
                return "PARTIALLY_FILLED"
            elif state == cls.FILLED:
                return "FILLED"
            elif state == cls.EXPIRED:
                return "EXPIRED"
            elif state == cls.REJECTED:
                return "REJECTED"
            else:
                raise Exception("Invalid state")

    class Type(object):
        MARKET = 1
        LIMIT = 2
        STOP = 3
        STOP_LIMIT = 4
        _to_str = {MARKET: "MARKET",
                   LIMIT: "LIMIT",
                   STOP: "STOP",
                   STOP_LIMIT: "STOP_LIMIT"}
        @classmethod
        def to_str(cls, val):
            return cls._to_str[val]
    
    class Validiy(object):
        DAY = 1 # Valid for day (default)
        GTC = 3 # Good till cancel
        GTD = 4 # Good till date (Implementation later)
        _to_str = {DAY: 'DAY', GTC: 'GTC', GTD: 'GTD'}
        @classmethod
        def to_str(cls, val):
            return cls._to_str[val]
            
    class FillStrategy(object):
        ALL = 1 # Try to fill all the quantity (default)
        IOC = 2 # Fill as much as possible immediately, cancel the rest
        AON = 3 # All or None
        FOK = 4 # Fill or Kill
        _to_str = {ALL: 'ALL', IOC: 'IOC', FOK: 'FOK', AON: 'AON'}
        @classmethod
        def to_str(cls,val):
            return cls._to_str[val]
            
    # Valid state transitions.
    VALID_TRANSITIONS = {
        State.INITIAL: [State.SUBMITTED, State.CANCELED],
        State.SUBMITTED: [State.ACCEPTED, State.CANCELED, State.REJECTED, State.EXPIRED],
        State.ACCEPTED: [State.PARTIALLY_FILLED, State.FILLED, State.CANCELED, State.REJECTED, State.EXPIRED],
        State.PARTIALLY_FILLED: [State.PARTIALLY_FILLED, State.FILLED, State.CANCELED],
    }

    def __init__(self, order_type, action, security, quantity, 
                 price = None, 
                 stop_price = None, 
                 validity = None,
                 exchange = None,
                 fill_strategy = None,
                 extra = None):
        """
        if quantity <= 0:
            raise ValueError("quantity cannot be negative")
        # Raise error if order type is limit and limit price not given
        if order_type == Order.Type.LIMIT and (not price or price <= 0):
            raise ValueError("price required for Limit orders or limit price cannot be negative")
        # Raise error if order type is stop and stop price not given
        if order_type == Order.Type.STOP and (not stop_price or stop_price <= 0):
            raise ValueError("stop_price required for Stop orders and it cannot be negative or 0")        
        # Raise error if order type is stop limit and either stop price or limit price not given
        if order_type == Order.Type.STOP_LIMIT and (not stop_price or not price or price <= 0 or stop_price <= 0):
            raise ValueError("price and stoptrigger required for the Stop Limit orders or price and stop_price cannot be negetive")
        # Raise error if order type is  Market and limit price or stop price is given
        if order_type == Order.Type.MARKET and (price or stop_price):
            raise ValueError("Do not pass any value in price or stop_price for Market Orders, Allowed values 0 or None ")
        """
        self.id = None
        self.type = order_type
        self.action = action
        self.security = security
        self.quantity = quantity
        self.price = price
        self.stop_price = stop_price
        self.filled = 0
        self.avg_fill_price = None
        if validity:
            self.validity = validity
        else:
            self.validity = Order.Validiy.DAY
        
        if fill_strategy:
            self.fill_strategy = fill_strategy
        else:
            self.fill_strategy = Order.FillStrategy.ALL
        self.commisions = 0
        self.fill_strategy = Order.FillStrategy.ALL
        self.state = Order.State.INITIAL
        self.submit_datetime = None
        self.exchange = exchange
        self.extra = extra
        
    def __getitem__(self,key):
        return self.__dict__[key]
    
    def __setitem__(self,key,value):
        self.__dict__[key] = value
        
        
    def get_id(self):
        """
        Returns the order id.
        .. note::
            This will be None if the order was not submitted.
        """
        return self.id

    def get_type(self):
        """Returns the order type. Valid order types are:
         * Order.Type.MARKET
         * Order.Type.LIMIT
         * Order.Type.STOP
         * Order.Type.STOP_LIMIT
        """
        return self.type

    def get_submit_datetime(self):
        """Returns the datetime when the order was submitted."""
        return self.submit_datetime

    def set_submitted(self, orderId, dateTime):
        if not (self.id is None or orderId == self.id):
            raise Warning('OrderId doesnt match')
        self.id = orderId
        self.submit_datetime = dateTime
        self.state = Order.State.SUBMITTED
        
    def get_action(self):
        """Returns the order action. Valid order actions are:
         * Order.Action.BUY
         * Order.Action.BUY_TO_COVER
         * Order.Action.SELL
         * Order.Action.SELL_SHORT
        """
        return self.action

    def get_state(self):
        """Returns the order state. Valid order states are:
         * Order.State.INITIAL (the initial state).
         * Order.State.SUBMITTED
         * Order.State.ACCEPTED
         * Order.State.CANCELED
         * Order.State.PARTIALLY_FILLED
         * Order.State.FILLED
        """
        return self.state

    def is_active(self):
        """Returns True if the order is active."""
        return self.state not in [Order.State.CANCELED, Order.State.FILLED, Order.State.EXPIRED, Order.State.REJECTED]

    def is_initial(self):
        """Returns True if the order state is Order.State.INITIAL."""
        return self.state == Order.State.INITIAL

    def is_submitted(self):
        """Returns True if the order state is Order.State.SUBMITTED."""
        return self.state == Order.State.SUBMITTED

    def is_accepted(self):
        """Returns True if the order state is Order.State.ACCEPTED."""
        return self.state == Order.State.ACCEPTED

    def is_canceled(self):
        """Returns True if the order state is Order.State.CANCELED."""
        return self.state == Order.State.CANCELED

    def is_partially_filled(self):
        """Returns True if the order state is Order.State.PARTIALLY_FILLED."""
        return self.state == Order.State.PARTIALLY_FILLED

    def is_filled(self):
        """Returns True if the order state is Order.State.FILLED."""
        return self.state == Order.State.FILLED

    def get_security(self):
        """Returns the security identifier."""
        return self.security

    def get_quantity(self):
        """Returns the quantity."""
        return self.quantity

    def get_filled(self):
        """Returns the number of shares that have been executed."""
        return self.filled

    def get_remaining(self):
        """Returns the number of shares still outstanding."""
        return int(self.quantity - self.filled)

    def get_avg_fill_price(self):
        """Returns the average price of the shares that have been executed, or None if nothing has been filled."""
        return self.avg_fill_price

    def get_commissions(self):
        return self.commisions

    def is_good_till_canceled(self):
        """Returns True if the order is good till canceled."""
        return self.validity == Order.Validiy.GTC

    def set_good_till_canceled(self):
        """Sets if the order should be good till canceled.
        Orders that are not filled by the time the session closes will be will be automatically canceled
        if they were not set as good till canceled
        :param goodTillCanceled: True if the order should be good till canceled.
        :type goodTillCanceled: boolean.
        .. note:: This can't be changed once the order is submitted.
        """
        if self.state != Order.State.INITIAL:
            raise Exception("The order has already been submitted")
        self.validity = Order.Validiy.GTC

    def is_all_or_none(self):
        """Returns True if the order should be completely filled or else canceled."""
        return self.fill_strategy == Order.FillStrategy.AON

    def set_all_or_none(self):
        """Sets the All-Or-None property for this order.
        :param allOrNone: True if the order should be completely filled.
        :type allOrNone: boolean.
        .. note:: This can't be changed once the order is submitted.
        """
        if self.state != Order.State.INITIAL:
            raise Exception("The order has already been submitted")
        self.fill_strategy == Order.FillStrategy.AON

    def switch_state(self, new_state):
        valid_transitions = Order.VALID_TRANSITIONS.get(self.state, [])
        if new_state not in valid_transitions:
            raise Exception("Invalid order state transition from %s to %s" % (Order.State.to_str(self.state), Order.State.to_str(new_state)))
        else:
            self.state = new_tate

    def set_state(self, new_state):
        self.state = new_state

    # Returns True if this is a BUY or BUY_TO_COVER order.
    def is_buy(self):
        return self.action in [Order.Action.BUY, Order.Action.BUY_TO_COVER]

    # Returns True if this is a SELL or SELL_SHORT order.
    def is_sell(self):
        return self.action in [Order.Action.SELL, Order.Action.SELL_SHORT]


class Broker(object):
    """Base class for broker implementation
    :param auth: Store authentication data as dictionary object
    :type auth: dict()
    :param prefs: Preferences or settings
    :type prefs: dict()
    .. Note::
        This is a base class, Should not be used directly
    """
    auth = {} 
    def __init__(self, auth, prefs = None):
        pass
    
    def submit_order(self, order):
        pass
    
    def __ip_to_order_type(self, price, stop_price):
        if price > 0 and stop_price > 0:
            order_type = Order.Type.STOP_LIMIT
        elif price > 0:
            order_type = Order.Type.LIMIT
        elif stop_price > 0:
            order_type = Order.Type.STOP
        else:
            order_type = Order.Type.MARKET
        return order_type
        
    def build_buy_order(self, security, quantity,
            price = None, 
            stop_price = None, 
            validity = None,
            exchange = None,
            fill_strategy = None,
            extra = None):
                
        order_type = self.__ip_to_order_type(price, stop_price)
        
        order = Order(order_type = order_type,
                      action = Order.Action.BUY,
                      security = security,
                      quantity = quantity, 
                      price = price, 
                      stop_price = stop_price,
                      validity = validity,
                      exchange = exchange,
                      fill_strategy = fill_strategy,
                      extra = extra)
        return order
    
    def build_sell_order(self, security, quantity,
            price = None, 
            stop_price = None, 
            validity = None,
            exchange = None,
            fill_strategy = None,
            extra = None):
        order_type = self.__ip_to_order_type(price, stop_price)
        order = Order(order_type = order_type,
                      action = Order.Action.SELL,
                      security = security,
                      quantity = quantity, 
                      price = price, 
                      stop_price = stop_price,
                      validity = validity,
                      exchange = exchange,
                      fill_strategy = fill_strategy,
                      extra = extra)
        return order
    
    def get_cash(self):
        pass
    
      
    def get_order_status(self, order_id):
        pass
    
    def cancel_order(self, order_id):
        pass
    
    def modifty_order(self, order_id, security, quantitiy,
            price = None, 
            stop_price = None, 
            validity = None,
            exchange = None,
            fill_strategy = None,
            extra = None):
        pass
    
    def get_all_orders(self):
        pass
    
    def connect(self):
        pass
    
    def disconnect(self):
        pass
    
    def get_quote(self,security):
        pass
    
    def get_market_depth(self, security):
        pass
