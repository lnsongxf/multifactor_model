# -*- coding: utf-8 -*-
"""
@author: shenjia yi hanchao Lei
"""

class AssetRealLot:
    def __init__(self,factor_score,return_data,TR_data,twap_data,factor_model,asset_wgtmtd,asset_wgtadj,asset_wgtpara,asset_smtmtd,asset_smtlen,\
                 initfund,lotround,holidaylen,holidaypct,backtest_startdate):
        self.factor_score = factor_score
        self.return_data = return_data
        self.TR_data = TR_data
        self.twap_data = twap_data
        self.factor_model = factor_model
        self.asset_wgtmtd = asset_wgtmtd
        self.asset_wgtadj = asset_wgtadj
        self.asset_wgtpara = asset_wgtpara
        self.asset_smtmtd = asset_smtmtd
        self.asset_smtlen = asset_smtlen
        self.initfund = initfund
        self.lotround = lotround
        self.holidaylen = holidaylen
        self.holidaypct = holidaypct
        self.backtest_startdate = backtest_startdate

    def ContractSize(self,asset):
        consize = {
            'CU':5.0,
            'AL':5.0,
            'ZN':5.0,
            'PB':5.0,
            'NI':1.0,
            'SN':1.0
            }
        return consize[asset]

    def AssetWeight(self):
        import pandas as pd
        import numpy as np
        import math
        from scipy.stats import rankdata
        from datetime import timedelta
        from chinese_calendar import is_holiday
        import math
        asset_weight = pd.DataFrame(index=self.factor_score.index[self.factor_score.index>=self.backtest_startdate],columns=self.factor_score.columns)
        if self.factor_model == "MultiScore":
            # asset_wgtmtd
            if self.asset_wgtmtd == "RankWeight":
                n = (asset_weight.shape[1]+1)/2
                for i in asset_weight.index:
                    rank = rankdata(self.factor_score.loc[i,:])
                    tempweight = np.multiply([int(j>n) for j in rank],[j-math.floor(n) for j in rank])+np.multiply([int(j<n) for j in rank],[j-math.ceil(n) for j in rank])
                    asset_weight.loc[i,:] = tempweight/sum(abs(tempweight))
            if self.asset_wgtmtd == "ScoreWeight":
                n = (asset_weight.shape[1]+1)/2
                for i in asset_weight.index:
                    rank = rankdata(self.factor_score.loc[i,:])
                    long = [int(j>n) for j in rank]
                    short = [int(j<n) for j in rank]
                    long_score_sum = [j*np.sum(np.multiply(long,self.factor_score.loc[i,:])) for j in long]
                    short_score_sum = [j*np.sum(np.multiply(short,self.factor_score.loc[i,:])) for j in short]
                    empty = [int(j==n) for j in rank] # Prevent 0 / 0 when the number of varieties is odd
                    denominator = list(map(lambda x,y,z:x+y+z,long_score_sum,short_score_sum,empty))
                    molecule = np.multiply(long,self.factor_score.loc[i,:])+np.multiply(short,list(map(lambda x,y:(y-x)/(sum(short)-1),short_score_sum,self.factor_score.loc[i,:])))
                    asset_weight.loc[i,:] = molecule/denominator/2
            if self.asset_wgtmtd == "MedianWeight":
                factor_medianscore = self.factor_score.median(axis=1)
                for i in asset_weight.index:
                    tempweight = self.factor_score.loc[i,:]-factor_medianscore.loc[i]
                    asset_weight.loc[i,:] = tempweight/sum(abs(tempweight))
            if self.asset_wgtmtd == "MeanWeight":
                factor_meanscore = self.factor_score.mean(axis=1)
                for i in asset_weight.index:
                    tempweight = self.factor_score.loc[i,:]-factor_meanscore.loc[i]
                    asset_weight.loc[i,:] = tempweight/sum(abs(tempweight))
            if self.asset_wgtmtd == "EqualWeight":
                n = (asset_weight.shape[1]+1)/2
                for i in asset_weight.index:
                    rank = rankdata(self.factor_score.loc[i,:])
                    tempweight = np.array(list(map(lambda x,y:x-y,[int(j>n) for j in rank],[int(j<n) for j in rank])))
                    asset_weight.loc[i,:] = tempweight/sum(abs(tempweight))

            # asset_wgtadj
            if self.asset_wgtadj == "ATRinverse":
                #asset_wgtpara is length for compute ATR
                ATR_data = pd.DataFrame(index=self.return_data.index,columns=self.return_data.columns)
                ATR_data.loc[:,:] = self.TR_data.rolling(window=self.asset_wgtpara,axis=0).mean()
                for i in asset_weight.index:
                    ATRinv = list(map(lambda x:1/x,ATR_data.loc[i,:]))
                    tempweight = np.multiply(asset_weight.loc[i,:],ATRinv)
                    asset_weight.loc[i,:] = tempweight/sum(abs(tempweight))
            if self.asset_wgtadj == "VOLinverse":
                #asset_wgtpara is length for compute volatility
                voldata = pd.DataFrame(index=self.return_data.index,columns=self.return_data.columns)
                voldata.loc[:,:] = self.return_data.rolling(window=self.asset_wgtpara,axis=0).std()
                for i in asset_weight.index:
                    volinv = list(map(lambda x:1/x,voldata.loc[i,:]))
                    tempweight = np.multiply(asset_weight.loc[i,:],volinv)
                    asset_weight.loc[i,:] = tempweight/sum(abs(tempweight))
            if self.asset_wgtadj == "PTVadjust":
                #asset_wgtpara is list, first is length for compute volatility, second is targeted volatility
                for i in asset_weight.index:
                    tempindex = list(self.return_data.index).index(i)
                    tempreturn = self.return_data.iloc[(tempindex-self.asset_wgtpara[0]+1):(tempindex+1),:]
                    vol = tempreturn.std(axis=0)
                    corr = tempreturn.astype(float).corr()
                    dominator = np.dot(np.dot(asset_weight.loc[i,:].T,corr),asset_weight.loc[i,:])
                    asset_weight.loc[i,:] = self.asset_wgtpara[1]*asset_weight.loc[i,:]/(math.sqrt(dominator)*vol)
        if self.factor_model == "MultiSignal":
            #asset_wgtpara is list, first is length for compute volatility, second is targeted volatility
            for i in asset_weight.index:
                tempweight = self.factor_score.loc[i,:]/sum(abs(self.factor_score.loc[i,:]))
                tempindex = list(self.return_data.index).index(i)
                tempreturn = self.return_data.iloc[(tempindex-self.asset_wgtpara[0]+1):(tempindex+1),:]
                vol = tempreturn.std(axis=0)
                corr = tempreturn.astype(float).corr()
                dominator = np.dot(np.dot(tempweight.T,corr),tempweight)
                asset_weight.loc[i,:] = self.asset_wgtpara[1]*tempweight/(math.sqrt(dominator)*vol)

        asset_lot = pd.DataFrame(index=asset_weight.index,columns=asset_weight.columns)
        for i in asset_lot.index:
            for j in asset_lot.columns:
                asset_lot.loc[i,j] = self.initfund*asset_weight.loc[i,j]/(self.twap_data.loc[i,j+'_close']*self.ContractSize(j))

        # datetime index translation for asset_weight
        factorseries = list(asset_weight.index)
        weightseries = factorseries[1:]
        nexttradeday = weightseries[-1]+timedelta(days=1)
        while is_holiday(nexttradeday) or nexttradeday.weekday()==5 or nexttradeday.weekday()==6:
            nexttradeday += timedelta(days=1)
        weightseries.append(nexttradeday)
        asset_weight.index = weightseries
        asset_lot.index = weightseries
        self.asset_weight = asset_weight
        self.asset_lot = asset_lot

    def SolveBound1(self,x0,x1,value,bound):
        # x0: last time point - lot_smt
        # x1: this time point - lot
        # value: last time point - close price*contract size
        # bound: boundary
        import cvxopt as opt
        import numpy as np
        n = len(x0)
        P = 2*opt.matrix(np.eye(n))
        q = -2*opt.matrix(x0)
        G0 = opt.matrix(np.eye(n))
        G = opt.matrix(np.row_stack((G0,-G0,G0,-G0)))
        h1 = opt.matrix(x1)+bound*opt.matrix(np.abs(x1))
        h2 = -opt.matrix(x1)+bound*opt.matrix(np.abs(x1))
        h3 = opt.matrix(list(map(lambda x,y:max(x,y),x0,x1)))
        h4 = opt.matrix(list(map(lambda x,y:-min(x,y),x0,x1)))
        h = opt.matrix(np.row_stack((h1,h2,h3,h4)))
        long_loc = list(map(lambda x:float(x>0),x1))
        short_loc = list(map(lambda x:float(x<0),x1))
        A = opt.matrix([opt.matrix(value*long_loc,(1,n)),opt.matrix(value*short_loc,(1,n))])
        b = opt.matrix([np.sum(x1*long_loc*list(value)),np.sum(x1*short_loc*list(value))])
        opt.solvers.options['show_progress'] = False
        x2 = opt.solvers.qp(P,q,G,h,A,b)['x']
        x2 = x2*self.initfund/np.dot(np.abs(list(x2)),value)
        return x2

    def SolveBound2(self,x0,x1,value,bound):
        # x0: last time point - lot_smt
        # x1: this time point - lot
        # value: last time point - close price*contract size
        # bound: boundary
        import cvxopt as opt
        import numpy as np
        n = len(x0)
        P = 2*opt.matrix(np.eye(n))
        q = -2*opt.matrix(x0)
        G0 = opt.matrix(np.eye(n))
        G = opt.matrix(np.row_stack((G0,-G0,G0,-G0)))
        h1 = opt.matrix(x1)+bound*opt.matrix(np.abs(list(map(lambda x,y:x-y,x1,x0))))
        h2 = -opt.matrix(x1)+bound*opt.matrix(np.abs(list(map(lambda x,y:x-y,x1,x0))))
        h3 = opt.matrix(list(map(lambda x,y:max(x,y),x0,x1)))
        h4 = opt.matrix(list(map(lambda x,y:-min(x,y),x0,x1)))
        h = opt.matrix(np.row_stack((h1,h2,h3,h4)))
        long_loc = list(map(lambda x:float(x>0),x1))
        short_loc = list(map(lambda x:float(x<0),x1))
        A = opt.matrix([opt.matrix(value*long_loc,(1,n)),opt.matrix(value*short_loc,(1,n))])
        b = opt.matrix([np.sum(x1*long_loc*list(value)),np.sum(x1*short_loc*list(value))])
        opt.solvers.options['show_progress'] = False
        x2 = opt.solvers.qp(P,q,G,h,A,b)['x']
        x2 = x2*self.initfund/np.dot(np.abs(list(x2)),value)
        return x2

    def OptBound1(self,asset_lot,bound):
        import pandas as pd
        asset_lotsmt = pd.DataFrame(index=asset_lot.index,columns=asset_lot.columns)
        asset_lotsmt.iloc[0,:] = asset_lot.iloc[0,:]
        for i in range(1,asset_lotsmt.shape[0]):
            asset_lotsmt.iloc[i,:] = list(self.SolveBound1(asset_lotsmt.iloc[i-1,:],asset_lot.iloc[i,:],\
                                     self.twap_data.loc[asset_lot.index[i-1],asset_lot.columns+'_close']*[self.ContractSize(j) for j in asset_lot.columns],bound))
        return asset_lotsmt

    def OptBound2(self,asset_lot,bound):
        import pandas as pd
        asset_lotsmt = pd.DataFrame(index=asset_lot.index,columns=asset_lot.columns)
        asset_lotsmt.iloc[0,:] = asset_lot.iloc[0,:]
        for i in range(1,asset_lotsmt.shape[0]):
            asset_lotsmt.iloc[i,:] = list(self.SolveBound2(asset_lotsmt.iloc[i-1,:],asset_lot.iloc[i,:],\
                                     self.twap_data.loc[asset_lot.index[i-1],asset_lot.columns+'_close']*[self.ContractSize(j) for j in asset_lot.columns],bound))
        return asset_lotsmt

    def LotSmooth(self):
        import copy
        from chinese_calendar import is_holiday
        from datetime import timedelta
        asset_lotsmt = copy.deepcopy(self.asset_lot)
        if self.asset_smtmtd == 'SMA':
            for i in range(self.asset_smtlen-1,self.asset_lot.shape[0]):
                asset_lotsmt.iloc[i,:] = self.asset_lot.iloc[(i-self.asset_smtlen+1):(i+1),:].mean(axis=0)
        if self.asset_smtmtd == 'WMA':
            weight = list(range(1,self.asset_smtlen+1))
            sumwgt = sum(weight)
            for i in range(self.asset_smtlen-1,self.asset_lot.shape[0]):
                asset_lotsmt.iloc[i,:] = self.asset_lot.iloc[(i-self.asset_smtlen+1):(i+1),:].apply(lambda x:x*weight/sumwgt,axis=0).sum(axis=0)
        if self.asset_smtmtd == 'EMA':
            alpha = 2/(self.asset_smtlen+1)
            for i in range(1,self.asset_lot.shape[0]):
                asset_lotsmt.iloc[i,:] = alpha*self.asset_lot.iloc[i,:]+(1-alpha)*asset_lotsmt.iloc[i-1,:]
        if self.asset_smtmtd == 'OptBound1':
            asset_lotsmt.loc[:,:] = self.OptBound1(self.asset_lot.loc[:,:],self.asset_smtlen)
        if self.asset_smtmtd == 'OptBound2':
            asset_lotsmt.loc[:,:] = self.OptBound2(self.asset_lot.loc[:,:],self.asset_smtlen)
        #holiday lot reduce
        if type(self.holidaylen) != list:
            for i in range(asset_lotsmt.shape[0]-1):
                if (asset_lotsmt.index[i+1]-asset_lotsmt.index[i]).days > self.holidaylen:
                    asset_lotsmt.iloc[i,:] = self.holidaypct*asset_lotsmt.iloc[i,:]
            daydiff = 1
            while is_holiday(asset_lotsmt.index[-1]+timedelta(days=daydiff)):
                daydiff += 1
            if daydiff > self.holidaylen:
                asset_lotsmt.iloc[-1,:] = self.holidaypct*asset_lotsmt.iloc[-1,:]
        else:
            for i in range(asset_lotsmt.shape[0]-1):
                for j in range(len(self.holidaylen)):
                    if (asset_lotsmt.index[i+1]-asset_lotsmt.index[i]).days > self.holidaylen[-j-1]:
                        asset_lotsmt.iloc[i,:] = self.holidaypct[-j-1]*asset_lotsmt.iloc[i,:]
                        break
            daydiff = 1
            while is_holiday(asset_lotsmt.index[-1]+timedelta(days=daydiff)):
                daydiff += 1
            for j in range(len(self.holidaylen)):
                if daydiff > self.holidaylen[-j-1]:
                    asset_lotsmt.iloc[-1,:] = self.holidaypct[-j-1]*asset_lotsmt.iloc[-1,:]
                    break
        #lot round
        if self.lotround == True:
            for i in asset_lotsmt.index:
                for j in asset_lotsmt.columns:
                    asset_lotsmt.loc[i,j] = round(asset_lotsmt.loc[i,j])
        self.asset_lotsmt = asset_lotsmt

    def GetAssetLot(self):
        self.AssetWeight()
        self.LotSmooth()
