# -*- coding: utf-8 -*-
"""
@author: shenyijia Hanchao Lei
"""
class BaseFunc:
    def TimeFormat(x):
        if x.find('/') != -1:
            return '%Y/%m/%d'
        if x.find('-') != -1:
            return '%Y-%m-%d'

class AssetReturn:
    def __init__(self,dominantpath,datapath,assettype,startdate,enddate,tradeinterval):
        self.dominantpath = dominantpath
        self.datapath = datapath
        self.assettype = assettype
        self.startdate = startdate
        self.enddate = enddate
        self.tradeinterval = tradeinterval

    def Dominant(self):
        import pandas as pd
        from datetime import datetime
        from dateutil.relativedelta import relativedelta
        dominant = pd.DataFrame()
        for i in self.assettype:
            tempdomi = pd.DataFrame(pd.read_csv(self.dominantpath+'/'+i+'_Dominant.csv'))
            tempdomi.loc[:,'date'] = tempdomi.loc[:,'date'].apply(lambda x:datetime.strptime(x,BaseFunc.TimeFormat(x)).date())
            tempdomi = tempdomi.set_index('date')
            # 处理主力合约进入交割月的问题，目前预设下一个主力合约为下个月的（有色可用，如果有1/5/9的后续需要特殊处理）
            if tempdomi.iloc[-1,0][-4:] == datetime.strftime(tempdomi.index[-1],"%Y%m")[2:]:
                tempdomi.iloc[-1,0] = i+datetime.strftime(tempdomi.index[-1]+relativedelta(months=1),"%Y%m")[2:]
            j = tempdomi.shape[0]-2
            while j >= 0:
                if tempdomi.loc[tempdomi.index[j],'dominant'][-4:] == datetime.strftime(tempdomi.index[j],"%Y%m")[2:]:
                    tempdomi.loc[tempdomi.index[j],'dominant'] = tempdomi.loc[tempdomi.index[j+1],'dominant']
                j -= 1
            tempdomi = tempdomi.rename(columns={'dominant':i})
            dominant = pd.merge(dominant,tempdomi.loc[:,i],how="outer",left_index=True,right_index=True)
        dominant = dominant.loc[(dominant.index>=self.startdate)&(dominant.index<=self.enddate),:]
        self.dominant = dominant

    def GetReturnData(self):
        import pandas as pd
        from datetime import datetime
        self.Dominant()
        return_data = pd.DataFrame(columns=self.dominant.columns,index=self.dominant.index)
        TR_data = pd.DataFrame(columns=self.dominant.columns,index=self.dominant.index)
        tempcolumn = []
        for i in self.dominant.columns:
            tempcolumn.append(i+'_open')
            tempcolumn.append(i+'_close')
            tempcolumn.append(i+'_openlast')
        twap_data = pd.DataFrame(columns=tempcolumn,index=self.dominant.index)
        if self.tradeinterval == 'NONC':
            for i in return_data.columns:
                for j in return_data.index:
                    data = pd.read_csv(self.datapath+'/'+i+'/'+self.dominant.loc[j,i]+'_'+datetime.strftime(j,'%Y%m%d')+'.csv')
                    data.loc[:,'datetime'] = list(map(lambda x,y:datetime.strptime(x+' '+y,BaseFunc.TimeFormat(x)+' %H:%M:%S'),data.loc[:,'date'],data.loc[:,'time']))
                    data = data.loc[data.loc[:,'datetime']<datetime(j.year,j.month,j.day,9,0,0),:]
                    if data.shape[0] == 0:
                        return_data.loc[j,i] = 0
                    else:
                        data = data.reset_index(drop=True)
                        data0 = data.loc[0:4,['high','low','close']] #NO
                        price0 = data0.sum().sum()/15
                        data1 = data.loc[(data.shape[0]-5):data.shape[0],['high','low','close']] #NC
                        price1 = data1.sum().sum()/15
                        return_data.loc[j,i] = (price1-price0)/price0
        else:
            for i in return_data.columns:
                for j in range(1,return_data.shape[0]):
                    data0 = pd.read_csv(self.datapath+'/'+i+'/'+self.dominant.loc[return_data.index[j],i]+'_'+datetime.strftime(return_data.index[j-1],'%Y%m%d')+'.csv')
                    data1 = pd.read_csv(self.datapath+'/'+i+'/'+self.dominant.loc[return_data.index[j],i]+'_'+datetime.strftime(return_data.index[j],'%Y%m%d')+'.csv')
                    high_today = data1.loc[:,'high'].max()
                    low_today = data1.loc[:,'low'].min()
                    close_lastday = data0['close'].iloc[-1]
                    close_today = data1['close'].iloc[-1]
                    TR_data.loc[return_data.index[j],i] = max([high_today-low_today,abs(high_today-close_lastday),abs(low_today-close_lastday)])/close_today
                    NO_twap1 = data1.loc[0:4,['high','low','close']].sum().sum()/15
                    AC_twap = data1.loc[(data1.shape[0]-5):data1.shape[0],['high','low','close']].sum().sum()/15
                    if self.tradeinterval == 'NONO':
                        if j != return_data.shape[0]-1:
                            data2 = pd.read_csv(self.datapath+'/'+i+'/'+self.dominant.loc[return_data.index[j],i]+'_'+datetime.strftime(return_data.index[j+1],'%Y%m%d')+'.csv')
                            NO_twap2 = data2.loc[0:4,['high','low','close']].sum().sum()/15
                        else:
                            NO_twap2 = AC_twap
                        return_data.loc[return_data.index[j],i] = (NO_twap2-NO_twap1)/NO_twap1
                    elif self.tradeinterval == 'NOAC':
                        return_data.loc[return_data.index[j],i] = (AC_twap-NO_twap1)/NO_twap1
                    else:
                        print('Error Trade Interval')
                    twap_data.loc[return_data.index[j],i+'_open'] = NO_twap1
                    twap_data.loc[return_data.index[j],i+'_close'] = AC_twap
                    if self.dominant.loc[return_data.index[j-1],i] != self.dominant.loc[return_data.index[j],i]:
                        data3 = pd.read_csv(self.datapath+'/'+i+'/'+self.dominant.loc[return_data.index[j-1],i]+'_'+datetime.strftime(return_data.index[j],'%Y%m%d')+'.csv')
                        twap_data.loc[return_data.index[j],i+'_openlast'] = data3.loc[0:4,['high','low','close']].sum().sum()/15
        self.return_data = return_data
        self.TR_data = TR_data
        self.twap_data = twap_data
