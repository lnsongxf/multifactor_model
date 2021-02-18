# -*- coding: utf-8 -*-
"""
@author: shenyijia hanchao lei
"""


# 暂时不包含因子筛选机制
class FactorScore:
    def __init__(self,return_data,factor_return,factor_calmar,factor_rank,factor_split,assettype,factor_cmrthd,factor_wgtlen,factor_wgtmtd,factor_model):
        self.return_data = return_data
        self.factor_return = factor_return
        self.factor_calmar = factor_calmar
        self.factor_rank = factor_rank
        self.factor_split = factor_split
        self.assettype = assettype
        self.factor_cmrthd = factor_cmrthd
        self.factor_wgtlen = factor_wgtlen
        self.factor_wgtmtd = factor_wgtmtd
        self.factor_model = factor_model

    def FactorIC(self):
        import pandas as pd
        factor_IC = pd.DataFrame(columns=self.factor_return.columns,index=self.factor_return.index)
        nexttradeindex = 1
        for i in factor_IC.index[:-1]:
            for j in factor_IC.columns:
                tempfactor = self.factor_rank.loc[i,[(j,k) for k in self.assettype]]
                tempreturn = self.return_data.loc[factor_IC.index[nexttradeindex],self.assettype]
                tempfactor.index = tempreturn.index
                tempfactor.name = tempreturn.name
                factor_IC.loc[i,j] = tempfactor.corr(tempreturn,'spearman')
            nexttradeindex += 1
        self.factor_IC = factor_IC

    def FactorWeight(self):
        import pandas as pd
        import numpy as np
        import math
        weight_start = self.factor_rank.index[self.factor_wgtlen]
        factor_weight = pd.DataFrame(columns=self.factor_return.columns,index=self.factor_return.index[self.factor_return.index>=weight_start])
        factor_group = pd.DataFrame(columns=['group'],index=self.factor_return.columns)
        for i in factor_group.index:
            factor_group.loc[i,'group'] = self.factor_split.loc[self.factor_split.loc[:,'factorname']==i,'group'].iloc[0]
        factor_choose = pd.DataFrame(index=factor_weight.index,columns=['choose'])
        for i in factor_choose.index:
            if sum(self.factor_calmar.loc[i,:].apply(lambda x:pd.isna(x))) == 0:
                factor_choose.loc[i,'choose'] = self.factor_calmar.loc[i,self.factor_calmar.loc[i,:]>=self.factor_cmrthd].index.tolist()
            else:
                factor_choose.loc[i,'choose'] = self.factor_calmar.columns.tolist()
        if self.factor_wgtmtd == "EqualWeight":
            for i in factor_weight.index:
                factor_weight.loc[i,factor_choose.loc[i,'choose']] = 1/len(factor_choose.loc[i,'choose'])
        if self.factor_wgtmtd == "GroupEqualWeight":
            for i in factor_weight.index:
                chooselist = factor_choose.loc[i,'choose']
                grouptype = list(set(factor_group.loc[chooselist,'group']))
                groupnum = []
                for j in grouptype:
                    tempfactor_uc = factor_group.loc[factor_group.loc[:,'group']==j,'group'].index.tolist()
                    tempfactor_c = [l for l in chooselist if l in tempfactor_uc]
                    groupnum.append(len(tempfactor_c))
                    factor_weight.loc[i,tempfactor_c] = math.sqrt(len(tempfactor_c))/len(tempfactor_c)
                factor_weight.loc[i,chooselist] = factor_weight.loc[i,chooselist]/sum(factor_weight.loc[i,chooselist])
        if self.factor_wgtmtd == "MaxIR":
            self.FactorIC()
            from MeanVariance import MeanVariance
            for i in factor_weight.index:
                idIC = list(self.factor_IC.index).index(i)
                MV = MeanVariance(self.factor_IC[factor_choose.loc[i,'choose']].iloc[(idIC-self.factor_wgtlen):idIC,:])
                factor_weight.loc[i,factor_choose.loc[i,'choose']] = MV.MaxSharpeWeight()
        if self.factor_wgtmtd == "MeanVariance":
            from MeanVariance import MeanVariance
            for i in factor_weight.index:
                idreturn = list(self.factor_return.index).index(i)
                MV = MeanVariance(self.factor_return[factor_choose.loc[i,'choose']].iloc[(idreturn-self.factor_wgtlen+1):(idreturn+1),:])
                factor_weight.loc[i,factor_choose.loc[i,'choose']] = MV.MaxSharpeWeight()
        if self.factor_wgtmtd == "RiskParity":
            import riskparityportfolio as rpp
            for i in factor_weight.index:
                idreturn = list(self.factor_return.index).index(i)
                sigma = np.asarray(self.factor_return[factor_choose.loc[i,'choose']].iloc[(idreturn-self.factor_wgtlen+1):(idreturn+1),:].astype(float).cov())
                my_rpp = rpp.RiskParityPortfolio(covariance=sigma)
                factor_weight.loc[i,factor_choose.loc[i,'choose']] = my_rpp.weights
        if self.factor_wgtmtd == "GroupRiskParity":
            import riskparityportfolio as rpp
            for i in factor_weight.index:
                chooselist = factor_choose.loc[i,'choose']
                grouptype = list(set(factor_group.loc[chooselist,'group']))
                idreturn = list(self.factor_return.index).index(i)
                tempdata_in = self.factor_return[chooselist].iloc[(idreturn-self.factor_wgtlen+1):(idreturn+1),:]
                tempdata_out = pd.DataFrame(index=tempdata_in.index,columns=grouptype)
                tempweight_in = pd.DataFrame(index=chooselist,columns=['weight'])
                tempweight_out = pd.DataFrame(index=grouptype,columns=['weight'])
                for j in grouptype:
                    tempfactor_uc = factor_group.loc[factor_group.loc[:,'group']==j,'group'].index.tolist()
                    tempfactor_c = [l for l in chooselist if l in tempfactor_uc]
                    if len(tempfactor_c) == 1:
                        tempweight_in.loc[tempfactor_c[0],'weight'] = 1
                        tempdata_out.loc[:,j] = tempdata_in.loc[:,tempfactor_c[0]]
                    else:
                        sigma = np.asarray(tempdata_in.loc[:,tempfactor_c].astype(float).cov())
                        my_rpp = rpp.RiskParityPortfolio(covariance=sigma)
                        tempweight_in.loc[tempfactor_c,'weight'] = my_rpp.weights
                        tempdata_out.loc[:,j] = (tempdata_in.loc[:,tempfactor_c]*tempweight_in.loc[tempfactor_c,'weight']).sum(axis=1)
                sigma = np.asarray(tempdata_out.astype(float).cov())
                my_rpp = rpp.RiskParityPortfolio(covariance=sigma)
                tempweight_out.loc[:,'weight'] = my_rpp.weights
                for j in grouptype:
                    tempfactor_uc = factor_group.loc[factor_group.loc[:,'group']==j,'group'].index.tolist()
                    tempfactor_c = [l for l in chooselist if l in tempfactor_uc]
                    tempweight_in.loc[tempfactor_c,'weight'] = tempweight_in.loc[tempfactor_c,'weight']*tempweight_out.loc[j,'weight']
                factor_weight.loc[i,chooselist] = tempweight_in.loc[chooselist,'weight']
        if self.factor_wgtmtd == "VolReverse":
            for i in factor_weight.index:
                idreturn = list(self.factor_return.index).index(i)
                vol = self.factor_return.iloc[(idreturn-self.factor_wgtlen+1):(idreturn+1),factor_choose.loc[i,'choose']].std(axis=0)
                tempweight = vol.apply(lambda x:1/x)
                factor_weight.loc[i,factor_choose.loc[i,'choose']] = tempweight/sum(tempweight)
        factor_weight = factor_weight.fillna(0)
        self.factor_weight = factor_weight

    def GetTotalScore(self):
        import pandas as pd
        import numpy as np
        self.FactorWeight()
        factor_score = pd.DataFrame(index=self.factor_weight.index,columns=self.assettype)
        if self.factor_model == "MultiScore":
            for i in factor_score.columns:
                temprank = self.factor_rank.loc[:,(self.factor_weight.columns,i)]
                for j in factor_score.index:
                    factor_score.loc[j,i] = np.dot(self.factor_weight.loc[j,:],temprank.loc[j,:])
        if self.factor_model == "MultiSignal":
            print('lack of code')
        self.factor_score = factor_score
