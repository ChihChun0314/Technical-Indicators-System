#!/usr/bin/env python
# coding: utf-8

# ## Quantitative Momentum Strategy

# ### Low Quality Momentum Strategy

# #### Import Libraries and Data

import sys
import os
import numpy as np
import pandas as pd
import yfinance as yf
import math
from scipy import stats
import xlsxwriter
from statistics import mean


# 確認當前工作目錄
current_dir = os.getcwd()
print(f"Current working directory: {current_dir}")
# 讀取台灣50指數的股票資料
file_path = 'PythonScripts/quantitative_momentum/Y_taiwan_50_index.csv'
if not os.path.isfile(file_path):
    print(f"File not found: {file_path}")
    

# 讀取台灣50指數的股票資料
stocks = pd.read_csv('Y_taiwan_50_index.csv')
stocks.rename(columns={'Symbol': 'Ticker'}, inplace=True)
print("Initial Stocks Data:")
print(stocks.head())

# #### Batch API Calls

def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

symbol_groups = list(chunks(stocks['Ticker'], 10))
symbol_strings = []
for i in range(0, len(symbol_groups)):
    symbol_strings.append(' '.join(symbol_groups[i]))

my_columns = ['Ticker', 'Price', 'One-Year Price Return', 'Number of Shares to Buy']

# #### Fetch Data from yfinance

final_dataframe = pd.DataFrame(columns=my_columns)

for symbol_string in symbol_strings:
    data = yf.download(symbol_string, period="1y", interval="1d", group_by='ticker', auto_adjust=True)
    for symbol in symbol_string.split():
        if symbol not in data:
            continue
        symbol_data = data[symbol]
        price = symbol_data['Close'].iloc[-1]
        one_year_return = (symbol_data['Close'].iloc[-1] - symbol_data['Close'].iloc[0]) / symbol_data['Close'].iloc[0]
        new_row = pd.DataFrame([[symbol, price, one_year_return, 'N/A']], columns=my_columns)
        final_dataframe = pd.concat([final_dataframe, new_row], ignore_index=True)

print("Final DataFrame after Fetching Data:")
print(final_dataframe)

# #### Remove Low-Momentum Stocks

final_dataframe.sort_values('One-Year Price Return', ascending=False, inplace=True)
final_dataframe = final_dataframe[:40+1]
final_dataframe.reset_index(drop=True, inplace=True)
print("Final DataFrame after Removing Low-Momentum Stocks:")
print(final_dataframe)

# #### Calculate Number of Shares to Buy

# def portfolio_input():
#     global portfolio_size
#     portfolio_size = input("Enter the value of your portfolio:")

#     try:
#         val = float(portfolio_size)
#     except ValueError:
#         print("That's not a number! \nTry again:")
#         portfolio_size = input("Enter the value of your portfolio:")

# portfolio_input()
# print("Portfolio Size:")
# print(portfolio_size)

position_size = float(1000000) / len(final_dataframe.index)
for i in range(0, len(final_dataframe['Ticker'])):
    final_dataframe.loc[i, 'Number of Shares to Buy'] = math.floor(position_size / final_dataframe['Price'][i])
print("Final DataFrame after Calculating Number of Shares to Buy:")
print(final_dataframe)

# ### High Quality Momentum Strategy

# #### Build DataFrame

hqm_columns = [
    'Ticker', 'Price', 'Number of Shares to Buy', 'One-Year Price Return', 'One-Year Return Percentile',
    'Six-Month Price Return', 'Six-Month Return Percentile', 'Three-Month Price Return',
    'Three-Month Return Percentile', 'One-Month Price Return', 'One-Month Return Percentile', 'HQM Score'
]

hqm_dataframe = pd.DataFrame(columns=hqm_columns)

for symbol_string in symbol_strings:
    data = yf.download(symbol_string, period="1y", interval="1d", group_by='ticker', auto_adjust=True)
    for symbol in symbol_string.split():
        if symbol not in data:
            continue
        symbol_data = data[symbol]
        price = symbol_data['Close'].iloc[-1]
        one_year_return = (symbol_data['Close'].iloc[-1] - symbol_data['Close'].iloc[0]) / symbol_data['Close'].iloc[0]
        six_month_return = (symbol_data['Close'].iloc[-1] - symbol_data['Close'].iloc[-126]) / symbol_data['Close'].iloc[-126]  # Approx. 6 months
        three_month_return = (symbol_data['Close'].iloc[-1] - symbol_data['Close'].iloc[-63]) / symbol_data['Close'].iloc[-63]  # Approx. 3 months
        one_month_return = (symbol_data['Close'].iloc[-1] - symbol_data['Close'].iloc[-21]) / symbol_data['Close'].iloc[-21]  # Approx. 1 month

        new_row = pd.DataFrame([[
            symbol, price, 'N/A', one_year_return, 'N/A', six_month_return, 'N/A', three_month_return,
            'N/A', one_month_return, 'N/A', 'N/A'
        ]], columns=hqm_columns)
        hqm_dataframe = pd.concat([hqm_dataframe, new_row], ignore_index=True)

print("HQM DataFrame after Building DataFrame:")
print(hqm_dataframe)

# #### Calculate Momentum Percentiles

time_periods = ['One-Year', 'Six-Month', 'Three-Month', 'One-Month']

for row in hqm_dataframe.index:
    for time_period in time_periods:
        hqm_dataframe.loc[row, f'{time_period} Return Percentile'] = stats.percentileofscore(
            hqm_dataframe[f'{time_period} Price Return'], hqm_dataframe.loc[row, f'{time_period} Price Return']) / 100

print("HQM DataFrame after Calculating Momentum Percentiles:")
print(hqm_dataframe)

# #### Calculate High Quality Momentum (HQM) Score

for row in hqm_dataframe.index:
    momentum_percentiles = []
    for time_period in time_periods:
        momentum_percentiles.append(hqm_dataframe.loc[row, f'{time_period} Return Percentile'])
    hqm_dataframe.loc[row, 'HQM Score'] = mean(momentum_percentiles)

print("HQM DataFrame after Calculating HQM Score:")
print(hqm_dataframe)

# #### Select 50 Best Momentum Stocks

hqm_dataframe.sort_values(by='HQM Score', ascending=False, inplace=True)
hqm_dataframe = hqm_dataframe[:51]
hqm_dataframe.reset_index(drop=True, inplace=True)
print("HQM DataFrame after Selecting 50 Best Momentum Stocks:")
print(hqm_dataframe)

# #### Calculate Number of Shares to Buy

# portfolio_input()
# print("Portfolio Size:")
# print(portfolio_size)

position_size = float(1000000) / len(hqm_dataframe.index)
for i in range(0, len(hqm_dataframe['Ticker'])):
    hqm_dataframe.loc[i, 'Number of Shares to Buy'] = math.floor(position_size / hqm_dataframe['Price'][i])
print("HQM DataFrame after Calculating Number of Shares to Buy:")
print(hqm_dataframe)

# ### Export High Quality Momentum Strategy Results to Excel

writer = pd.ExcelWriter('high_quality_momentum_strategy.xlsx', engine='xlsxwriter')
hqm_dataframe.to_excel(writer, sheet_name='Momentum Strategy', index=False)

background_color = '#0a0a23'
font_color = '#ffffff'

string_template = writer.book.add_format({
    'font_color': font_color,
    'bg_color': background_color,
    'border': 1
})

dollar_template = writer.book.add_format({
    'num_format': '$0.00',
    'font_color': font_color,
    'bg_color': background_color,
    'border': 1
})

integer_template = writer.book.add_format({
    'num_format': '0',
    'font_color': font_color,
    'bg_color': background_color,
    'border': 1
})

percent_template = writer.book.add_format({
    'num_format': '0.0%',
    'font_color': font_color,
    'bg_color': background_color,
    'border': 1
})

column_formats = {
    'A': ['Ticker', string_template],
    'B': ['Price', dollar_template],
    'C': ['Number of Shares to Buy', integer_template],
    'D': ['One-Year Price Return', percent_template],
    'E': ['One-Year Return Percentile', percent_template],
    'F': ['Six-Month Price Return', percent_template],
    'G': ['Six-Month Return Percentile', percent_template],
    'H': ['Three-Month Price Return', percent_template],
    'I': ['Three-Month Return Percentile', percent_template],
    'J': ['One-Month Price Return', percent_template],
    'K': ['One-Month Return Percentile', percent_template],
    'L': ['HQM Score', integer_template]
}

for column in column_formats.keys():
    writer.sheets['Momentum Strategy'].set_column(f'{column}:{column}', 20, column_formats[column][1])
    writer.sheets['Momentum Strategy'].write(f'{column}1', column_formats[column][0], string_template)
