from keys import api, secret
from pybit.unified_trading import HTTP
import pandas as pd
import ta
from time import sleep

session = HTTP(api_key = api,api_secret = secret)



tp = 0.02
sl = 0.01
timeframe = 5
mode = 1
leverage = 10
qty = 50

def get_balance():
    try:
        resp = session.get_wallet_balance(accountType="CONTRACT", coin="USDT")['result']['list'][0]['coin'][0]['walletBalance']
        resp = float(resp)
        return resp
    except Exception as err:
        print(err)

print(f'Your balance: {get_balance()} USDT')



def get_tickers():
    try:
        resp = session.get_tickers(category="linear")['result']['list']
        symbols = []
        for elem in resp:
            if 'USDT' in elem['symbol'] and not 'USDC' in elem['symbol']:
                symbols.append(elem['symbol'])
        return symbols
    except Exception as err:
        print(err)



def klines(symbol):
    try:
        resp = session.get_kline(
            category='linear',
            symbol=symbol,
            interval=timeframe,
            limit=500
        )['result']['list']
        resp = pd.DataFrame(resp)
        resp.columns = ['Time', 'Open', 'High', 'Low', 'Close', 'Volume', 'Turnover']
        resp = resp.set_index('Time')
        resp = resp.astype(float)
        resp = resp[::-1]
        return resp
    except Exception as err:
        print(err)



def get_positions():
    try:
        resp = session.get_positions(
            category='linear',
            settleCoin='USDT'
        )['result']['list']
        pos = []
        for elem in resp:
            pos.append(elem['symbol'])
        return pos
    except Exception as err:
        print(err)



def get_pnl():
    try:
        resp = session.get_closed_pnl(category="linear", limit=50)['result']['list']
        pnl = 0
        for elem in resp:
            pnl += float(elem['closedPnl'])
        return pnl
    except Exception as err:
        print(err)



def set_mode(symbol):
    try:
        resp = session.switch_margin_mode(
            category='linear',
            symbol=symbol,
            tradeMode=mode,
            buyLeverage=leverage,
            sellLeverage=leverage
        )
        print(resp)
    except Exception as err:
        print(err)



def get_precisions(symbol):
    try:
        resp = session.get_instruments_info(
            category='linear',
            symbol=symbol
        )['result']['list'][0]
        price = resp['priceFilter']['tickSize']
        if '.' in price:
            price = len(price.split('.')[1])
        else:
            price = 0
        qty = resp['lotSizeFilter']['qtyStep']
        if '.' in qty:
            qty = len(qty.split('.')[1])
        else:
            qty = 0

        return price, qty
    except Exception as err:
        print(err)



def place_order_market(symbol, side):
    price_precision = get_precisions(symbol)[0]
    qty_precision = get_precisions(symbol)[1]
    mark_price = session.get_tickers(
        category='linear',
        symbol=symbol
    )['result']['list'][0]['markPrice']
    mark_price = float(mark_price)
    print(f'Placing {side} order for {symbol}. Mark price: {mark_price}')
    order_qty = round(qty/mark_price, qty_precision)
    sleep(2)
    if side == 'buy':
        try:
            tp_price = round(mark_price + mark_price * tp, price_precision)
            sl_price = round(mark_price - mark_price * sl, price_precision)
            resp = session.place_order(
                category='linear',
                symbol=symbol,
                side='Buy',
                orderType='Market',
                qty=order_qty,
                takeProfit=tp_price,
                stopLoss=sl_price,
                tpTriggerBy='Market',
                slTriggerBy='Market'
            )
            print(resp)
        except Exception as err:
            print(err)

    if side == 'sell':
        try:
            tp_price = round(mark_price - mark_price * tp, price_precision)
            sl_price = round(mark_price + mark_price * sl, price_precision)
            resp = session.place_order(
                category='linear',
                symbol=symbol,
                side='Sell',
                orderType='Market',
                qty=order_qty,
                takeProfit=tp_price,
                stopLoss=sl_price,
                tpTriggerBy='Market',
                slTriggerBy='Market'
            )
            print(resp)
        except Exception as err:
            print(err)



def rsi_signal(symbol):
    kl = klines(symbol)
    ema = ta.trend.ema_indicator(kl.Close, window=200)
    rsi = ta.momentum.RSIIndicator(kl.Close).rsi()
    if rsi.iloc[-3] < 30 and rsi.iloc[-2] < 30 and rsi.iloc[-1] > 30:
        return 'up'
    if rsi.iloc[-3] > 70 and rsi.iloc[-2] > 70 and rsi.iloc[-1] < 70:
        return 'down'
    else:
        return 'none'


def williamsR(symbol):
    kl = klines(symbol)
    w = ta.momentum.WilliamsRIndicator(kl.High, kl.Low, kl.Close, lbp=24).williams_r()
    ema_w = ta.trend.ema_indicator(w, window=24)
    if w.iloc[-1] < -99.5:
        return 'up'
    elif w.iloc[-1] > -0.5:
        return 'down'
    elif w.iloc[-1] < -75 and w.iloc[-2] < -75 and w.iloc[-2] < ema_w.iloc[-2] and w.iloc[-1] > ema_w.iloc[-1]:
        return 'up'
    elif w.iloc[-1] > -25 and w.iloc[-2] > -25 and w.iloc[-2] > ema_w.iloc[-2] and w.iloc[-1] < ema_w.iloc[-1]:
        return 'down'
    else:
        return 'none'



max_pos = 50
symbols = get_tickers()


# while True:
#     balance = get_balance()
#     if balance == None:
#         print('Cant connect to API')
#     if balance != None:
#         balance = float(balance)
#         print(f'Balance: {balance}')
#         pos = get_positions()
#         print(f'You have {len(pos)} positions: {pos}')
#
#         if len(pos) < max_pos:
#             for elem in symbols:
#                 pos = get_positions()
#                 if len(pos) >= max_pos:
#                     break
#                 signal = rsi_signal(elem)
#                 if signal == 'up':
#                     print(f'Found BUY signal for {elem}')
#                     set_mode(elem)
#                     sleep(2)
#                     place_order_market(elem, 'buy')
#                     sleep(5)
#                 if signal == 'down':
#                     print(f'Found SELL signal for {elem}')
#                     set_mode(elem)
#                     sleep(2)
#                     place_order_market(elem, 'sell')
#                     sleep(5)
#     print('Waiting 2 mins')
#     sleep(120)