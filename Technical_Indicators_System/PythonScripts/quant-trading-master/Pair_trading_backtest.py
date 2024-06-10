#pair trading is also called mean reversion trading
#we find two cointegrated assets, normally a stock and an ETF index
#or two stocks in the same industry or any pair that passes the test
#we run an cointegration test on the historical data
#we set the trigger condition for both stocks
#theoretically these two stocks cannot drift too far from each other
#its like a drunk man with a dog
#the invisible dog leash would keep both assets in check
#when one stock is getting too bullish
#we short the bullish one and long the bearish one, vice versa
#sooner or later, the dog would converge to the drunk man
#nevertheless, the backtest is based on historical datasets
#in real stock market, market conditions are dynamic
#two assets may seem cointegrated for the past two years
#they can completely diverge after one company launch a new product or whatsoever
#i am talking about nvidia and amd, two gpu companies
#after bitcoin mining boom and machine learning hype
#stock price of nvidia went skyrocketing
#on the contrary amd didnt change much 
#the cointegrated relationship just broke up
#so be extremely cautious with cointegration
#there is no such thing as riskless statistical arbitrage
#always check the cointegration status before trading execution
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yfinance as yf
import statsmodels.api as sm
import sys
import os
from datetime import datetime
import warnings
import json
# 忽略 FutureWarning 和 pandas 的 SettingWithCopyWarning 警告
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=pd.errors.SettingWithCopyWarning)

#use Engle-Granger two-step method to test cointegration
#the underlying method is straight forward and easy to implement
#a more important thing is the method is invented by the mentor of my mentor!!!
#the latest statsmodels package should ve included johansen test which is more common
#check sm.tsa.var.vecm.coint_johansen
#the malaise of two-step is the order of the cointegration
#unlike johansen test, two-step method can only detect the first order
#check the following material for further details
# https://warwick.ac.uk/fac/soc/economics/staff/gboero/personal/hand2_cointeg.pdf
# 使用 Engle-Granger 兩步法檢驗共整合
def EG_method(X, Y, show_summary=False):
    model1 = sm.OLS(Y, sm.add_constant(X)).fit()  # 建立並擬合 OLS 模型
    epsilon = model1.resid  # 獲取殘差

    if show_summary:
        print('\nStep 1\n')
        print(model1.summary())  # 顯示第一步模型的摘要

    # 檢查殘差的單位根檢驗結果
    if sm.tsa.stattools.adfuller(epsilon)[1] > 0.05:
        return False, model1  # 如果殘差的 ADF 檢驗結果 p 值大於 0.05，則認為沒有共整合關係

    X_dif = sm.add_constant(pd.concat([X.diff(), epsilon.shift(1)], axis=1).dropna())  # 計算 X 的一階差分和滯後殘差
    Y_dif = Y.diff().dropna()  # 計算 Y 的一階差分
    model2 = sm.OLS(Y_dif, X_dif).fit()  # 建立並擬合第二步 OLS 模型

    if show_summary:
        print('\nStep 2\n')
        print(model2.summary())  # 顯示第二步模型的摘要

    # 檢查第二步模型的調整係數
    if list(model2.params)[-1] > 0:
        return False, model1  # 如果調整係數為正，則認為沒有共整合關係
    else:
        return True, model1  # 否則，認為有共整合關係

#first we verify the status of cointegration by checking historical datasets
#bandwidth determines the number of data points for consideration
#bandwidth is 250 by default, around one year's data points
#if the status is valid, we check the signals
#when z stat gets above the upper bound
#we long the bearish one and short the bullish one, vice versa
# 生成交易信號
def signal_generation(asset1, asset2, method, bandwidth):
    signals = pd.DataFrame()  # 創建 DataFrame 來存儲信號
    signals['asset1'] = asset1['Close']  # 存儲第一個資產的收盤價
    signals['asset2'] = asset2['Close']  # 存儲第二個資產的收盤價

    signals['signals1'] = 0  # 初始化第一個資產的信號為 0
    signals['signals2'] = 0  # 初始化第二個資產的信號為 0

    prev_status = False  # 初始化前一個狀態為 False
    signals['z'] = np.nan  # 初始化 z 統計量為 NaN
    signals['z upper limit'] = np.nan  # 初始化 z 上限為 NaN
    signals['z lower limit'] = np.nan  # 初始化 z 下限為 NaN
    signals['fitted'] = np.nan  # 初始化擬合值為 NaN
    signals['residual'] = np.nan  # 初始化殘差為 NaN

    try:
        for i in range(bandwidth, len(signals)):  # 遍歷信號資料
            coint_status, model = method(signals['asset1'].iloc[i-bandwidth:i],
                                         signals['asset2'].iloc[i-bandwidth:i])  # 檢查共整合狀態

            if prev_status and not coint_status:  # 如果前一個狀態為 True 且當前狀態為 False
                if signals.at[signals.index[i-1], 'signals1'] != 0:  # 如果前一個信號不為 0
                    signals.loc[signals.index[i], ['signals1', 'signals2']] = 0  # 清除當前信號
                    signals.loc[signals.index[i]:, ['z', 'z upper limit', 'z lower limit', 'fitted', 'residual']] = np.nan  # 清除 z 統計量和其他變量

            if not prev_status and coint_status:  # 如果前一個狀態為 False 且當前狀態為 True
                try:
                    signals.loc[signals.index[i]:, 'fitted'] = model.predict(sm.add_constant(signals['asset1'].iloc[i:]))  # 計算擬合值
                    signals.loc[signals.index[i]:, 'residual'] = signals['asset2'].iloc[i:] - signals.loc[signals.index[i]:, 'fitted']  # 計算殘差
                    signals.loc[signals.index[i]:, 'z'] = (signals.loc[signals.index[i]:, 'residual'] - np.mean(model.resid)) / np.std(model.resid)  # 計算 z 統計量
                    signals.loc[signals.index[i]:, 'z upper limit'] = signals.loc[signals.index[i], 'z'] + np.std(model.resid)  # 設定 z 上限
                    signals.loc[signals.index[i]:, 'z lower limit'] = signals.loc[signals.index[i], 'z'] - np.std(model.resid)  # 設定 z 下限
                except Exception as e:
                    print(f"Error in signal processing at index {i}: {e}")
                    continue

            # 如果cointegration狀態為True，且當前z值超過z上限
            if coint_status and signals.loc[signals.index[i], 'z'] > signals.loc[signals.index[i], 'z upper limit']:
                signals.loc[signals.index[i], 'signals1'] = 1  # 設定做多信號，表示當前資產價格偏低，應該買入
            # 如果cointegration狀態為True，且當前z值低於z下限
            if coint_status and signals.loc[signals.index[i], 'z'] < signals.loc[signals.index[i], 'z lower limit']:
                signals.loc[signals.index[i], 'signals1'] = -1  # 設定做空信號，表示當前資產價格偏高，應該賣出

            prev_status = coint_status  # 更新前一個狀態
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        signals['positions1'] = signals['signals1'].diff()  # 計算第一個資產的倉位變動
        signals['signals2'] = -signals['signals1']  # 計算第二個資產的信號，方向相反
        signals['positions2'] = signals['signals2'].diff()  # 計算第二個資產的倉位變動
        return signals

# 繪製交易信號圖表
def plot(data, ticker1, ticker2, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)  # 如果輸出目錄不存在，則創建它
    fig = plt.figure(figsize=(10, 5))  # 創建圖表
    bx = fig.add_subplot(111)  # 創建主坐標軸
    bx2 = bx.twinx()  # 創建第二坐標軸

    asset1_price, = bx.plot(data.index, data['asset1'],
                            c='#113aac', alpha=0.7)  # 繪製第一個資產的價格
    asset2_price, = bx2.plot(data.index, data['asset2'],
                            c='#907163', alpha=0.7)  # 繪製第二個資產的價格

    asset1_long, = bx.plot(data.loc[data['positions1'] == 1].index,
                           data['asset1'][data['positions1'] == 1],
                           lw=0, marker='^', markersize=8,
                           c='g', alpha=0.7)  # 繪製第一個資產的做多信號
    asset1_short, = bx.plot(data.loc[data['positions1'] == -1].index,
                            data['asset1'][data['positions1'] == -1],
                            lw=0, marker='v', markersize=8,
                            c='r', alpha=0.7)  # 繪製第一個資產的做空信號
    asset2_long, = bx2.plot(data.loc[data['positions2'] == 1].index,
                            data['asset2'][data['positions2'] == 1],
                            lw=0, marker='^', markersize=8,
                            c='g', alpha=0.7)  # 繪製第二個資產的做多信號
    asset2_short, = bx2.plot(data.loc[data['positions2'] == -1].index,
                             data['asset2'][data['positions2'] == -1],
                             lw=0, marker='v', markersize=8,
                             c='r', alpha=0.7)  # 繪製第二個資產的做空信號

    bx.set_ylabel(ticker1, )  # 設定第一個資產的 Y 軸標籤
    bx2.set_ylabel(ticker2, rotation=270)  # 設定第二個資產的 Y 軸標籤
    bx.yaxis.labelpad = 15  # 設定 Y 軸標籤的填充
    bx2.yaxis.labelpad = 15  # 設定第二個 Y 軸標籤的填充
    bx.set_xlabel('Date')  # 設定 X 軸標籤
    bx.xaxis.labelpad = 15  # 設定 X 軸標籤的填充

    plt.legend([asset1_price, asset2_price, asset1_long, asset1_short],
               [ticker1, ticker2,
                'LONG', 'SHORT'],
               loc='lower left')  # 添加圖例

    plt.title('Pair Trading')  # 設定圖表標題
    plt.xlabel('Date')  # 設定 X 軸標籤
    plt.grid(True)  # 顯示網格線
    positions_path_Pair = os.path.join(output_dir, "output_positions_Pair.png")  # 設定圖表保存路徑
    plt.savefig(positions_path_Pair)  # 保存圖表
    plt.close(fig)  # 關閉圖表
    return positions_path_Pair  # 返回圖表保存路徑

# 繪製投資組合績效圖表
def portfolio(data, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)  # 如果輸出目錄不存在，則創建它

    capital0 = 20000  # 初始資本

    positions1 = capital0 // max(data['asset1'])  # 計算第一個資產的倉位數量
    positions2 = capital0 // max(data['asset2'])  # 計算第二個資產的倉位數量

    data = data.copy()  # 確保 data 是一個副本而不是原始數據的視圖
    data.loc[:, 'cumsum1'] = data['positions1'].cumsum()  # 計算第一個資產的累積倉位
    data.loc[:, 'cumsum2'] = data['positions2'].cumsum()  # 計算第二個資產的累積倉位

    portfolio = pd.DataFrame()  # 創建 DataFrame 來存儲投資組合數據
    portfolio['asset1'] = data['asset1']  # 存儲第一個資產的價格
    portfolio['holdings1'] = data['cumsum1'] * data['asset1'] * positions1  # 計算第一個資產的持倉價值
    portfolio['cash1'] = capital0 - (data['positions1'] * data['asset1'] * positions1).cumsum()  # 計算第一個資產的現金
    portfolio['total asset1'] = portfolio['holdings1'] + portfolio['cash1']  # 計算第一個資產的總資產
    portfolio['return1'] = portfolio['total asset1'].pct_change()  # 計算第一個資產的回報率
    portfolio['positions1'] = data['positions1']  # 存儲第一個資產的倉位

    portfolio['asset2'] = data['asset2']  # 存儲第二個資產的價格
    portfolio['holdings2'] = data['cumsum2'] * data['asset2'] * positions2  # 計算第二個資產的持倉價值
    portfolio['cash2'] = capital0 - (data['positions2'] * data['asset2'] * positions2).cumsum()  # 計算第二個資產的現金
    portfolio['total asset2'] = portfolio['holdings2'] + portfolio['cash2']  # 計算第二個資產的總資產
    portfolio['return2'] = portfolio['total asset2'].pct_change()  # 計算第二個資產的回報率
    portfolio['positions2'] = data['positions2']  # 存儲第二個資產的倉位

    portfolio['z'] = data['z']  # 存儲 z 統計量
    portfolio['total asset'] = portfolio['total asset1'] + portfolio['total asset2']  # 計算總資產
    portfolio['z upper limit'] = data['z upper limit']  # 存儲 z 上限
    portfolio['z lower limit'] = data['z lower limit']  # 存儲 z 下限

    fig = plt.figure(figsize=(10, 5))  # 創建圖表
    ax = fig.add_subplot(111)  # 創建主坐標軸
    ax2 = ax.twinx()  # 創建第二坐標軸

    total_asset_performance, = ax.plot(portfolio['total asset'], c='#46344e')  # 繪製總資產績效
    z_stats, = ax2.plot(portfolio['z'], c='#4f4a41', alpha=0.2)  # 繪製 z 統計量

    threshold = ax2.fill_between(portfolio.index, portfolio['z upper limit'],
                                 portfolio['z lower limit'],
                                 alpha=0.2, color='#ffb48f')  # 繪製 z 統計量區間

    ax.set_ylabel('Asset Value')  # 設定主坐標軸的 Y 軸標籤
    ax2.set_ylabel('Z Statistics', rotation=270)  # 設定第二坐標軸的 Y 軸標籤
    ax.yaxis.labelpad = 15  # 設定 Y 軸標籤的填充
    ax2.yaxis.labelpad = 15  # 設定第二 Y 軸標籤的填充
    ax.set_xlabel('Date')  # 設定 X 軸標籤
    ax.xaxis.labelpad = 15  # 設定 X 軸標籤的填充

    plt.legend([z_stats, threshold, total_asset_performance],
               ['Z Statistics', 'Z Statistics +-1 Sigma',
                'Total Asset Performance'], loc='best')  # 添加圖例

    plt.grid(True)  # 顯示網格線
    plt.title('Total Asset')  # 設定圖表標題
    pair_path = os.path.join(output_dir, "output_Pair_portfolio.png")  # 設定圖表保存路徑
    plt.savefig(pair_path)  # 保存圖表
    plt.close(fig)  # 關閉圖表

    return pair_path  # 返回圖表保存路徑

# 計算開始日期和結束日期之間的天數
def calculate_days(start_date, end_date):
    """
    計算開始日期和結束日期之間的天數。

    :param start_date: 開始日期（格式：'YYYY-MM-DD'）
    :param end_date: 結束日期（格式：'YYYY-MM-DD'）
    :return: 天數
    """
    start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')  # 將開始日期字串轉換為 datetime 對象
    end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')  # 將結束日期字串轉換為 datetime 對象
    
    delta = end_date_obj - start_date_obj  # 計算日期之間的差異
    
    return delta.days  # 返回天數

# 主函數
def main():
    
    stdate = sys.argv[1]  # 從命令行參數獲取開始日期
    eddate = sys.argv[2]  # 從命令行參數獲取結束日期
    ticker1 = sys.argv[3]  # 從命令行參數獲取第一個資產的代號
    ticker2 = sys.argv[4]  # 從命令行參數獲取第二個資產的代號
    output_dir = sys.argv[5]  # 從命令行參數獲取輸出目錄
    
    asset1 = yf.download(ticker1, start=stdate, end=eddate)  # 下載第一個資產的數據
    asset2 = yf.download(ticker2, start=stdate, end=eddate)  # 下載第二個資產的數據

    if asset1.empty or asset2.empty:  # 如果任一資產數據為空，則打印錯誤信息並返回
        print("No data for one or both of the assets.")
        return

    days = int(calculate_days(stdate, eddate) / 3)  # 計算時間跨度並除以 3
    print('-----------------------'+str(days)+'--------------------------')  # 打印天數

    signals = signal_generation(asset1, asset2, EG_method, days)  # 生成交易信號

    if signals is None or signals['z'].dropna().empty:  # 如果沒有生成交易信號，則打印信息並返回
        print("-----------------------No trading signals generated.----------------------------")
        return

    ind = signals['z'].dropna().index[0]  # 獲取第一個有效信號的索引

    plot_details = plot(signals[ind:], ticker1, ticker2, output_dir)  # 繪製交易信號圖表
    portfolio_details = portfolio(signals[ind:], output_dir)  # 繪製投資組合績效圖表

    print(f"Analysis completed for {ticker1} and {ticker2} from {stdate} to {eddate}")  # 打印分析完成信息
    print("The results have been plotted and saved as images.")  # 打印保存圖表信息
    print(f"Positions plot saved at: {plot_details}")  # 打印交易信號圖表保存路徑
    print(f"Portfolio plot saved at: {portfolio_details}")  # 打印投資組合績效圖表保存路徑
    


if __name__ == '__main__':
    main()  # 執行主函數
