from ibapi.client import EClient
from ibapi.wrapper import EWrapper

import threading
import time
import numpy as np
import datetime as datetime
import pandas as pd


from ibapi.contract import Contract
from ibapi.client import MarketDataTypeEnum
from ibapi.order import *
from ibapi.utils import iswrapper


import matplotlib.pyplot as plt


historical_stock_name = input('Enter real time stock: ')


class IBApi(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self)
        self.real_time_prices = []
        self.historical_time_data = []
        self.nextOrderId = None

    def tickPrice(self, reqId, tickType, price, attrib):
        if reqId == 1:
            self.real_time_prices.append(price)

    def historicalData(self, reqId, bar):
        self.historical_time_data.append([bar.date, bar.close])

    def orderStatus(self, orderId, status, filled, remaining, avgFillPrice, permId, parentId, lastFillPrice, clientId, whyHeld, mktCapPrice):
        print('orderStatus - orderid:', orderId, 'status:', status, 'filled',
              filled, 'remaining', remaining, 'lastFillPrice', lastFillPrice)

    def openOrder(self, orderId, contract, order, orderState):
        print('openOrder id:', orderId, contract.symbol, contract.secType, '@', contract.exchange,
              ':', order.action, order.orderType, order.totalQuantity, orderState.status)

    def execDetails(self, reqId, contract, execution):
        print('Order Executed: ', reqId, contract.symbol, contract.secType, contract.currency,
              execution.execId, execution.orderId, execution.shares, execution.lastLiquidity)

    @iswrapper
    def nextValidId(self, orderId):
        super().nextValidId(orderId)
        self.nextOrderId = orderId
        print('Next order id: ', self.nextOrderId)


app = IBApi()
app.connect('127.0.0.1', 4002, 123)


def run_loop():
    app.run()


api_thread = threading.Thread(target=run_loop, daemon=True)
api_thread.start()


time.sleep(3)


# Real time data
apple_market_contract = Contract()
apple_market_contract.symbol = historical_stock_name
apple_market_contract.secType = 'STK'
apple_market_contract.exchange = 'SMART'
apple_market_contract.currency = 'USD'


app.reqMarketDataType(MarketDataTypeEnum.DELAYED)
app.reqMktData(1, apple_market_contract, '', False, False, [])


time.sleep(10)


# Plotting real time data
real_time_prices_formatted = [
    price for price in app.real_time_prices if price != 0]
plt.plot(real_time_prices_formatted)
plt.title('Real time data')
plt.legend(['Price'])
plt.xlabel('Ticks')
plt.ylabel('Price')
plt.xticks(np.arange(1, len(real_time_prices_formatted)))
plt.show()


# Historical data
eurusd_historical = Contract()
eurusd_historical.symbol = 'EUR'
eurusd_historical.secType = 'CASH'
eurusd_historical.exchange = 'IDEALPRO'
eurusd_historical.currency = 'USD'


app.reqHistoricalData(1, eurusd_historical, '', '2 D',
                      '1 hour', 'BID', 0, 2, False, [])

time.sleep(3)

# Plotting historical data
df = pd.DataFrame(app.historical_time_data, columns=['Date', 'Close'])
df['Date'] = pd.to_datetime(df['Date'], unit='s')
print(df.head())

plt.plot(df['Date'], df['Close'])
plt.title('Historical data')
plt.legend(['Price'])
plt.xlabel('Date')
plt.ylabel('Price')
plt.show()


order_amount = input('How many would you like to order?')
order_price = input('At what price?')

# Orders
while True:
    if isinstance(app.nextOrderId, int):
        break
    else:
        time.sleep(1)


order = Order()
order.action = 'BUY'
order.totalQuantity = int(order_amount)
order.orderType = 'LMT'
order.lmtPrice = float(order_price)

order_contract = Contract()
order_contract.symbol = 'EUR'
order_contract.secType = 'CASH'
order_contract.exchange = 'IDEALPRO'
order_contract.currency = 'USD'

app.placeOrder(app.nextOrderId, order_contract, order)


time.sleep(4)


app.cancelOrder(app.nextOrderId)


time.sleep(10)


input('Exit?')


app.disconnect()
