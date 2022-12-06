#Чистый привод для долгих позиций
import pandas as pd
from binance.client import Client
from binance.helpers import round_step_size
import info
import asyncio
from discord.ext import commands
import discord


client = Client(api_key=info.api, api_secret=info.secret_api, testnet=False)
DS = commands.Bot(command_prefix='/', intents = discord.Intents.all())
DS.remove_command("help")

def get_qsize(symbol):
    info = client.futures_exchange_info()
    for item in info['symbols']:
        if(item['symbol'] == symbol):
            for f in item['filters']:
                if f['filterType'] == 'LOT_SIZE':
                    return f['stepSize']

def get_pricesize(symbol):
    info = client.futures_exchange_info()
    for item in info['symbols']:
        if(item['symbol'] == symbol):
            for f in item['filters']:
                if f['filterType'] == 'PRICE_FILTER':
                    return f['tickSize']

for i in info.tokens:
        try:
            client.futures_change_margin_type(symbol=i, marginType='ISOLATED')
        except:
            continue

pos_list = {}

class Position:
    async def new_position(self, side, symbol, price, stopl, takep):
        print('OK')
        if side == "BUY":
            self.close_side = "SELL"
        else:
            self.close_side = "BUY"

        self.symbol = symbol

        #calculating quaintity
        b=client.futures_account_balance()
        b = pd.DataFrame.from_dict(b)
        b = b.loc[b['asset']=='USDT']
        balance = float(b['balance'].values) * 0.05
        q = balance / price * info.laverage

        #rounding
        q_size = get_qsize(symbol)
        price_size = get_pricesize(symbol)
        self.q = round_step_size(q, q_size)

        #opening order
        client.futures_change_leverage(symbol=symbol, leverage=info.laverage)
        buyorder = client.futures_create_order(symbol=self.symbol, side=side, type="MARKET", quantity=self.q, isIsolated='TRUE')
        self.stop = client.futures_create_order(symbol=self.symbol, side=self.close_side, type="STOP_MARKET", stopPrice=round_step_size(float(stopl), float(price_size)), closePosition="true")
        self.take = client.futures_create_order(symbol=self.symbol, side=self.close_side, type="TAKE_PROFIT_MARKET", stopPrice=round_step_size(float(takep), float(price_size)), closePosition="true")
        
        #monitoring
        a = True
        while a == True:
            await asyncio.sleep(1.8)
            orders = client.futures_get_open_orders(symbol=self.symbol)
            if len(orders) == 1:
                try:
                    client.futures_cancel_order(symbol=self.symbol, orderId=self.take['orderId'], timestamp='true')
                    a = False
                except:
                    a = False
    



@DS.event
async def on_message(ctx):
    global pos_list
    raw_data = ctx.content.split()
    if raw_data[0] == "/open":
        loop = asyncio.get_event_loop()
        position = Position()
        loop.create_task(position.new_position(raw_data[1], raw_data[2].replace("PERP", ""), float(raw_data[3]), float(raw_data[4]), float(raw_data[5])))
        pos_list[raw_data[2]] = position
        print(pos_list)

DS.run(info.discord_token)
