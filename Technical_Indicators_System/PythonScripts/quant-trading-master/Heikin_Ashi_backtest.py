# -*- coding: utf-8 -*-
"""
Created on Thu Feb 15 20:48:35 2030

@author: Administrator
"""

# In[1]:

# heikin ashi 是一種日本的方法，用於過濾動量交易的噪音
# 它可以防止橫盤整理的發生
# 基本上我們對四個關鍵基準進行一些轉換 - 開盤價、收盤價、最高價、最低價
# 將一些獨特的規則應用於 ha 開盤價、收盤價、最高價、最低價進行交易
# heikin ashi 指標和規則的詳細信息可以在以下鏈接找到
# https://quantiacs.com/Blog/Intro-to-Algorithmic-Trading-with-Heikin-Ashi.aspx

# 需要先獲取 yfinance 包
# 它的名稱從 fix_yahoo_finance 變為 yfinance，哈哈

# In[2]:

# 引入所需的庫
import pandas as pd  # 用於數據操作的庫
import matplotlib.pyplot as plt  # 用於繪圖的庫
import yfinance as yf  # 用於從 Yahoo Finance 獲取數據的庫
import numpy as np  # 用於數值計算的庫
import scipy.integrate  # 用於數值積分的庫
import scipy.stats  # 用於統計計算的庫
import sys
import os

# In[3]:

# Heikin Ashi 有一種獨特的方法來過濾噪音
# 它的開盤價、收盤價、最高價、最低價需要不同的計算方法
# 請參閱上述網站以了解更多細節
def heikin_ashi(data):
    
    # 複製數據框
    df = data.copy()
    
    # 重置索引
    df.reset_index(inplace=True)
        
    # 計算 Heikin Ashi 的收盤價
    df['HA close'] = (df['Open'] + df['Close'] + df['High'] + df['Low']) / 4

    # 初始化 Heikin Ashi 的開盤價
    df['HA open'] = float(0)  # 初始化為0
    if len(df) > 0:
        df.loc[0, 'HA open'] = df['Open'].iloc[0]  # 第一個 HA 開盤價等於原始開盤價

    # 計算 Heikin Ashi 的開盤價
    for n in range(1, len(df)):
        df.loc[n, 'HA open'] = (df.loc[n-1, 'HA open'] + df.loc[n-1, 'HA close']) / 2
        
    # 計算 Heikin Ashi 的最高價和最低價
    temp = pd.concat([df['HA open'], df['HA close'], df['Low'], df['High']], axis=1)
    df['HA high'] = temp.max(axis=1)  # 最高價為四者中的最大值
    df['HA low'] = temp.min(axis=1)  # 最低價為四者中的最小值

    # 刪除不需要的列
    df.drop(columns=['Adj Close', 'Volume'], inplace=True)
    
    return df

# In[4]:

# 設置信號生成
# 觸發條件可以從上述網站找到
# 它們看起來像 Marubozu 燭台
# 還有一個短策略
# 短策略的觸發條件是長策略的反向
# 您必須滿足所有四個條件才能長/短
# 然而，退出信號只有三個條件
def signal_generation(df, method, stls):
        
    data = method(df)  # 應用 Heikin Ashi 方法
    
    # 初始化信號列
    data['signals'] = 0

    # 使用累積和來檢查有多少Position
    # 如果不持有Position，將忽略退出信號
    # 也追踪有多少Long Position
    # 長信號不能超過止損限制
    data['cumsum'] = 0

    for n in range(1, len(data)):
        
        # 長信號觸發
        if (data.loc[n, 'HA open'] > data.loc[n, 'HA close'] and data.loc[n, 'HA open'] == data.loc[n, 'HA high'] and
            np.abs(data.loc[n, 'HA open'] - data.loc[n, 'HA close']) > np.abs(data.loc[n-1, 'HA open'] - data.loc[n-1, 'HA close']) and
            data.loc[n-1, 'HA open'] > data.loc[n-1, 'HA close']):
            
            data.loc[n, 'signals'] = 1
            data['cumsum'] = data['signals'].cumsum()

            # 積累過多的Long Position
            if data.loc[n, 'cumsum'] > stls:
                data.loc[n, 'signals'] = 0
        
        # 退出Position
        elif (data.loc[n, 'HA open'] < data.loc[n, 'HA close'] and data.loc[n, 'HA open'] == data.loc[n, 'HA low'] and 
              data.loc[n-1, 'HA open'] < data.loc[n-1, 'HA close']):
            
            data.loc[n, 'signals'] = -1
            data['cumsum'] = data['signals'].cumsum()

            # 清除所有Long Position
            # 如果投資組合中沒有Long Position
            # 忽略退出信號
            if data.loc[n, 'cumsum'] > 0:
                data.loc[n, 'signals'] = -1 * (data.loc[n-1, 'cumsum'])

            if data.loc[n, 'cumsum'] < 0:
                data.loc[n, 'signals'] = 0
                
    return data

# In[5]:

# 由於 matplotlib 移除了燭台
# 並且我們不想安裝 mpl_finance
# 我們實現自己的版本
# 使用 fill_between 來構建條
# 使用線圖來構建高和低
def candlestick(df, ax=None, titlename='', highcol='High', lowcol='Low',
                opencol='Open', closecol='Close', xcol='Date',
                colorup='r', colordown='g', **kwargs):  
    
    # 條的寬度
    # 默認為 0.6
    dif = [(-3 + i) / 10 for i in range(7)]
    
    if not ax:
        ax = plt.figure(figsize=(10, 5)).add_subplot(111)
    
    # 一個一個地構建條
    for i in range(len(df)):
        
        # 默認寬度為 0.6
        # 因此每個條需要 7 個數據點
        x = [i + j for j in dif]
        y1 = [df[opencol].iloc[i]] * 7
        y2 = [df[closecol].iloc[i]] * 7

        barcolor = colorup if y1[0] > y2[0] else colordown
        
        # 如果開盤/收盤是高點，則沒有高線圖
        if df[highcol].iloc[i] != max(df[opencol].iloc[i], df[closecol].iloc[i]):
            
            # 使用通用圖來顯示高和低
            # 使用 1.001 作為縮放因子
            # 防止高線越過條
            plt.plot([i, i],
                     [df[highcol].iloc[i],
                      max(df[opencol].iloc[i],
                          df[closecol].iloc[i]) * 1.001], c='k', **kwargs)
    
        # 與高點相同
        if df[lowcol].iloc[i] != min(df[opencol].iloc[i], df[closecol].iloc[i]):             
            
            plt.plot([i, i],
                     [df[lowcol].iloc[i],
                      min(df[opencol].iloc[i],
                          df[closecol].iloc[i]) * 0.999], c='k', **kwargs)
        
        # 將條視為填充區域
        plt.fill_between(x, y1, y2,
                         edgecolor='k',
                         facecolor=barcolor, **kwargs)

    # 計算 x 軸刻度的間隔，確保間隔不為零
    if len(df) // 5 == 0:
        xticks_interval = 1  # 如果數據點少於 5 個，設置間隔為 1
    else:
        xticks_interval = len(df) // 5
    
    # 只顯示 5 個 x 軸刻度
    plt.xticks(range(0, len(df), xticks_interval), df[xcol][0::xticks_interval].dt.date)
    plt.title(titlename)
    
    
# 繪製回測結果
def plot(df, ticker, output_dir):    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)  # 如果輸出目錄不存在，則創建它
    df.set_index(df['Date'], inplace=True)
    
    # 第一個圖是 Heikin-Ashi 燭台
    # 使用 candlestick 函數並設置 Heikin-Ashi 的 O, C, H, L
    ax1 = plt.subplot2grid((200, 1), (0, 0), rowspan=120, ylabel='HA price')
    candlestick(df, ax1, titlename='', highcol='HA high', lowcol='HA low',
                opencol='HA open', closecol='HA close', xcol='Date',
                colorup='r', colordown='g')
    plt.grid(True)
    plt.xticks([])
    plt.title('Heikin-Ashi')

    # 第二個圖是實際價格，帶有Long/Short Position的上下箭頭
    ax2 = plt.subplot2grid((200, 1), (120, 0), rowspan=80, ylabel='price', xlabel='')
    df['Close'].plot(ax=ax2, label=ticker)

    # Long/Short Position附加到股票的實際收盤價
    # 設置線寬為零
    # 因此我們只會觀察到標記
    ax2.plot(df.loc[df['signals'] == 1].index, df.loc[df['signals'] == 1, 'Close'], marker='^', lw=0, c='g', label='long')
    ax2.plot(df.loc[df['signals'] < 0].index, df.loc[df['signals'] < 0, 'Close'], marker='v', lw=0, c='r', label='short')

    plt.grid(True)
    plt.legend(loc='best')
    positions_path_HeikinAshi = os.path.join(output_dir, "output_positions_HeikinAshi.png")  # 設定圖表保存路徑
    plt.savefig(positions_path_HeikinAshi)  # 保存圖表
    return positions_path_HeikinAshi  # 返回圖表保存路徑

# In[6]:

# 回測
# 初始資金 10k 計算實際損益
# 每個Position購買 100 股
def portfolio(data, capital0=10000, positions=100):   
        
    # cumsum 列用於檢查持倉
    data.loc[:, 'cumsum'] = data['signals'].cumsum()

    portfolio = pd.DataFrame()
    portfolio['holdings'] = data['cumsum'] * data['Close'] * positions  # 計算持有資產的價值
    portfolio['cash'] = capital0 - (data['signals'] * data['Close'] * positions).cumsum()  # 計算現金餘額
    portfolio['total asset'] = portfolio['holdings'] + portfolio['cash']  # 計算總資產價值
    portfolio['return'] = portfolio['total asset'].pct_change()  # 計算每日回報率
    portfolio['signals'] = data['signals']  # 保存信號
    portfolio['date'] = data['Date']  # 保存日期
    portfolio.set_index('date', inplace=True)  # 設置日期為索引

    return portfolio

# In[7]:

# 繪製投資組合資產價值變化
def profit(portfolio, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)  # 如果輸出目錄不存在，則創建它
    fig = plt.figure()
    bx = fig.add_subplot(111)
    
    portfolio['total asset'].plot(label='Total Asset')  # 繪製總資產價值
    
    # 與投資組合相關的Long/Short Position標記
    # 與前面的機制相同
    # 用總資產值替換收盤價
    bx.plot(portfolio.loc[portfolio['signals'] == 1].index, portfolio.loc[portfolio['signals'] == 1, 'total asset'], lw=0, marker='^', c='g', label='long')
    bx.plot(portfolio.loc[portfolio['signals'] < 0].index, portfolio.loc[portfolio['signals'] < 0, 'total asset'], lw=0, marker='v', c='r', label='short')
    
    plt.legend(loc='best')
    plt.grid(True)
    plt.xlabel('Date')
    plt.ylabel('Asset Value')
    plt.title('Total Asset')
    HeikinAshi_path = os.path.join(output_dir, "output_HeikinAshi_portfolio.png")  # 設定圖表保存路徑
    plt.savefig(HeikinAshi_path)  # 保存圖表
    plt.close(fig)  # 關閉圖表

    return HeikinAshi_path  # 返回圖表保存路徑

# In[8]:

# omega 比率是 sharpe 比率的一個變體
# 無風險回報被給定的門檻取代
# 在這種情況下，基準的回報
# 需要積分來計算高於和低於門檻的回報
# 您也可以使用求和來進行近似
# 它是一個更合理的比率來衡量風險調整後的回報
# 正態分佈無法解釋回報的胖尾
# 因此我使用 student T 累積分佈函數
# 為了讓生活更輕鬆，我不使用經驗分佈
# 經驗分佈的累積分佈函數要複雜得多
# 詳情請參閱維基百科
# https://en.wikipedia.org/wiki/Omega_ratio
def omega(risk_free, degree_of_freedom, maximum, minimum):

    y = scipy.integrate.quad(lambda g: 1 - scipy.stats.t.cdf(g, degree_of_freedom), risk_free, maximum)
    x = scipy.integrate.quad(lambda g: scipy.stats.t.cdf(g, degree_of_freedom), minimum, risk_free)

    z = (y[0]) / (x[0])

    return z

# sortino 比率是 sharpe 比率的另一個變體
# 所有回報的標準差被負回報的標準差取代
# sortino 比率衡量負回報對回報的影響
# 我也使用 student T 概率分佈函數而不是正態分佈
# 詳情請參閱維基百科
# https://en.wikipedia.org/wiki/Sortino_ratio
def sortino(risk_free, degree_of_freedom, growth_rate, minimum):

    v = np.sqrt(np.abs(scipy.integrate.quad(lambda g: ((risk_free - g) ** 2) * scipy.stats.t.pdf(g, degree_of_freedom), risk_free, minimum)))
    s = (growth_rate - risk_free) / v[0]

    return s

# 計算最大回撤的函數
# 概念很簡單
# 每天，我們將當前資產價值標記為市場
# 與之前的最高資產價值比較
# 我們得到每日回撤
# 如果當前值不是最高值，則應為負數
# 我們實現一個臨時變量來存儲最小負值
# 這就是所謂的最大回撤
# 對於每個比臨時值小的每日回撤
# 我們更新該臨時值，直到完成遍歷
# 最後我們返回最大回撤
def mdd(series):

    minimum = 0
    for i in range(1, len(series)):
        if minimum > (series.iloc[i] / max(series.iloc[:i]) - 1):
            minimum = (series.iloc[i] / max(series.iloc[:i]) - 1)

    return minimum

# In[9]:

# 統計計算
def stats(portfolio, trading_signals, stdate, eddate, capital0=10000):

    stats = pd.DataFrame(columns=['CAGR', 'portfolio return', 'benchmark return', 'sharpe ratio', 'maximum drawdown', 'calmar ratio', 'omega ratio', 'sortino ratio', 'numbers of longs', 'numbers of shorts', 'numbers of trades', 'total length of trades', 'average length of trades', 'profit per trade'])

    # 獲取回報的最小值和最大值
    maximum = np.max(portfolio['return'])
    minimum = np.min(portfolio['return'])    

    # growth_rate 表示投資組合的平均增長率
    # 使用幾何平均而不是算術平均來計算百分比增長
    if len(portfolio) > 0:
        growth_rate = (float(portfolio['total asset'].iloc[-1] / capital0)) ** (1 / len(trading_signals)) - 1
    else:
        growth_rate = 0

    # 計算標準差
    if len(portfolio) > 1:
        std = float(np.sqrt((((portfolio['return'] - growth_rate) ** 2).sum()) / len(trading_signals)))
    else:
        std = 0

    # 使用標普500作為基準
    benchmark = yf.download('^GSPC', start=stdate, end=eddate)

    # 基準回報
    return_of_benchmark = float(benchmark['Close'].iloc[-1] / benchmark['Open'].iloc[0] - 1)

    # rate_of_benchmark 表示基準的平均增長率
    # 使用幾何平均而不是算術平均來計算百分比增長
    rate_of_benchmark = (return_of_benchmark + 1) ** (1 / len(trading_signals)) - 1

    del benchmark

    # 回測統計
    # CAGR 表示累計平均增長率
    stats.loc[0, 'CAGR'] = growth_rate
    stats.loc[0, 'portfolio return'] = portfolio['total asset'].iloc[-1] / capital0 - 1
    stats.loc[0, 'benchmark return'] = return_of_benchmark
    stats.loc[0, 'sharpe ratio'] = (growth_rate - rate_of_benchmark) / std if std != 0 else 0
    stats.loc[0, 'maximum drawdown'] = mdd(portfolio['total asset'])

    # calmar 比率類似於 sharpe 比率
    # 標準差被最大回撤取代
    # 它是最壞情況調整後的回報測量
    # 詳情請參閱維基百科
    # https://en.wikipedia.org/wiki/Calmar_ratio
    stats.loc[0, 'calmar ratio'] = growth_rate / stats.loc[0, 'maximum drawdown'] if stats.loc[0, 'maximum drawdown'] != 0 else 0
    stats.loc[0, 'omega ratio'] = omega(rate_of_benchmark, len(trading_signals), maximum, minimum)
    stats.loc[0, 'sortino ratio'] = sortino(rate_of_benchmark, len(trading_signals), growth_rate, minimum)

    # 注意我使用止損限制來限制Long Position的數量
    # 並且在清倉時，我們一次性清除所有Position
    # 所以每個Long Position始終為一，Short Position不能超過止損限制
    stats.loc[0, 'numbers of longs'] = trading_signals['signals'].loc[trading_signals['signals'] == 1].count()
    stats.loc[0, 'numbers of shorts'] = trading_signals['signals'].loc[trading_signals['signals'] < 0].count()
    stats.loc[0, 'numbers of trades'] = stats.loc[0, 'numbers of shorts'] + stats.loc[0, 'numbers of longs']  

    # 獲取交易的總長度
    # 因為 cumsum 表示持倉
    # 我們可以獲取所有可能的 cumsum 不等於零的情況
    # 然後我們計算有多少非零Position
    # 我們估計交易的總長度
    stats.loc[0, 'total length of trades'] = trading_signals['signals'].loc[trading_signals['cumsum'] != 0].count()
    stats.loc[0, 'average length of trades'] = stats.loc[0, 'total length of trades'] / stats.loc[0, 'numbers of trades'] if stats.loc[0, 'numbers of trades'] != 0 else 0
    stats.loc[0, 'profit per trade'] = (portfolio['total asset'].iloc[-1] - capital0) / stats.loc[0, 'numbers of trades'] if stats.loc[0, 'numbers of trades'] != 0 else 0

    print(stats)

# In[10]:

def main():
    
    # 初始化

    # 止損Position，能夠持有的最大Long Position
    # 如果沒有某些限制，只要市場狀況觸發信號，您將無限次地做多
    # 在波動市場中，這是自殺的
    stls = 3  # 設置止損限制
    ticker = sys.argv[1]  # 從命令行參數獲取第一個資產的代號 股票代碼
    stdate = sys.argv[2]  # 從命令行參數獲取開始日期
    eddate = sys.argv[3]  # 從命令行參數獲取結束日期
    output_dir = sys.argv[4]  # 從命令行參數獲取輸出目錄

    # slicer 用於繪圖
    # 一個三年的數據集有750個數據點會太多
    slicer = 700  # 設置繪圖的數據點範圍

    # 下載數據
    df = yf.download(ticker, start=stdate, end=eddate)

    trading_signals = signal_generation(df, heikin_ashi, stls)

    viz = trading_signals[slicer:]
    plot_details = plot(viz, ticker, output_dir)  # 圖一

    portfolio_details = portfolio(viz)
    portfolio_details_img = profit(portfolio_details, output_dir)  # 圖二

    stats(portfolio_details, trading_signals, stdate, eddate)

    print(f"Analysis completed for {ticker} from {stdate} to {eddate}")  # 打印分析完成信息
    print("The results have been plotted and saved as images.")  # 打印保存圖表信息
    print(f"Positions plot saved at: {plot_details}")  # 打印交易信號圖表保存路徑
    print(f"Portfolio plot saved at: {portfolio_details_img}")  # 打印投資組合績效圖表保存路徑
    # 注意這是唯一包含完整統計計算的 py 文件
    
if __name__ == '__main__':
    main()  # 執行主函數
