# -*- coding: utf-8 -*-
"""

@author: shen jiayi hanchao lei
"""

import pandas as pd
from datetime import datetime,date

system = "linux_sub"
if system == "linux_sub":
    path = r"/mnt/d"
elif system == "windows":
    path = r"D:"
else:
    print("Incorrect system!")
codepath = path+"/MultiFactor/PYcode/NONO_FactorRank_MultiScore"
# factorpath = path+"/Factor/multi"
factorpath = path+"/Multifactor/PYcode/factor/Factor_20201230"
dominantpath = path+"/RQData/Dominant"
datapath = path+"/RQData/DailyData/1M"
marginpath = path+'/Multifactor/PYcode/factor'
minpricepath = path+"/Multifactor/PYcode/minprice"
outputpath = path+"/Multifactor/PYcode/output/MultiFactor/20210113_NONO_ModelTest/OutputTest"

factorname = ["BasisRatio","CapitalFlow","Momentum","Reverse","RollYield","Stocks","WarrantChange"]
tradeinterval_pool = ['NONC','NOAC','NONO']
factor_wgtmtd_pool = ['EqualWeight','GroupEqualWeight','MaxIR','MeanVariance','RiskParity','GroupRiskParity','VolReverse'] #factor weight allocation
factor_model_pool = ['MultiScore','MultiSignal'] #factor model
asset_wgtmtd_pool = ['RankWeight','ScoreWeight','MedianWeight','MeanWeight','EqualWeight']
asset_wgtadj_pool = [None,'ATRinverse','VOLinverse','PTVadjust']
asset_smtmtd_pool = [None,'SMA','WMA','EMA','OptBound1','OptBound2']

tradeinterval = tradeinterval_pool[2] #NONO
factor_cmrlen = 240
factor_cmrthd = -1
factor_wgtmtd = factor_wgtmtd_pool[4] #RiskParity
factor_wgtlen = 120
factor_model = factor_model_pool[0] #MultiScore
transfeepct = 0.0005
initfund = 100000000
backtest_startdate = date(2017,1,1)
asset_wgtmtd = asset_wgtmtd_pool[3] #MeanWeight
asset_wgtadj = asset_wgtadj_pool[2] #VOLinverse
asset_wgtpara = 240
asset_smtmtd = asset_smtmtd_pool[5]
asset_smtlen = 0.6
lotround = False
holidaylen = [3,4,5]
holidaypct = [1.0,1.0,1.0]
stoploss = False
threshold_intra = -0.018
threshold_inter = -0.019


import sys
sys.path.append(codepath)

# get factor data
import MultiFactor
Mf = MultiFactor.MultiFactor(factorpath,factorname,tradeinterval)
Mf.GetMultiFactor()

# 数据长度需再定，因为计算ATR和Vol要用到历史长度的数据
# get asset return
import AssetReturn
Ar = AssetReturn.AssetReturn(dominantpath,datapath,Mf.assettype,date(2015,3,27),Mf.enddate,tradeinterval)
Ar.GetReturnData()

# construct single factor strategy
import SingleFactorReturn
Sfr = SingleFactorReturn.SingleFactorReturn(factorname,Mf.factor_rank,Ar.return_data,factor_cmrlen)
Sfr.GetFactorCalmar()

import MarginRatio
Mr = MarginRatio.MarginRatio(Ar.dominant,marginpath)
Mr.GetMarginRatio()

import FactorScore
Fs = FactorScore.FactorScore(Ar.return_data,Sfr.factor_return,Sfr.factor_calmar,Mf.factor_rank,Mf.factor_split,Mf.assettype,factor_cmrthd,factor_wgtlen,factor_wgtmtd,factor_model)
Fs.GetTotalScore()

import AssetRealLot
Arl = AssetRealLot.AssetRealLot(Fs.factor_score,Ar.return_data,Ar.TR_data,Ar.twap_data,factor_model,asset_wgtmtd,asset_wgtadj,asset_wgtpara,asset_smtmtd,asset_smtlen,\
                                      initfund,lotround,holidaylen,holidaypct,backtest_startdate)
Arl.GetAssetLot()

import MinutePrice
Mp = MinutePrice.MinutePrice(Arl.asset_lotsmt.index[:-1],Arl.asset_lotsmt.columns,Ar.dominant,datapath,minpricepath)
Mp.GetMinPrice()

if stoploss == True:
    import PortfolioReturn_Stop
    Pr = PortfolioReturn_Stop.PortfolioReturn_Stop(initfund,Arl.asset_lotsmt,minpricepath,threshold_intra,threshold_inter,Ar.twap_data,Ar.return_data,transfeepct,Mr.marginpct)
    Pr.GetPortfolioReturn()
else:
    import PortfolioReturn
    Pr = PortfolioReturn.PortfolioReturn(initfund,Arl.asset_lotsmt,Ar.twap_data,Ar.return_data,transfeepct,Mr.marginpct)
    Pr.GetPortfolioReturn()

Pr.portfolio_return = Pr.portfolio_return.iloc[:-1,:]
Pr.portfolio_return.to_csv(outputpath+'/portfolio_return.csv',index=True)

import MultiFactorReturn_PPA
Mfrp = MultiFactorReturn_PPA.MultiFactorReturn_PPA(Pr.portfolio_return)
Mfrp.PerformData(0,0,250,0.05,outputpath)
Mfrp.performdata.to_csv(outputpath+'/performdata.csv',index=True)
Mfrp.CumDDPlot(outputpath+'/CumDDplot.jpg')
