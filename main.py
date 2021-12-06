import sys
from binance.client import Client
from binance.streams import BinanceSocketManager
from twisted.internet import reactor
from src import historic_dataset
from src import historic_prices
import csv
from config import *
from datetime import datetime

api_key = ''
api_secret = ''
if TEST_MODE == True:
    api_key = TEST_API_KEY
    api_secret = TEST_API_SECRET
else:
    api_key = API_KEY
    api_secret = API_SECRET

startdate_str = START_DATE_DAY + ' ' + START_DATE_MONTH + ', ' + START_DATE_YEAR

filename = ''
Dataset = historic_dataset.DatasetCreation(api_key, api_secret)
if CREATE_DATASET == True:
    filename = Dataset.createCsvDataset(TRADING_PAIR_FIRST + TRADING_PAIR_SECOND, TIME_INTERVAL, startdate_str, DATASET_FOLDER)
    print('Data successfully written to ' + DATASET_FOLDER + filename + ' in format TOHLCV.')
    del Dataset
else:
    filename = TRADING_PAIR_FIRST + TRADING_PAIR_SECOND + '_' + TIME_INTERVAL + '_' + START_DATE_DAY + '_' + START_DATE_MONTH + '_' + START_DATE_YEAR + '.csv'

BTCUSDT = historic_prices.HistoricPrices(TRADING_PAIR_FIRST + TRADING_PAIR_SECOND, TRADING_PAIR_FIRST_BALANCE, TRADING_PAIR_SECOND_BALANCE)

print('Opening file for reading...')
try:
    with open(DATASET_FOLDER + filename) as dataset_csv:
        csv_reader = csv.reader(dataset_csv, delimiter=',')
        for row in csv_reader:
            BTCUSDT.addTimestamp(datetime.fromtimestamp(float(row[BTCUSDT.TIMESTAMP])/1e3).strftime('%Y-%m-%d %H:%M:%S'))
            BTCUSDT.addOpenPrice(float(row[BTCUSDT.OPEN]))
            BTCUSDT.addHighPrice(float(row[BTCUSDT.HIGH]))
            BTCUSDT.addLowPrice(float(row[BTCUSDT.LOW]))
            BTCUSDT.addClosePrice(float(row[BTCUSDT.CLOSE]))
            BTCUSDT.addVolume(float(row[BTCUSDT.VOLUME]))
except OSError:
    sys.exit('File does not exist. Please create the dataset before trying to open.')

print('CSV reading completed for ' + DATASET_FOLDER + filename)


########################## ALGORITHMS BELOW THIS POINT ##############################
first_pair_amount = (BTCUSDT.secondTradingPairBalance/BTCUSDT.closePrices[1]) * .9999
first_pair_amount = (first_pair_amount * BTCUSDT.closePrices[-1]) * .9999
print('If you bought ' + str(BTCUSDT.secondTradingPairBalance) + ' ' + TRADING_PAIR_SECOND + ' of ' + TRADING_PAIR_FIRST + ' on ' \
    + startdate_str + ' it would now be worth: ' + str(first_pair_amount) + ' ' + TRADING_PAIR_SECOND + '.')
########################## IF YOU BUY AND SELL EVERY INTERVAL ##############################

BTCUSDT.firstTradingPairBalance = 10000/BTCUSDT.closePrices[1]
BTCUSDT.secondTradingPairBalance = 0
for price_index in range(len(BTCUSDT.closePrices)):
    if price_index >=2 and price_index != len(BTCUSDT.closePrices)-1:
        if BTCUSDT.closePrices[price_index] > BTCUSDT.closePrices[price_index-1]:
            BTCUSDT.buyFirstOfSecondValue(50, BTCUSDT.closePrices[price_index], EXCHANGE_FEE)
        elif BTCUSDT.closePrices[price_index] < BTCUSDT.closePrices[price_index-1]:
            BTCUSDT.sellFirstOfSecondValue(50, BTCUSDT.closePrices[price_index], EXCHANGE_FEE)
    elif price_index == len(BTCUSDT.closePrices)-1:
        BTCUSDT.sellFirstOfFirstValue(BTCUSDT.firstTradingPairBalance, BTCUSDT.openPrices[price_index], EXCHANGE_FEE)

print('Final USDT balance is: ' + str(BTCUSDT.secondTradingPairBalance) + ' and final BTC balance is ' \
    + str(BTCUSDT.firstTradingPairBalance))

BTCUSDT.firstTradingPairBalance = 0
BTCUSDT.secondTradingPairBalance = 10000

############################ IF YOU TRADE ON MOVING AVERAGE ##############################



MA_INT1 = 10
MA_INT2 = 50
BTCUSDT.firstTradingPairBalance = 0
BTCUSDT.secondTradingPairBalance = 10000
MAs5 = BTCUSDT.getMovingAverages(BTCUSDT.CLOSE, MA_INT1)
MAs10 = BTCUSDT.getMovingAverages(BTCUSDT.CLOSE, MA_INT2)
five_over_ten = False

print('Before the moving average divergence algorithm I had ' + str(BTCUSDT.firstTradingPairBalance) + ' ' + \
    TRADING_PAIR_FIRST + ' and ' + str(BTCUSDT.secondTradingPairBalance) + ' ' + TRADING_PAIR_SECOND)
for price_index in range(len(MAs10)-1):
    if price_index == MA_INT2:
        if MAs5[price_index] < MAs10[price_index]:
            five_over_ten = False
        elif MAs5[price_index] >= MAs10[price_index]:
            five_over_ten = True
    elif price_index > MA_INT2 and MAs5[price_index] < MAs10[price_index] and five_over_ten == True:
        BTCUSDT.buyFirstOfSecondValue(BTCUSDT.secondTradingPairBalance, BTCUSDT.closePrices[price_index], EXCHANGE_FEE)
        five_over_ten = False            
    elif price_index > MA_INT2 and MAs5[price_index] > MAs10[price_index] and five_over_ten == False:
        BTCUSDT.sellFirstOfFirstValue(BTCUSDT.firstTradingPairBalance, BTCUSDT.closePrices[price_index], EXCHANGE_FEE)
        five_over_ten = True

BTCUSDT.sellFirstOfFirstValue(BTCUSDT.firstTradingPairBalance, BTCUSDT.closePrices[price_index], EXCHANGE_FEE)

print('After the moving average divergence algorithm I have ' + str(BTCUSDT.firstTradingPairBalance) + ' ' + \
    TRADING_PAIR_FIRST + ' and ' + str(BTCUSDT.secondTradingPairBalance) + ' ' + TRADING_PAIR_SECOND)

i = 10
########################################################################################## 
######################### FIND THE HIGHEST PERFORMING MA PAIR ############################
print('Starting MA analysis...')

MA_MIN_INT1 = 13
MA_MIN_INT2 = 15
# MA_INT1 = 20
MA_INT2 = 25
price_arrays = []
for ma_range_2 in range(MA_MIN_INT2, MA_INT2):
    for ma_range_1 in range(MA_MIN_INT1, ma_range_2-1):
        MAs5 = BTCUSDT.getMovingAverages(BTCUSDT.CLOSE, ma_range_1)
        MAs10 = BTCUSDT.getMovingAverages(BTCUSDT.CLOSE, ma_range_2)
        five_over_ten = False
        BTCUSDT.firstTradingPairBalance = 0
        BTCUSDT.secondTradingPairBalance = 10000
        for price_index in range(len(MAs10)-1):
            if price_index == ma_range_2:
                if MAs5[price_index] < MAs10[price_index]:
                    five_over_ten = False
                elif MAs5[price_index] >= MAs10[price_index]:
                    five_over_ten = True
            elif price_index > ma_range_2 and MAs5[price_index] < MAs10[price_index] and five_over_ten == True:
                BTCUSDT.buyFirstOfSecondValue(BTCUSDT.secondTradingPairBalance, BTCUSDT.closePrices[price_index], EXCHANGE_FEE)
                five_over_ten = False            
            elif price_index > MA_INT2 and MAs5[price_index] > MAs10[price_index] and five_over_ten == False:
                BTCUSDT.sellFirstOfFirstValue(BTCUSDT.firstTradingPairBalance, BTCUSDT.closePrices[price_index], EXCHANGE_FEE)
                five_over_ten = True
        BTCUSDT.sellFirstOfFirstValue(BTCUSDT.firstTradingPairBalance, BTCUSDT.closePrices[price_index], EXCHANGE_FEE)
        price_arrays.append([ma_range_1, ma_range_2, str(BTCUSDT.secondTradingPairBalance)])
Dataset.createCSVFromList(TESTRESULTS_FOLDER, "BTCUSDT_MA_RESULTS", price_arrays)
print('MA Analysis finished')



