
import sys
import os
import numpy as np
import pandas as pd
import yfinance as yf
import math
from scipy import stats
import xlsxwriter
from statistics import mean
import warnings

# 忽略 FutureWarning 和 pandas 的 SettingWithCopyWarning 警告
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=pd.errors.SettingWithCopyWarning)

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('display.width', None)

def fetch_data(symbol_strings):
    all_data = {}
    for symbol_string in symbol_strings:
        data = yf.download(symbol_string, period="1y", interval="1d", group_by='ticker', auto_adjust=True)
        for symbol in symbol_string.split():
            if symbol not in data or data[symbol]['Close'].isna().all():
                continue
            all_data[symbol] = data[symbol]
    return all_data

def process_data(all_data, my_columns):
    final_dataframe = pd.DataFrame(columns=my_columns)
    for symbol, symbol_data in all_data.items():
        price = symbol_data['Close'].iloc[-1]
        one_year_return = (symbol_data['Close'].iloc[-1] - symbol_data['Close'].iloc[0]) / symbol_data['Close'].iloc[0]
        new_row = pd.DataFrame([[symbol, price, one_year_return, 'N/A']], columns=my_columns)
        final_dataframe = pd.concat([final_dataframe, new_row], ignore_index=True)
    return final_dataframe

def calculate_momentum_scores(hqm_dataframe):
    time_periods = ['One-Year', 'Six-Month', 'Three-Month', 'One-Month']
    for row in hqm_dataframe.index:
        for time_period in time_periods:
            hqm_dataframe.loc[row, f'{time_period} Return Percentile'] = stats.percentileofscore(
                hqm_dataframe[f'{time_period} Price Return'], hqm_dataframe.loc[row, f'{time_period} Price Return']) / 100
        momentum_percentiles = [hqm_dataframe.loc[row, f'{time_period} Return Percentile'] for time_period in time_periods]
        hqm_dataframe.loc[row, 'HQM Score'] = mean(momentum_percentiles)
    return hqm_dataframe

def export_to_excel(hqm_dataframe):
    # ### Export High Quality Momentum Strategy Results to Excel
    
    writer = pd.ExcelWriter('PythonScripts/quantitative_momentum/high_quality_momentum_strategy.xlsx', engine='xlsxwriter')
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
    
    writer.close()

def main():
    Remove_Low_Momentum_Stocks_Number = int(sys.argv[1])
    portfolio = int(sys.argv[2])

    current_dir = os.getcwd()
    print(f"Current working directory: {current_dir}")
    file_path = 'PythonScripts/quantitative_momentum/Y_taiwan_50_index.csv'
    if not os.path.isfile(file_path):
        print(f"File not found: {file_path}")
        return
    
    try:
        stocks = pd.read_csv(file_path)
        stocks.rename(columns={'Symbol': 'Ticker'}, inplace=True)
        print("Initial Stocks Data:")
        print(stocks.head())

        def chunks(lst, n):
            for i in range(0, len(lst), n):
                yield lst[i:i + n]

        symbol_groups = list(chunks(stocks['Ticker'], 10))
        symbol_strings = [' '.join(symbol_groups[i]) for i in range(len(symbol_groups))]
        global my_columns
        my_columns = ['Ticker', 'Price', 'One-Year Price Return', 'Number of Shares to Buy']
        
        all_data = fetch_data(symbol_strings)
        final_dataframe = process_data(all_data, my_columns)
        # print("Final DataFrame after Fetching Data:")
        # print(final_dataframe)

        final_dataframe.sort_values('One-Year Price Return', ascending=False, inplace=True)
        final_dataframe = final_dataframe[:Remove_Low_Momentum_Stocks_Number]
        final_dataframe.reset_index(drop=True, inplace=True)
        # print("Final DataFrame after Removing Low-Momentum Stocks:")
        # print(final_dataframe)

        position_size = float(portfolio) / len(final_dataframe.index)
        for i in range(len(final_dataframe['Ticker'])):
            final_dataframe.loc[i, 'Number of Shares to Buy'] = math.floor(position_size / final_dataframe['Price'][i])
        print("Final DataFrame after Calculating Number of Shares to Buy:")
        print(final_dataframe)

        hqm_columns = [
            'Ticker', 'Price', 'Number of Shares to Buy', 'One-Year Price Return', 'One-Year Return Percentile',
            'Six-Month Price Return', 'Six-Month Return Percentile', 'Three-Month Price Return',
            'Three-Month Return Percentile', 'One-Month Price Return', 'One-Month Return Percentile', 'HQM Score'
        ]

        hqm_dataframe = pd.DataFrame(columns=hqm_columns)
        for symbol, symbol_data in all_data.items():
            price = symbol_data['Close'].iloc[-1]
            one_year_return = (symbol_data['Close'].iloc[-1] - symbol_data['Close'].iloc[0]) / symbol_data['Close'].iloc[0]
            six_month_return = (symbol_data['Close'].iloc[-1] - symbol_data['Close'].iloc[-126]) / symbol_data['Close'].iloc[-126]
            three_month_return = (symbol_data['Close'].iloc[-1] - symbol_data['Close'].iloc[-63]) / symbol_data['Close'].iloc[-63]
            one_month_return = (symbol_data['Close'].iloc[-1] - symbol_data['Close'].iloc[-21]) / symbol_data['Close'].iloc[-21]

            new_row = pd.DataFrame([[
                symbol, price, 'N/A', one_year_return, 'N/A', six_month_return, 'N/A', three_month_return,
                'N/A', one_month_return, 'N/A', 'N/A'
            ]], columns=hqm_columns)
            hqm_dataframe = pd.concat([hqm_dataframe, new_row], ignore_index=True)

        # print("HQM DataFrame after Building DataFrame:")
        # print(hqm_dataframe)

        hqm_dataframe = calculate_momentum_scores(hqm_dataframe)
        # print("HQM DataFrame after Calculating Momentum Percentiles and HQM Score:")
        # print(hqm_dataframe)

        hqm_dataframe.sort_values(by='HQM Score', ascending=False, inplace=True)
        hqm_dataframe = hqm_dataframe[:Remove_Low_Momentum_Stocks_Number]
        hqm_dataframe.reset_index(drop=True, inplace=True)
        # print("HQM DataFrame after Selecting 50 Best Momentum Stocks:")
        # print(hqm_dataframe)

        position_size = float(portfolio) / len(hqm_dataframe.index)
        for i in range(len(hqm_dataframe['Ticker'])):
            hqm_dataframe.loc[i, 'Number of Shares to Buy'] = math.floor(position_size / hqm_dataframe['Price'][i])
        print("HQM DataFrame after Calculating Number of Shares to Buy:")
        print(hqm_dataframe)

        export_to_excel(hqm_dataframe)
        print("Excel file 'high_quality_momentum_strategy.xlsx' has been created successfully.")
        
    except Exception as e:
        print(f"An error occurred: {e}")
        return

if __name__ == "__main__":
    main()

