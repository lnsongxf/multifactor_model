# -*- coding: utf-8 -*-
"""
@author: shenyijia hanchao lei
"""

class BaseFunc:
    def unique_index(list,value):
        return [i for (i,v) in enumerate(list) if v==value]

    def TimeFormat(x):
        if x.find('/') != -1:
            return '%Y/%m/%d'
        if x.find('-') != -1:
            return '%Y-%m-%d'

class MultiFactor:
    def __init__(self,factorpath,factorname,tradeinterval):
        self.factorpath = factorpath
        self.factorname = factorname
        self.tradeinterval = tradeinterval

    def FactorInform(self):
        import os
        import pandas as pd
        files = os.listdir(self.factorpath)
        files.sort()
        factor_file = []
        factor_split = pd.DataFrame(columns=['asset','factorname','group','tradeinterval','frequency','author','date','datatype'])
        j = 0
        # extract correct factor files, 1)included in factorname; 2)correct tradeinterval; 3)raw data (not signal)
        for i in files:
            if (i.find(".csv") == -1) or (i.find(self.tradeinterval) == -1):
                continue
            exist = False
            for k in self.factorname:
                if i.find(k) != -1:
                    exist = True
                    break
            if exist == False:
                continue
            if i.split('.')[0].split('_')[-1] != 'raw':
                continue
            factor_file.append(i.split('.')[0])
            factor_split.loc[j] = factor_file[-1].split('_')
            j += 1
        self.factor_file = factor_file
        self.factor_split = factor_split
        self.assettype = list(set(factor_split.loc[:,'asset']))
        self.assettype.sort()

    def FactorData(self,factorname,compindex):
        import pandas as pd
        from datetime import datetime
        factor_data = pd.DataFrame()
        for i in compindex:
            tempfactor = pd.DataFrame(pd.read_csv(self.factorpath+'/'+self.factor_file[i]+'.csv'))
            tempfactor.loc[:,'date'] = tempfactor.loc[:,'date'].apply(lambda x:datetime.strptime(x,BaseFunc.TimeFormat(x)).date())
            tempfactor = tempfactor.set_index('date')
            tempfactor = tempfactor.rename(columns={self.factor_split.loc[i,'factorname']:self.factor_split.loc[i,'asset']})
            factor_data = pd.merge(factor_data,tempfactor.loc[:,self.factor_split.loc[i,'asset']],how="outer",left_index=True,right_index=True)
        startdate = factor_data.index[-1]
        for i in factor_data.index:
            if sum(factor_data.loc[i,:].apply(lambda x:pd.isna(x))) == 0:
                startdate = i
                break
        factor_data = factor_data.loc[factor_data.index>=startdate,:]
        factor_data.columns = pd.MultiIndex.from_product([[factorname],factor_data.columns],names=['factorname','asset'])
        return factor_data

    def FactorRank(self,factor_data):
        import pandas as pd
        from scipy.stats import rankdata
        factor_rank = pd.DataFrame(columns=factor_data.columns,index=factor_data.index)
        for i in factor_rank.index:
            factor_rank.loc[i,factor_data.loc[i,:].isnull()==False] = rankdata(list(factor_data.loc[i,factor_data.loc[i,:].isnull()==False]),'average')
        return factor_rank

    def GetMultiFactor(self):
        import pandas as pd
        self.FactorInform()
        self.factor_data = pd.DataFrame()
        self.factor_rank = pd.DataFrame()
        for i in self.factorname:
            compindex = BaseFunc.unique_index(self.factor_split.loc[:,'factorname'],i)
            compfactordata = self.FactorData(i,compindex)
            compfactorrank = self.FactorRank(compfactordata)
            if self.factor_data.empty == True:
                self.factor_data = compfactordata
                self.factor_rank = compfactorrank
            else:
                self.factor_data = pd.merge(self.factor_data,compfactordata,how='inner',left_index=True,right_index=True)
                self.factor_rank = pd.merge(self.factor_rank,compfactorrank,how='inner',left_index=True,right_index=True)
        self.startdate = self.factor_data.index[0]
        self.enddate = self.factor_data.index[-1]
