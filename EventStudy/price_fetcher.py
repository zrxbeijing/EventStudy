import pandas_datareader as pdr_data
import pandas as pd
import os
import logging


class PriceFetcher(object):
    def __init__(self, ticker, start, end, cache_dir='cached_data'):
        """
        This is a price fetcher.
        :param ticker: Stock ticker.
        :param start: The begin of the observation period. Pattern: "%Y-%m-%d"
        :param end: The end of the observation period. Pattern: "%Y-%m-%d"
        :param cache_dir: where stock price data is stored.
        """
        self.ticker = ticker
        self.start = start
        self.end = end
        self.cache_dir = cache_dir
        if not os.path.exists(self.cache_dir):
            os.mkdir(self.cache_dir)
        self.data_path = os.path.join(self.cache_dir, self.ticker + '-' + 'from' + self.start + 'to' + self.end+'.csv')

    def fetch(self):
        """
        Fetch the corresponding stock price data. If the data doesn't exist, the download method will be initiated.
        :return: stock price data in the form of DataFrame
        """
        if not os.path.exists(self.data_path):
            data_df = self.download()
            if data_df is not None:
                data_df = pd.read_csv(self.data_path, index_col=0)
                data_df['Date'] = pd.to_datetime(data_df.Date)
            else:
                data_df = None
        else:
            data_df = pd.read_csv(self.data_path, index_col=0)
            data_df['Date'] = pd.to_datetime(data_df.Date)
        return data_df

    def download(self):
        """
        Download stock price data and store it in the cache directory.
        :return: stock price data in the form of DataFrame
        """
        try:
            data_df = pdr_data.DataReader(self.ticker, 'yahoo', self.start, self.end)
            data_df.reset_index(level=0, inplace=True)
            data_df = data_df[['Date', 'Adj Close']]
            data_df.to_csv(self.data_path)
        except KeyError:
            logging.info('no requested data from Yahoo Finance.')
            data_df = None
        return data_df

