import os 
import sys
from typing_extensions import ParamSpecKwargs
from binance.client import Client
from binance.streams import BinanceSocketManager
from twisted.internet import reactor
import time
import smtplib
import csv

class DatasetCreation:
    def __init__(self, api_key, api_secret):
        self.api_key = api_key
        self.api_secret = api_secret
        self.client = Client(api_key, api_secret)

    def createCSVFromList(self, folder, filename, data): # Will write the CSV as titles on the first row, and the data accordingly
        with open(folder+filename, 'w', newline='') as emptyfile:
            wr = csv.writer(emptyfile)
            for line in data:
                wr.writerow(line)

    def createCsvDataset(self, trading_pair, interval, start_date, dataset_folder):
        start_date_split = start_date.split(' ')
        start_date_split[1] = start_date_split[1][:-1]

        valid_date = True
        if start_date_split[1] == 'January' or start_date_split[1] == 'March' or start_date_split[1] == 'May' or \
        start_date_split[1] == 'July' or start_date_split[1] == 'August' or start_date_split[1] == 'October' or \
        start_date_split[1] == 'December':
            if int(start_date_split[0]) <1 or int(start_date_split[0]) > 31 or int(start_date_split[2]) < 2008:
                valid_date = False
        elif start_date_split[1] == 'February':
            if int(start_date_split[0]) <1 or int(start_date_split[0]) > 28 or int(start_date_split[2]) < 2008:
                valid_date = False
        elif start_date_split[1] == 'April' or start_date_split[1] == 'June' or start_date_split[1] == 'September' or \
        start_date_split[1] == 'November':
            if int(start_date_split[0]) <1 or int(start_date_split[0]) > 30 or int(start_date_split[2]) < 2008:
                valid_date = False
        else:
            valid_date = False

        if valid_date == False:
            sys.exit('Date in config file is not valid. Please enter a valid date.')

        bars = self.client.get_historical_klines(trading_pair, interval, start_date)

        filename = trading_pair + '_' + interval + '_' + start_date_split[0] + '_' + start_date_split[1] + '_' + start_date_split[2] + '.csv'
        with open(dataset_folder+filename, 'w', newline='') as emptyfile:
            wr = csv.writer(emptyfile)
            for line in bars:
                wr.writerow(line)
        return filename