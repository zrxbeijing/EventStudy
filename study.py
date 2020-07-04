import argparse
import pandas as pd
from EventStudy import ReturnCalculator


def run():
    parser = argparse.ArgumentParser(description='Conduct an event study')
    parser.add_argument('event_file', metavar='F', type=str, default=None,
                        help='A data file containing stocks and events.')
    parser.add_argument('-stock_index', dest='stock_index', type=str, default='^GSPC',
                        help='The stock index that the considered stock is related to.')
    parser.add_argument('-window_size', dest='window_size', type=int, default=10, help='The size of the event window.')
    parser.add_argument('-window_distance', dest='window_distance', type=int, default=50,
                        help='The distance between the estimation period and the event window.')
    parser.add_argument('-estimation_period', dest='estimation_period', type=int, default=200,
                        help='The distance between the estimation period and the event window.')

    args = parser.parse_args()

    if not args.event_file:
        raise RuntimeError("An event file should be provided.")
    if not args.stock_index:
        raise RuntimeError("A stock index should be provided.")

    print('start')

    event_df = pd.read_excel(args.event_file)
    return_column_list = ['return t{}'.format(str(day))
                          for day in list(range(-args.window_size, args.window_size + 1))]
    abnormal_column_list = ['ab return t{}'.format(str(day))
                            for day in list(range(-args.window_size, args.window_size + 1))]
    stock_window_df = pd.DataFrame(columns=return_column_list)
    abnormal_window_df = pd.DataFrame(columns=abnormal_column_list)

    for index, row in event_df.iterrows():
        print('processing no. {}'.format(str(index)))
        ticker, event_date = row['ticker'], row['date'].split(' ')[0]
        window_df = ReturnCalculator(ticker, event_date, args.stock_index).calculate_window_abnormal(
            args.window_size, args.window_distance, args.estimation_period
        )
        if window_df is not None and len(window_df) == len(return_column_list):  # make sure that the shapes match.
            stock_df = window_df[['stock_return']].transpose()
            stock_df.columns = return_column_list
            stock_window_df = stock_window_df.append(stock_df, ignore_index=True)
            abnormal_df = window_df[['abnormal_return']].transpose()
            abnormal_df.columns = abnormal_column_list
            abnormal_window_df = abnormal_window_df.append(abnormal_df, ignore_index=True)
        else:
            stock_df = pd.DataFrame(columns=return_column_list)
            stock_df = stock_df.append(pd.Series(), ignore_index=True)
            stock_window_df = stock_window_df.append(stock_df, ignore_index=True)
            abnormal_df = pd.DataFrame(columns=abnormal_column_list)
            abnormal_df = abnormal_df.append(pd.Series(), ignore_index=True)
            abnormal_window_df = abnormal_window_df.append(abnormal_df, ignore_index=True)

    combined_window_df = event_df.join(stock_window_df.join(abnormal_window_df))
    combined_window_df.to_excel('example_result.xlsx')


if __name__ == '__main__':
    run()
