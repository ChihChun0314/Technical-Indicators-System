# -*- coding: utf-8 -*-
"""
Created on Tue Feb  6 11:57:46 2018

@author: Administrator
"""

# In[1]:

#need to get fix yahoo finance package first

import matplotlib.pyplot as plt  # �ɤJø�Ϯw
import numpy as np  # �ɤJ�ƾڳB�z�w
import pandas as pd  # �ɤJ�ƾڤ��R�w
import yfinance as yf  # �ɤJyahoo finance�ƾڥ]
import sys  # �ɤJ�t�ήw
import os  # �ɤJ�ާ@�t�ήw


# In[2]:

#simple moving average
# ²�沾�ʥ����u
def macd(signals, ma1, ma2):
    signals['ma1'] = signals['Close'].rolling(window=ma1, min_periods=1, center=False).mean()  # �p��u�����ʥ����u
    signals['ma2'] = signals['Close'].rolling(window=ma2, min_periods=1, center=False).mean()  # �p��������ʥ����u
    return signals  # ��^�]�t���ʥ����u���ƾڮ�


# In[3]:

#signal generation
#when the short moving average is larger than long moving average, we long and hold
#when the short moving average is smaller than long moving average, we clear positions
#the logic behind this is that the momentum has more impact on short moving average
#we can subtract short moving average from long moving average
#the difference between is sometimes positive, it sometimes becomes negative
#thats why it is named as moving average converge/diverge oscillator
# ����H���ͦ����
def signal_generation(df, ma1, ma2, method):
    signals = method(df, ma1, ma2)  # �p�Ⲿ�ʥ����u
    signals['positions'] = 0   # ��l�ƫ���

    #positions becomes and stays one once the short moving average is above long moving average
    # ��u�����ʥ����u����������ʥ����u�ɡA���ܬ�1�]���h�^
    signals['positions'][ma1:] = np.where(signals['ma1'][ma1:] >= signals['ma2'][ma1:], 1, 0)

    #as positions only imply the holding
    #we take the difference to generate real trade signal
    # ���ͥ���H��
    signals['signals'] = signals['positions'].diff()

    #oscillator is the difference between two moving average
    #when it is positive, we long, vice versa
    # �p�⮶����
    signals['oscillator'] = signals['ma1'] - signals['ma2']

    return signals # ��^�]�t�H�����ƾڮ�


# In[4]:

#plotting the backtesting result
# ø�s�^�����G�����
def plot(new, ticker, output_dir):
    # �T�O��X�ؿ��s�b
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    #the first plot is the actual close price with long/short positions
    # ø�s���L���Υ���H��
    fig = plt.figure()
    ax = fig.add_subplot(111)

    new['Close'].plot(label=ticker)  # ø�s���L��
    ax.plot(new.loc[new['signals'] == 1].index, new['Close'][new['signals'] == 1], label='LONG', lw=0, marker='^', c='g')  # ø�s���h�H��
    ax.plot(new.loc[new['signals'] == -1].index, new['Close'][new['signals'] == -1], label='SHORT', lw=0, marker='v', c='r')  # ø�s���ūH��

    plt.legend(loc='best')  # �K�[�Ϩ�
    plt.grid(True)  # �K�[����
    plt.title('Positions')  # �K�[���D
    positions_path = os.path.join(output_dir, "output_positions_MACD.png")  # �]�w��X���|
    plt.savefig(positions_path)  # �O�s�Ϫ��Ϥ�
    plt.close(fig)  # �����Ϫ�H�`�٤��s

    #the second plot is long/short moving average with oscillator
    #note that i use bar chart for oscillator
    # ø�s���ʥ����u�M������
    fig = plt.figure()
    cx = fig.add_subplot(211)

    new['oscillator'].plot(kind='bar', color='r')  # ø�s������

    plt.legend(loc='best')  # �K�[�Ϩ�
    plt.grid(True)  # �K�[����
    plt.xticks([])  # ����x�b����
    plt.xlabel('')  # �M��x�b����
    plt.title('MACD Oscillator')  # �K�[���D

    bx = fig.add_subplot(212)

    new['ma1'].plot(label='ma1')  # ø�s�u�����ʥ����u
    new['ma2'].plot(label='ma2', linestyle=':')  # ø�s�������ʥ����u

    plt.legend(loc='best')  # �K�[�Ϩ�
    plt.grid(True)  # �K�[����
    macd_path = os.path.join(output_dir, "output_macd.png")  # �]�w��X���|
    plt.savefig(macd_path)  # �O�s�Ϫ��Ϥ�
    plt.close(fig)  # �����Ϫ�H�`�٤��s

    return positions_path, macd_path  # ��^�Ϥ����|




# In[5]:

def main():
    # ����R�O��Ѽ�
    ma1 = int(sys.argv[1])  # �u�����ʥ����u�����f�j�p
    ma2 = int(sys.argv[2])  # �������ʥ����u�����f�j�p
    stdate = sys.argv[3]  # �}�l���
    eddate = sys.argv[4]  # �������
    ticker = sys.argv[5]  # �Ѳ��N�X
    slicer = int(sys.argv[6])  # �Ω�����ƾڪ��Ѽ�
    output_dir = sys.argv[7]  # �����X�ؿ��Ѽ�

    # �U���ƾ�
    df = yf.download(ticker, start=stdate, end=eddate)

    # �ͦ�����H��
    new = signal_generation(df, ma1, ma2, macd)
    new = new[slicer:]  # �����ƾ�

    # ø�Ϩ�����Ϥ����|
    positions_path, macd_path = plot(new, ticker, output_dir)
    
    # ���L�@�ǿ�X���ˬd
    print(f"Analysis completed for {ticker} from {stdate} to {eddate}")
    print(f"MA1: {ma1}, MA2: {ma2}, Slicer: {slicer}")
    print("The results have been plotted and saved as images.")
    print(f"Positions plot saved at: {positions_path}")
    print(f"MACD plot saved at: {macd_path}")


#how to calculate stats could be found from my other code called Heikin-Ashi
# https://github.com/je-suis-tm/quant-trading/blob/master/heikin%20ashi%20backtest.py

if __name__ == '__main__':
    main()
