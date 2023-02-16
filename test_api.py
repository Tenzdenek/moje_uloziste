

#api only for reed
apikey='9jx20rVWns0WlEyU7lzJKdBGTxYK7qPqbX09cPnkNMjG17er3hTyM3mcAoCqzGN0'
secret='Xi3MgBOMKnYriwJ2ek6NuDlv1cTeqaGkRyMO9K0twtmdYlQbZF4nfbz1u3v1Gqlb'

import sys
from io import StringIO
from functools import total_ordering
from lib2to3.pgen2.token import PERCENT
from pickle import TRUE
from sqlite3 import Time
from binance import Client, ThreadedWebsocketManager, ThreadedDepthCacheManager  
import pandas as pd
import datetime as date
import mplfinance as mpf
import time
import kivymd
import kivy

from kivy.config import Config
Config.set('kivy', 'exit_on_escape', '0')
from kivymd.app import MDApp
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock
from kivy.lang import Builder
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRectangleFlatButton
from kivy.properties import ObjectProperty


def MACD(symbol,leverage,Quantity,TP1,TP2,SL):
    
    global Long, Short, ema_decision, calculate_TP, Fast, Slow, smooting, long_position_side, short_position_side
    global long_side, short_side
    global i
    #kazdy indikator potrebuje jiny casovy horizont pro vzpocet
    last_40_day=date.datetime.now() - date.timedelta(days=40)
    last_2_day=date.datetime.now() - date.timedelta(days=2)
    date_for_2hourEMA=last_40_day.strftime("%d %b %Y")
    date_for_MACD=last_2_day.strftime("%d %b %Y")
    
    

    try:
        Binance_client=Client(apikey,secret)
        response = Binance_client.get_account(recvWindow=5000)
        tickers=Binance_client.get_all_tickers()
        info = Binance_client.get_symbol_info(symbol)
        tickers_df=pd.DataFrame(tickers)
        tickers_df.set_index('symbol',inplace=True)
         # Get the ticker price for the symbol
        ticker = Binance_client.get_symbol_ticker(symbol=symbol)
        # Extract the current price from the ticker
        price = float(ticker['price'])
        change_leverage=Binance_client.futures_change_leverage(symbol=symbol, leverage=leverage, is_isolated= True)
    except Exception as e:
        # Print an error message with the exception type and message
        print(f"An error occurred: {type(e).__name__}: {str(e)}")
        print(f"Connection error: {e}")
        print("Will try again in 10 seconds...")
        time.sleep(10)
    

        
    

    

    

    
    
    try:
        #get Historical data  btc of 15minute(1minute for test)
        historical15m=Binance_client.get_historical_klines(symbol,Client.KLINE_INTERVAL_15MINUTE,date_for_MACD)
        hist_df_15m=pd.DataFrame(historical15m)
        hist_df_15m.columns=['Open Time','Open','High','low','Close','Volume','Close Time','Quote Asset Volume','Number of Trades','Base Volume','Quote Volume','ignor']
        
        historical_3_klines=Binance_client.get_historical_klines(symbol,Client.KLINE_INTERVAL_15MINUTE,limit=4)
        last_3_klines= pd.DataFrame( historical_3_klines)
        
        last_3_klines.columns=['Open Time','Open','High','low','Close','Volume','Close Time','Quote Asset Volume','Number of Trades','Base Volume','Quote Volume','ignor']
        last_3_klines = last_3_klines.drop(last_3_klines.index[-1])
        last_3_klines['Close'] = pd.to_numeric(last_3_klines['Close'])
        percent_change = last_3_klines['Close'].pct_change() * 100
        total_change = percent_change.tail(3).sum()
        if total_change<0:
            total_change=total_change*(-1)
        
        hist_df_15m['MA_Fast']=hist_df_15m['Close'].ewm(span=Fast,adjust=False).mean()
        hist_df_15m['MA_Slow']=hist_df_15m['Close'].ewm(span=Slow,adjust=False).mean()
        hist_df_15m['macd']=hist_df_15m['MA_Fast']-hist_df_15m['MA_Slow']
        hist_df_15m['signal']=hist_df_15m['macd'].ewm(span=smooting,adjust=False).mean()
    
       
        #math MACD and recognize if short or long
        Last_MACD=hist_df_15m['macd'].tail(1)
        Last_Signal=hist_df_15m['signal'].tail(1)

        global is_ma12_higher

        if symbol not in is_ma12_higher.keys():
            is_ma12_higher[symbol]=False
        print(symbol) 
        
        if TP2<=3:
            volatility=0.5
        elif TP2 <=4.5:
            volatility=1
        elif TP2<=7:
            volatility=2
        elif TP2>7:
            volatility=2.5



        if Last_MACD.item() > Last_Signal.item() and is_ma12_higher[symbol]==False and total_change<volatility :
            if i==len(is_ma12_higher):#podle poctu minic(1mince=2)
                print("Long MACD")
                Long=1
                is_ma12_higher[symbol] = True
            elif i<len(is_ma12_higher):
                is_ma12_higher[symbol] = True
                i=i+1
    
        if Last_MACD.item() < Last_Signal.item() and is_ma12_higher[symbol]==True and total_change<volatility :
            if i==len(is_ma12_higher):#podle poctu minic(1mince=2)
                print("Short MACD")
                Short=1
                is_ma12_higher[symbol] = False
            elif i<len(is_ma12_higher):
                is_ma12_higher[symbol] = False
                i=i+1
    except Exception as e:
        # Print an error message with the exception type and message
        print(f"An error occurred: {type(e).__name__}: {str(e)}")
        print(f"Connection error: {e}")
        print("Will try again in 11 seconds...")
        time.sleep(11)
        
#get Historical data  btc of 2hour
    try:
        historical_2hour=Binance_client.get_historical_klines(symbol,Client.KLINE_INTERVAL_2HOUR,date_for_2hourEMA)
        hist_df_2hour=pd.DataFrame(historical_2hour)
        hist_df_2hour.columns=['Open Time','Open','High','low','Close','Volume','Close Time','Quote Asset Volume','Number of Trades','Base Volume','Quote Volume','ignor']

        hist_df_2hour['200hourEWM'] = hist_df_2hour['Close'].ewm(span=200, adjust=False).mean()
        EMA200=hist_df_2hour.loc[:,"200hourEWM"]
        lastEMA200=EMA200.tail(1)
    
        if price> lastEMA200.item():
            
            ema_decision="true"
        else:
            
            ema_decision="false"
    except Exception as e:
        # Print an error message with the exception type and message
        print(f"An error occurred: {type(e).__name__}: {str(e)}")
        print(f"Connection error: {e}")
        print("Will try again in 12 seconds...")
        time.sleep(12)
    
            
    
    try:
        positions = Binance_client.futures_position_information()
        symbolbalance=0
        for position in positions:
            if position['symbol'] == symbol:
                # check if the position is open or not
    
                if float(position['positionAmt']) != 0:
                
                    symbolbalance=(f"{position['positionAmt']}")
                    symbolbalance=float(symbolbalance)
    except Exception as e:
        # Print an error message with the exception type and message
        print(f"An error occurred: {type(e).__name__}: {str(e)}")
        print(f"Connection error: {e}")
        print("Will try again in 13 seconds...")
        time.sleep(13)             
       
    if Long==1 and ema_decision=="true":
        print("Long")
            
            

        # Calculate how much i want buy
        buy_quantity = Quantity / price
            
        #pocet desetinnych mist pro urzu
        price_precision = 2
        quantity_precision = 2
                    
        #prevedeni mnozstvi na format pro burzu
        amount_str = "{:0.0{}f}".format( buy_quantity, quantity_precision)
        try:
            if symbolbalance==0:
                Binance_client.futures_create_order(
                symbol=symbol,
                type='MARKET',
                side=Binance_client.SIDE_BUY,
                positionSide='LONG',
                quantity=amount_str,
            
                )
                calculate_TP="true"
            elif symbolbalance<0 or symbolbalance>0:
                print(f"{symbol} position is open. Position side: {position['positionSide']}, Position amount: {position['positionAmt']}, Unrealized profit: {position['unRealizedProfit']}")
                Long=0
                Short=0
        except Exception as e:
            # Print an error message with the exception type and message
            print(f"An error occurred: {type(e).__name__}: {str(e)}")

    elif Short==1 and ema_decision=="false":
        print("Short")
            
            
        # Calculate how much i want buy
        buy_quantity = Quantity / price
            
        #pocet desetinnych mist pro urzu
        price_precision = 2
        quantity_precision = 2
                    
        #prevedeni mnozstvi na format pro burzu
        amount_str = "{:0.0{}f}".format( buy_quantity, quantity_precision)
        try:
            if symbolbalance==0:
                Binance_client.futures_create_order(
                symbol=symbol,
                type='MARKET',
                side=Binance_client.SIDE_SELL,
                positionSide='SHORT',
                quantity=amount_str,
                
                )
                calculate_TP="true"
            elif symbolbalance<0 or symbolbalance>0:
                print(f"{symbol} position is open. Position side: {position['positionSide']}, Position amount: {position['positionAmt']}, Unrealized profit: {position['unRealizedProfit']}")
                Long=0
                Short=0
        except Exception as e:
            # Print an error message with the exception type and message
            print(f"An error occurred: {type(e).__name__}: {str(e)}")
            print(f"Connection error: {e}")
            print("Will try again in 60 seconds...")
            time.sleep(60)
            

    elif Long==1 and ema_decision=="false" or Short==1 and ema_decision=="true":
        Long==0
        Short==0

        

    if calculate_TP=="true" and Long==1:
        try:    
            price_TP1=(price/100)*(100+TP1)
            price_TP2=(price/100)*(100+TP2)
            price_SL=(price/100)*(100-SL)

            #prevedeni limitek na format pro burzu
            TP1_limit_str="{:0.0{}f}".format( price_TP1 ,price_precision )
            TP2_limit_str="{:0.0{}f}".format( price_TP2, price_precision)
            SL_limit_str="{:0.0{}f}".format( price_SL, price_precision)
            #vypocitani mnostvi pro prodej
            TP1_quantity= (Quantity / price_TP1)/2
            TP2_quantity= Quantity / price_TP2
            SL_quantity= Quantity / price_SL
            #prevedeni mnozstvi na format pro burzu
            TP1_amount_str="{:0.0{}f}".format( TP1_quantity, quantity_precision)
            TP2_amount_str="{:0.0{}f}".format( TP2_quantity/2, quantity_precision)
            SL_amount_str="{:0.0{}f}".format( SL_quantity, quantity_precision)
        

            tp1_order= Binance_client.futures_create_order(
                                                symbol= symbol,
                                                side=short_side,
                                                positionSide= long_position_side,
                                                type='TAKE_PROFIT_MARKET',
                                                quantity= TP1_amount_str,
                                                stopPrice= TP1_limit_str,
                                                
                                                
            )

            tp2_order= Binance_client.futures_create_order(
                                                    symbol= symbol,
                                                side=short_side,
                                                positionSide= long_position_side,
                                                type='TAKE_PROFIT_MARKET',
                                                quantity= TP2_amount_str,
                                                stopPrice= TP2_limit_str,
                                                
            )                                  
            sl_order = Binance_client.futures_create_order(
                                                symbol= symbol,
                                                side=short_side,
                                                positionSide= long_position_side,
                                                type='STOP_MARKET',
                                                quantity= SL_amount_str,
                                                stopPrice= SL_limit_str,
                                                closePosition=True,
                                                
                                                            )
        except Exception as e:
            # Print an error message with the exception type and message
            print(f"An error occurred: {type(e).__name__}: {str(e)}")
        Long=0
        print(Time)
        print("Long at price:",price)
        print("TP1:",price_TP1)
        print("TP2:",price_TP2)
        print("SL:",price_SL)
        calculate_TP="false"

    if calculate_TP=="true" and Short==1:
        try:
            
            price_TP1=(price/100)*(100-TP1)
            price_TP2=(price/100)*(100-TP1)
            price_SL=(price/100)*(100+SL)
            
            TP1_limit_str="{:0.0{}f}".format( price_TP1 ,price_precision )
            TP2_limit_str="{:0.0{}f}".format( price_TP2, price_precision)
            SL_limit_str="{:0.0{}f}".format( price_SL, price_precision)
            

            

            TP1_quantity= (Quantity / price_TP1)/2
            TP2_quantity= Quantity / price_TP2
            SL_quantity= Quantity / price_SL

            TP1_amount_str="{:0.0{}f}".format( TP1_quantity, quantity_precision)
            
            TP2_amount_str="{:0.0{}f}".format( TP2_quantity/2, quantity_precision)
            SL_amount_str="{:0.0{}f}".format( SL_quantity, quantity_precision)
            # place the take-profit and stop-loss orders
        

            tp1_order= Binance_client.futures_create_order(
                                                symbol= symbol,
                                                side=long_side,
                                                positionSide= short_position_side,
                                                type='TAKE_PROFIT_MARKET',
                                                quantity= TP1_amount_str,
                                                stopPrice= TP1_limit_str,
                                                
                                                
            )

            tp2_order= Binance_client.futures_create_order(
                                                    symbol= symbol,
                                                side=long_side,
                                                positionSide= short_position_side,
                                                type='TAKE_PROFIT_MARKET',
                                                quantity= TP2_amount_str,
                                                stopPrice= TP2_limit_str,
                                                
            )                                  
            sl_order = Binance_client.futures_create_order(
                                                symbol= symbol,
                                                side=long_side,
                                                positionSide= short_position_side,
                                                type='STOP_MARKET',
                                                quantity= SL_amount_str,
                                                stopPrice= SL_limit_str,
                                                closePosition=True,
                                                
                                                            )
        except Exception as e:
            # Print an error message with the exception type and message
            print(f"An error occurred: {type(e).__name__}: {str(e)}")                                               
        Short=0
        print(Time)
        print("short at price:"+ str(price ))
        print("TP1:"+str(price_TP1))
        print("TP2:"+str(price_TP2))
        print("SL:",price_SL)
        calculate_TP="false"

#POT5EBN0 KONSTANTZ A PROM2NN0
opak=1
i=1
symbols = ['BTCUSDT']
is_ma12_higher = {symbol: False for symbol in symbols}
 
print( is_ma12_higher)

Long=0
Short=0
ema_decision=""
calculate_TP=""
Fast=48
Slow=104
smooting=9


long_position_side='LONG'
short_position_side='SHORT'
long_side='BUY'
short_side='SELL'
   
    
    
kv = """
<RootWidget>:
    orientation: "vertical"
    MDLabel:
        id: time_label
        text: "00:00:00"
        halign: "center"
        font_style: "H5"
    MDRectangleFlatButton:
        id: start_button
        text: "Start"
        pos_hint: {"center_x": 0.5, "center_y": 0.5}
        on_press: root.start()
    MDRectangleFlatButton:
        id: stop_button
        text: "Stop"
        pos_hint: {"center_x": 0.5, "center_y": 0.4}
        on_press: root.stop()
    BoxLayout:
        orientation: 'vertical'
        ScrollView:
            TextInput:
                id: console_output
                size_hint_y: None
                height: self.minimum_height
                readonly: True
                background_color: 0, 0, 0, 0
                foreground_color: 0, 1, 0, 1
                font_size: '15sp'
        TextInput:
            id: console_input
            size_hint_y: None
            height: '48dp'
            foreground_color: 0, 1, 0, 1
            on_text_validate: root.execute_console_command(self.text)
"""
    




    



class RootWidget(BoxLayout):
    console_output = ObjectProperty()
    def __init__(self, **kwargs):
        
        super(RootWidget, self).__init__(**kwargs)
        self.time_label = self.ids.time_label
        self.start_button = self.ids.start_button
        self.stop_button = self.ids.stop_button
        self.event = None
        self.output_buffer = StringIO()
        self.console_output = self.ids.console_output
        self.console_input = self.ids.console_input
        sys.stdout = self.output_buffer


    def start(self):
        self.console_input.text = "Started\n"
        self.my_function(None)
        self.event = Clock.schedule_interval(self.my_function, 900)

    def stop(self):
        if self.event is not None:
            self.event.cancel()
        self.console_input.text += "Stopped\n"  

    
    def execute_console_command(self, command):
        self.console_input.text = ''
        try:
            exec(command)
        except Exception as e:
            print(e)
        self.console_output.text = self.output_buffer.getvalue()
        self.output_buffer.truncate(0)
        self.console_output.scroll_y = 0
        
    def my_function(self, dt):
        
        #ziskani aktualniho casu 
        localtime = time.localtime()
        Time = time.strftime("%H:%M", localtime)
        result = time.strftime("%M", localtime)
        second=time.strftime("%S", localtime)
        now = date.datetime.now()
    
        

        
        self.time_label.text = Time
        
            
        result = MACD('BTCUSDT',4,70,1.5,2,0.5)
        result = MACD('ETHUSDT',4,60,2.3,3,0.75)
        result = MACD('LTCUSDT',4,30.5,5,7,1.5)
        result = MACD('DOGEUSDT',4,30,5,7,1.5)
        result = MACD('AVAXUSDT',2,40,5.5,7.5,1.9)
        result = MACD('LINKUSDT',4,30,5.5,6.5,1.5)
        result = MACD('LDOUSDT',2,30,7,10,2.5)
        result = MACD('APEUSDT',4,30,5,7,1.5)
        result = MACD('AXSUSDT',3,28,6,8,2)
        result = MACD('CRVUSDT',4,30,4,4.5,1.5)
        result = MACD('MATICUSDT',4,35,3.5,4.5,1.2)
        self.console_output.text = self.output_buffer.getvalue()        
        print(time)
        opak=0
class MyBoxLayout(BoxLayout):
    def on_enter(self, value):
        print(value)        

class MyApp(MDApp):
    def build(self):
        Builder.load_string(kv)
        return RootWidget()
            

if __name__ == '__main__':
    MyApp().run()