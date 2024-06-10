# -*- coding: utf-8 -*-
"""
Created on Tue Feb  6 11:57:46 2018

@author: Administrator
"""

# In[1]:

#need to get fix yahoo finance package first

import matplotlib.pyplot as plt  # 導入繪圖庫
import numpy as np  # 導入數據處理庫
import pandas as pd  # 導入數據分析庫
import yfinance as yf  # 導入yahoo finance數據包
import sys  # 導入系統庫
import os  # 導入操作系統庫


# In[2]:

#simple moving average
# 簡單移動平均線
def macd(signals, ma1, ma2):
    signals['ma1'] = signals['Close'].rolling(window=ma1, min_periods=1, center=False).mean()  # 計算短期移動平均線
    signals['ma2'] = signals['Close'].rolling(window=ma2, min_periods=1, center=False).mean()  # 計算長期移動平均線
    return signals  # 返回包含移動平均線的數據框


# In[3]:

#signal generation
#when the short moving average is larger than long moving average, we long and hold
#when the short moving average is smaller than long moving average, we clear positions
#the logic behind this is that the momentum has more impact on short moving average
#we can subtract short moving average from long moving average
#the difference between is sometimes positive, it sometimes becomes negative
#thats why it is named as moving average converge/diverge oscillator
# 交易信號生成函數
def signal_generation(df, ma1, ma2, method):
    signals = method(df, ma1, ma2)  # 計算移動平均線
    signals['positions'] = 0   # 初始化持倉

    #positions becomes and stays one once the short moving average is above long moving average
    # 當短期移動平均線高於長期移動平均線時，持倉為1（做多）
    signals['positions'][ma1:] = np.where(signals['ma1'][ma1:] >= signals['ma2'][ma1:], 1, 0)

    #as positions only imply the holding
    #we take the difference to generate real trade signal
    # 產生交易信號
    signals['signals'] = signals['positions'].diff()

    #oscillator is the difference between two moving average
    #when it is positive, we long, vice versa
    # 計算振盪器
    signals['oscillator'] = signals['ma1'] - signals['ma2']

    return signals # 返回包含信號的數據框


# In[4]:

#plotting the backtesting result
# 繪製回測結果的函數
def plot(new, ticker, output_dir):
    # 確保輸出目錄存在
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    #the first plot is the actual close price with long/short positions
    # 繪製收盤價及交易信號
    fig = plt.figure()
    ax = fig.add_subplot(111)

    new['Close'].plot(label=ticker)  # 繪製收盤價
    ax.plot(new.loc[new['signals'] == 1].index, new['Close'][new['signals'] == 1], label='LONG', lw=0, marker='^', c='g')  # 繪製做多信號
    ax.plot(new.loc[new['signals'] == -1].index, new['Close'][new['signals'] == -1], label='SHORT', lw=0, marker='v', c='r')  # 繪製做空信號

    plt.legend(loc='best')  # 添加圖例
    plt.grid(True)  # 添加網格
    plt.title('Positions')  # 添加標題
    positions_path = os.path.join(output_dir, "output_positions_MACD.png")  # 設定輸出路徑
    plt.savefig(positions_path)  # 保存圖表為圖片
    plt.close(fig)  # 關閉圖表以節省內存

    #the second plot is long/short moving average with oscillator
    #note that i use bar chart for oscillator
    # 繪製移動平均線和振盪器
    fig = plt.figure()
    cx = fig.add_subplot(211)

    new['oscillator'].plot(kind='bar', color='r')  # 繪製振盪器

    plt.legend(loc='best')  # 添加圖例
    plt.grid(True)  # 添加網格
    plt.xticks([])  # 隱藏x軸標籤
    plt.xlabel('')  # 清空x軸標籤
    plt.title('MACD Oscillator')  # 添加標題

    bx = fig.add_subplot(212)

    new['ma1'].plot(label='ma1')  # 繪製短期移動平均線
    new['ma2'].plot(label='ma2', linestyle=':')  # 繪製長期移動平均線

    plt.legend(loc='best')  # 添加圖例
    plt.grid(True)  # 添加網格
    macd_path = os.path.join(output_dir, "output_macd.png")  # 設定輸出路徑
    plt.savefig(macd_path)  # 保存圖表為圖片
    plt.close(fig)  # 關閉圖表以節省內存

    return positions_path, macd_path  # 返回圖片路徑




# In[5]:

def main():
    # 獲取命令行參數
    ma1 = int(sys.argv[1])  # 短期移動平均線的窗口大小
    ma2 = int(sys.argv[2])  # 長期移動平均線的窗口大小
    stdate = sys.argv[3]  # 開始日期
    eddate = sys.argv[4]  # 結束日期
    ticker = sys.argv[5]  # 股票代碼
    slicer = int(sys.argv[6])  # 用於切片數據的參數
    output_dir = sys.argv[7]  # 獲取輸出目錄參數

    # 下載數據
    df = yf.download(ticker, start=stdate, end=eddate)

    # 生成交易信號
    new = signal_generation(df, ma1, ma2, macd)
    new = new[slicer:]  # 切片數據

    # 繪圖並獲取圖片路徑
    positions_path, macd_path = plot(new, ticker, output_dir)
    
    # 打印一些輸出供檢查
    print(f"Analysis completed for {ticker} from {stdate} to {eddate}")
    print(f"MA1: {ma1}, MA2: {ma2}, Slicer: {slicer}")
    print("The results have been plotted and saved as images.")
    print(f"Positions plot saved at: {positions_path}")
    print(f"MACD plot saved at: {macd_path}")


#how to calculate stats could be found from my other code called Heikin-Ashi
# https://github.com/je-suis-tm/quant-trading/blob/master/heikin%20ashi%20backtest.py

if __name__ == '__main__':
    main()
