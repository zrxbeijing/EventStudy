# Event Study

This repo aims to simplify a routine in finance research/practice - calculating abnormal returns for specific events for
a given stock. A [Event Study](https://en.wikipedia.org/wiki/Event_study) is a statistical method to measure the impact 
of an event on the pricing/value of financial assets. This package aims to simplify this process and let finance 
researchers or practitioners focus on their empirical ideas.

The package is built upon the [pandas-datareader](https://github.com/pydata/pandas-datareader), an awesome package to
get access to data from different sources for free. In this package, the stock price data is by default derived from 
Yahoo Finance API. 

## How to use
First, prepare an excel file containing the necessary information for event study. The excel file should have the
following columns:
- 'date'. The date of the event.
- 'ticker'. The ticker of the stock.

For a small example, you can use the 'example.xlsx'. In the Terminal, type the following command:

$ python study.py example.xlsx

To change the parameters for the event study, type the following command to see what can be set:

$ python study.py -h

You can change the following parameters:
- -stock_index. The market index for the asset pricing model.
- -window_size. The window size for the event study, e.g., window_size=10 means the event study will be conducted for 10 
days before and the event (day zero, defined as the event date, is also included).
- -window_distance. The distance between the event date and the estimation period.
- -estimation_period. How long is the estimation period. For a statistically meaningful regression of a market model, 
the estimation_period should be at least 30.

After executing the **python study.py example.xlsx** command, a new excel file containing the results will be generated.
In this excel file, you are expected to see the normal and abnormal returns for all the events during the window period.
You can take a look at the file 'example_result.xlsx'.
