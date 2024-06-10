# -*- coding: utf-8 -*-

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yfinance as yf
import sys
import os

# ²�沾�ʥ����u
def macd(signals, ma1, ma2):
    signals['ma1'] = signals['Close'].rolling(window=ma1, min_periods=1, center=False).mean()
    signals['ma2'] = signals['Close'].rolling(window=ma2, min_periods=1, center=False).mean()
    return signals

# ����H���ͦ����
def signal_generation(df, ma1, ma2, method):
    signals = method(df, ma1, ma2)
    signals['positions'] = 0

    # ���`?��?��ĵ�i�A�̫O?�פ@�P
    signals.loc[signals.index[ma1:], 'positions'] = np.where(signals['ma1'][ma1:] >= signals['ma2'][ma1:], 1, 0)
    signals['signals'] = signals['positions'].diff()
    signals['oscillator'] = signals['ma1'] - signals['ma2']
    return signals

# ø�s�^�����G�����
def plot(new, ticker, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    fig = plt.figure()
    ax = fig.add_subplot(111)
    new['Close'].plot(label=ticker)
    ax.plot(new.loc[new['signals'] == 1].index, new['Close'][new['signals'] == 1], label='LONG', lw=0, marker='^', c='g')
    ax.plot(new.loc[new['signals'] == -1].index, new['Close'][new['signals'] == -1], label='SHORT', lw=0, marker='v', c='r')
    plt.legend(loc='best')
    plt.grid(True)
    plt.title('Positions')
    positions_path = os.path.join(output_dir, "output_positions_MACD.png")
    plt.savefig(positions_path)
    plt.close(fig)
    
    fig = plt.figure()
    cx = fig.add_subplot(211)
    new['oscillator'].plot(kind='bar', color='r')
    plt.legend(loc='best')
    plt.grid(True)
    plt.xticks([])
    plt.xlabel('')
    plt.title('MACD Oscillator')
    
    bx = fig.add_subplot(212)
    new['ma1'].plot(label='ma1')
    new['ma2'].plot(label='ma2', linestyle=':')
    plt.legend(loc='best')
    plt.grid(True)
    macd_path = os.path.join(output_dir, "output_macd.png")
    plt.savefig(macd_path)
    plt.close(fig)
    
    return positions_path, macd_path

def main():
    ma1 = int(sys.argv[1])
    ma2 = int(sys.argv[2])
    stdate = sys.argv[3]
    eddate = sys.argv[4]
    ticker = sys.argv[5]
    slicer = int(sys.argv[6])
    output_dir = sys.argv[7]
    
    df = yf.download(ticker, start=stdate, end=eddate)
    
    if df.empty:
        print(f"No data found for ticker {ticker} between {stdate} and {eddate}")
        return
    
    new = signal_generation(df, ma1, ma2, macd)
    new = new.iloc[slicer:]  # �ϥ�iloc�i�����
    
    positions_path, macd_path = plot(new, ticker, output_dir)
    
    print(f"Analysis completed for {ticker} from {stdate} to {eddate}")
    print(f"MA1: {ma1}, MA2: {ma2}, Slicer: {slicer}")
    print("The results have been plotted and saved as images.")
    print(f"Positions plot saved at: {positions_path}")
    print(f"MACD plot saved at: {macd_path}")

if __name__ == '__main__':
    main()
