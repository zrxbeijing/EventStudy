from EventStudy import PriceFetcher
import statsmodels.formula.api as sm
from datetime import datetime, timedelta
import pandas as pd


def calculate_return(ticker, start_date, end_date):
    """
    A simple return calculator.
    :param ticker: the stock ticker.
    :param start_date: the beginning date of the calculation.
    :param end_date: the ending date of the calculation.
    :return: a return DataFrame.
    """
    data_df = PriceFetcher(ticker, start_date, end_date).fetch()
    if data_df is not None:
        data_lag = data_df['Adj Close'].shift(periods=1)
        data_df['return'] = (data_df['Adj Close'] - data_lag) / data_lag
    return data_df


def combine_return(stock_df, index_df):
    """
    Combine the return of the target stock and the market index.
    :param stock_df: the stock's return DataFrame.
    :param index_df: the market's return DataFrame.
    :return: a combined return DataFrame.
    """
    if stock_df is not None and index_df is not None:
        price_df = pd.merge(stock_df, index_df, on='Date').reset_index(drop=True)
        price_df.rename(columns={'return_x': 'stock_return', 'return_y': 'index_return'}, inplace=True)
    else:
        price_df = None
    return price_df


class ReturnCalculator(object):
    def __init__(self, ticker: str, event_date: str, stock_index: str, calendar_day: bool = False):
        """
        This is a return calculator.
        :param ticker: the stock ticker.
        :param event_date: the event date, should be in format of "%Y-%m-%d".
        :param stock_index: the ticker of the stock index.
        :param calendar_day: choose one of two modes: calendar day or trading day.
        """
        self.ticker = ticker
        self.event_date = event_date
        self.stock_index = stock_index
        self.calendar_day = calendar_day

    def calculate_window_return(self, window_size: int):
        """
        Calculate the absolute returns during the event window.
        :param window_size: the size of the event window.
        :return: a dict containing the absolute returns during the event window.
        """
        event_date = datetime.strptime(self.event_date, "%Y-%m-%d")
        # To make sure we have stock price data covering the whole event window.
        start_date = datetime.strftime(
            event_date - timedelta(days=window_size * 7), "%Y-%m-%d"
        )
        end_date = datetime.strftime(
            event_date + timedelta(days=window_size * 7), "%Y-%m-%d"
        )
        stock_df = calculate_return(self.ticker, start_date, end_date)
        index_df = calculate_return(self.stock_index, start_date, end_date)
        price_df = combine_return(stock_df, index_df)
        event_date = pd.Timestamp(
            datetime(event_date.year, event_date.month, event_date.day)
        )
        if price_df is not None:
            # add a 'drift' column, recording the distance between the event day and each observation day.
            price_df['drift'] = price_df['Date'] - event_date
            price_df['drift'] = price_df['drift'].apply(lambda x: x.days)
            # create a template DataFrame.
            df_template = pd.DataFrame(
                index=range((price_df.Date.iloc[-1] - price_df.Date.iloc[0]).days + 1), columns=price_df.columns
            )
            df_template['Date'] = [pd.Timestamp(price_df.Date.iloc[0].to_pydatetime() + timedelta(days=i))
                                   for i in range((price_df.Date.iloc[-1] - price_df.Date.iloc[0]).days + 1)]
            df_template['drift'] = df_template['Date'] - event_date
            df_template['drift'] = df_template['drift'].apply(lambda x: x.days)
            # concat the template and price DataFrame
            concat_df = pd.concat([price_df, df_template])
            concat_df = concat_df.drop_duplicates(subset=['drift'], keep='first')
            concat_df = concat_df.sort_values(by='drift').reset_index(drop=True)
            window_list = list(range(-window_size, window_size + 1))
            if self.calendar_day:
                window_return_df = concat_df[concat_df['drift'].isin(window_list)].reset_index(drop=True)[
                    ['drift', 'Date', 'stock_return', 'index_return']].set_index('drift').transpose()
            else:
                # create a new column, indicating trading drift, to replace the original drift column.
                intermediate_df = concat_df.dropna().reset_index(drop=True)
                if len(intermediate_df[intermediate_df['drift'] >= 0]) != 0:    # make sure that zero_index exists.
                    zero_index = intermediate_df[intermediate_df['drift'] >= 0].index[0]
                    intermediate_df = intermediate_df.drop(columns=['drift'])
                    drift_trading = [index - zero_index for index, row in intermediate_df.iterrows()]
                    intermediate_df['drift'] = drift_trading
                    window_return_df = intermediate_df[intermediate_df['drift'].isin(window_list)].reset_index(drop=True)[
                        ['drift', 'Date', 'stock_return', 'index_return']].set_index('drift')
                else:
                    window_return_df = None
        else:
            window_return_df = None
        return window_return_df

    def estimate_market_model(self, window_distance: int, period_len: int):
        """
        Estimate the market model.
        :param window_distance: how many days earlier than the begin of the event window.
        :param period_len: how long is the estimation period.
        :return: a dict containing the abnormal returns during the event window.
        """
        event_date = datetime.strptime(self.event_date, "%Y-%m-%d")
        end_date = event_date - timedelta(days=window_distance)
        start_date = datetime.strftime(
            end_date - timedelta(days=period_len * 2), "%Y-%m-%d"
        )
        end_date = datetime.strftime(end_date, "%Y-%m-%d")
        stock_df = calculate_return(self.ticker, start_date, end_date)
        index_df = calculate_return(self.stock_index, start_date, end_date)
        price_df = combine_return(stock_df, index_df)
        if price_df is None:
            intercept, beta, rsquared = None, None, None
        else:
            price_df = price_df.iloc[-period_len:]
            regression_result = sm.ols(formula="stock_return ~ index_return", data=price_df).fit()
            intercept = regression_result.params['Intercept']
            beta = regression_result.params['index_return']
            rsquared = regression_result.rsquared
        return intercept, beta, rsquared

    def calculate_window_abnormal(self, window_size: int, window_distance: int, period_len: int):
        """
        Calculate the abnormal return.
        :param window_size: the size of the event window.
        :param window_distance: how many days earlier than the begin of the event window.
        :param period_len: how long is the estimation period.
        :return: a dict containing the abnormal returns during the event window.
        """
        window_return_df = self.calculate_window_return(window_size)
        intercept, beta, rsquared = self.estimate_market_model(window_distance, period_len)
        if window_return_df is not None and rsquared is not None:
            window_return_df['abnormal_return'] = [row['stock_return'] - intercept - beta*row['index_return']
                                                   for index, row in window_return_df.iterrows()]
        else:
            window_return_df = None
        return window_return_df

