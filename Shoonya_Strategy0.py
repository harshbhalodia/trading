import datetime
import time
import threading
import requests
from NorenRestApiPy.NorenApi import NorenApi
#import dill
import Login_API # login python file

######PIVOT POINTS##########################
####################__INPUT__#####################
isEnd = False
class ShoonyaApiPy(NorenApi):
    def __init__(self):
        NorenApi.__init__(self, host='https://api.shoonya.com/NorenWClientTP/',
                          websocket='wss://api.shoonya.com/NorenWSTP/',
                          eodhost='https://api.shoonya.com/chartApi/getdata/')

#EITHER THIS
#api = ShoonyaApiPy()
#with open ('api.dill', 'rb') as fp:
#    api = dill.load(fp)
#    print(api)

#OR THIS
api = Login_API.api

#TIME TO FIND THE STRIKE
entryHour   = 0
entryMinute = 0
entrySecond = 0


stock="NIFTY" # BANKNIFTY OR NIFTY
otm = 500  #If you put -100, that means its 100 points ITM.
SL_percentage = 0.4
target_percentage = 1.2
yesterday_closing_price = 17530


expiry ={
    "year": "23",
    "month": "FEB",
    "day": "16",
    #YYMDD  22O06  22OCT
}
clients = [
    {
        "broker": "shoonya",
        "userID": "",
        "apiKey": "",
        "accessToken": "",
        "qty" : 50
    }
]


##################################################


def findStrikePriceATM(cepe, sl_fut, target_fut):
    global kc
    global clients
    global SL_percentage

    if stock == "BANKNIFTY":
        name = "Nifty Bank"   #"NSE:NIFTY BANK"
    elif stock == "NIFTY":
        name = "Nifty 50"       #"NSE:NIFTY 50"
    #TO get feed to Nifty: "NSE:NIFTY 50" and banknifty: "NSE: NIFTY BANK"

    strikeList=[]

    prev_diff = 10000
    closest_Strike=10000

    intExpiry=expiry["day"]+expiry["month"]+expiry["year"]   #22SEP

    ######################################################
    #FINDING ATM
    ltp = float(getLTP("NSE",name))
    if stock == "BANKNIFTY":
        closest_Strike = int(round((ltp / 100),0) * 100)
        print(closest_Strike)

    elif stock == "NIFTY":
        closest_Strike = int(round((ltp / 50),0) * 50)
        print(closest_Strike)

    print("closest",closest_Strike)

    closest_Strike_CE = closest_Strike+otm
    closest_Strike_PE = closest_Strike-otm

    if stock == "BANKNIFTY":
        atmCE = "BANKNIFTY" + str(intExpiry)+"C"+str(closest_Strike_CE)
        atmPE = "BANKNIFTY" + str(intExpiry)+"P"+str(closest_Strike_PE)
    elif stock == "NIFTY":
        atmCE = "NIFTY" + str(intExpiry)+"C"+str(closest_Strike_CE)
        atmPE = "NIFTY" + str(intExpiry)+"P"+str(closest_Strike_PE)

    print(atmCE)
    print(atmPE)

    if cepe == "CE":
        takeEntry(closest_Strike_CE, atmCE, sl_fut, target_fut, name, cepe)
    else:
        takeEntry(closest_Strike_PE, atmPE, sl_fut, target_fut, name, cepe)


def takeEntry(closest_Strike, atmCEPE, sl_fut, target_fut, name, cepe):
    global SL_point
    cepe_entry_price = getLTP("NFO",atmCEPE)
    print(" closest ATM ", closest_Strike, " CE Entry Price = ", cepe_entry_price)

    #SELL AT MARKET PRICE
    for client in clients:
        print("\n============_Placing_Trades_=====================")
        print("userID = ", client['userID'])
        broker = client['broker']
        uid = client['userID']
        key = client['apiKey']
        token = client['accessToken']
        qty = client['qty']

        #oidentryCE = 0
        #oidentryPE = 0

        oidentry = placeOrderShoonya( atmCEPE, "SELL", qty, "MARKET", cepe_entry_price, "regular")

        print("The OID of Entry is: ", oidentry)
        exitPosition(atmCEPE, sl_fut, target_fut, qty, name, cepe)


def exitPosition(atmCEPE, sl_fut, target_fut, qty, name, cepe):
    traded = "No"

    while traded == "No":
        dt = datetime.datetime.now()
        try:
            ltp = getLTP("NFO",name)

            #if LTP (Nifty) < s1, then we are going to sell CE. Future = SELL
            if (cepe == "CE"):
                if ((ltp < target_fut) or (ltp > sl_fut) or (dt.hour >= 15 and dt.minute >= 15)) and ltp != -1:
                    oidexitCE = placeOrderShoonya( atmCEPE, "BUY", qty, "MARKET", 0, "regular")
                    print("The OID of Exit is: ", oidexitCE)
                    traded = "Close"
                else:
                    time.sleep(1)
            #if LTP (Nifty) > r1, then I am going to Sell PE. Future = LONG / BUY
            else:
                if ((ltp > target_fut) or (ltp < sl_fut) or (dt.hour >= 15 and dt.minute >= 15)) and ltp != -1:
                    oidexitCE = placeOrderShoonya( atmCEPE, "BUY", qty, "MARKET", 0, "regular")
                    print("The OID of Exit is: ", oidexitCE)
                    traded = "Close"
                else:
                    time.sleep(1)
            time.sleep(30)

        except:
            print("Couldn't find LTP , RETRYING !!")
            time.sleep(1)



def getLTP(exch,token):
    try:

        ret = api.get_quotes(exchange=exch, token=token)
        return float(ret['lp'])

    except Exception as e:
        print(token , "Failed : {} ".format(e))


def checkTime_tofindStrike():
    x = 1
    while x == 1:
        dt = datetime.datetime.now()
        if( dt.hour >= entryHour and dt.minute >= entryMinute and dt.second >= entrySecond ):
            print("time reached")
            x = 2
            while not isEnd:
                takeEntryFut()
                time.sleep(1)
            #findStrikePriceATM()
        else:
            time.sleep(.1)
            print(dt , " Waiting for Time to check new ATM ")


def takeEntryFut():
    global isEnd
    global kc
    global clients
    global SL_percentage
    global target_percentage

    if stock == "BANKNIFTY":
        name = "Nifty Bank"
        yesterdayHigh = 37638
        yesterdayLow = 37291
        yesterdayClose = 37335
    elif stock == "NIFTY":
        name = "Nifty 50"
        yesterdayHigh = 17176.45
        yesterdayLow = 16942.35
        yesterdayClose = 17007.4

    time=datetime.datetime.now()
    minute = time.strftime("%M")
    second = time.strftime("%S")

    pp = (yesterdayHigh + yesterdayLow + yesterdayClose)/3
    r1 = (pp * 2) - yesterdayLow
    s1 = (pp * 2) - yesterdayHigh
    print(r1)
    print(s1)

    if int(minute)%5 ==0 and int(second) ==0 :
        print("This is every fifth minute", minute)
        ltp = getLTP("NSE",name)

        if ltp > r1:
            sl_fut = round(ltp*(1-SL_percentage/100),1)
            target_fut = round(ltp*(1+target_percentage/100),1)
            findStrikePriceATM("PE", sl_fut, target_fut)
            isEnd = True
        elif ltp < s1:
            sl_fut = round(ltp*(1+SL_percentage/100),1)
            target_fut = round(ltp*(1-target_percentage/100),1)
            findStrikePriceATM("CE", sl_fut, target_fut)
            isEnd = True


def placeOrderShoonya(inst, buy_or_sell, qty, order_type, price, amo):
    global api
    exch = "NFO"
    symb = inst
    paperTrading = 1 #if this is 0, then real trades will be placed
    if( buy_or_sell=="BUY"):
        buy_or_sell="B"
    else:
        buy_or_sell="S"

    if(order_type=="MARKET"):
        order_type="MKT"
    elif(order_type=="LIMIT"):
        order_type="LMT"

    try:
        if(paperTrading == 0):
            order_id = api.place_order(buy_or_sell=buy_or_sell,  #B, S
                                       product_type="I", #C CNC, M NRML, I MIS
                                       exchange=exch,
                                       tradingsymbol=symb,
                                       quantity = qty,
                                       discloseqty=qty,
                                       price_type= order_type, #LMT, MKT, SL-LMT, SL-MKT
                                       price = price,
                                       trigger_price=price,
                                       amo=amo,#YES, NO
                                       retention="DAY"
                                       )
            print(" => ", symb , order_id['norenordno'] )
            return order_id['norenordno']

        else:
            order_id=0
            return order_id

    except Exception as e:
        print(" => ", symb , "Failed : {} ".format(e))



checkTime_tofindStrike()