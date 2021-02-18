# -*- coding: utf-8 -*-
"""
Created on Wed Dec 14 17:56:12 2020

@author: shenyijia
"""

class MultiFactorReturn_PPA():
    def __init__(self,return_portfolio):
        self.return_portfolio = return_portfolio

    def GetDrawdown(self,returndata):
        import copy
        cumretdata = returndata.cumsum()
        maxcum = cumretdata.iloc[0,:]
        drawdowndata = copy.deepcopy(cumretdata)
        for i in range(cumretdata.shape[1]):
            for j in range(cumretdata.shape[0]):
                maxcum.iloc[i] = max(maxcum.iloc[i],cumretdata.iloc[j,i])
                drawdowndata.iloc[j,i] = cumretdata.iloc[j,i]-maxcum.iloc[i]
        return drawdowndata

    def CumReturn(self):
        return self.return_portfolio.cumsum().iloc[-1,:]
    
    def MeanReturn(self):
        return self.CumReturn()/self.return_portfolio.shape[0]
    
    def AnnualReturn(self,scale):
        return self.MeanReturn()*scale
    
    def MaxDrawdown(self):
        return -self.GetDrawdown(self.return_portfolio).min(axis=0)

    def SharpeRatio(self,rfrate,scale):
        import copy
        import pandas as pd
        import math
        sharpe = copy.deepcopy(self.MeanReturn())
        for i in range(self.return_portfolio.shape[1]):
            sharpe[i] = (sharpe[i]-rfrate)/pd.Series.std(self.return_portfolio.iloc[:,i],ddof=1)
        return sharpe*math.sqrt(scale)

    def SortinoRatio(self,MAR,scale):
        import copy
        import numpy as np
        import math
        sortino = copy.deepcopy(self.MeanReturn())
        for i in range(self.return_portfolio.shape[1]):
            arr = np.asarray(self.return_portfolio.iloc[:,i])
            arr = arr[arr<MAR]-MAR
            sortino[i] = (sortino[i]-MAR)/math.sqrt(np.sum(np.square(arr))/self.return_portfolio.shape[0])
        return sortino*math.sqrt(scale)

    def CalmarRatio(self,scale):
        return self.AnnualReturn(scale)/self.MaxDrawdown()
    
    def MinSlope(self,scale):
        import numpy as np
        import pandas as pd
        import statsmodels.api as sm
        minslope = pd.Series(index=self.return_portfolio.columns)
        for i in minslope.index:
            value = self.return_portfolio.loc[:,i].cumsum()
            j = 0
            restmp = []
            roll = 20
            while j+scale <= len(value):
                tmp1 = value.iloc[j:j+scale].copy()
                X = sm.add_constant(range(1,len(tmp1)+1))
                Y = tmp1.values
                result = sm.OLS(Y,X).fit()
                restmp.append(result.params[1])
                j += roll
            X = sm.add_constant(range(1,len(value)+1))
            result = sm.OLS(value.values,X).fit()
            res = result.params[1]
            sloperatio = abs(restmp/res-1)
            part10 = (sloperatio<np.nanpercentile(sloperatio,90))
            minslope.loc[i] = np.mean(sloperatio[part10])
        return minslope
        
    def LinearRegCoef(self,q):
        import copy
        import numpy as np
        import pandas as pd
        from sklearn.linear_model import LinearRegression
        cumretdata = self.return_portfolio.cumsum()
        slope = [None for _ in range(cumretdata.shape[1])]
        VaRres = copy.deepcopy(slope)
        abssumres = copy.deepcopy(slope)
        for i in range(cumretdata.shape[1]):
            x = np.array(range(cumretdata.shape[0]))/1000
            x = x.reshape(-1,1)
            y = np.asarray(cumretdata.iloc[:,i])
            y = y.reshape(-1,1)
            lr = LinearRegression()
            lr.fit(x,y)
            slope[i] = lr.coef_[0][0]
            res = y-lr.intercept_-lr.coef_*x
            abssumres[i] = np.sum(abs(res))
            res = pd.Series(res[:,0])
            VaRres[i] = -res.quantile(q=0.05)
        slope_VaRres = list(map(lambda x,y:x/y,slope,VaRres))
        slope_abssumres = list(map(lambda x,y:x/y,slope,abssumres))
        return slope,VaRres,abssumres,slope_VaRres,slope_abssumres
    
    # performance data
    def PerformData(self,rfrate,MAR,scale,q,outputpath):
        import pandas as pd
        performdata = pd.DataFrame(columns=self.return_portfolio.columns,index=('Mean Return',\
                                   'Cumulative Return','Annualized Return','Max Drawdown',\
                                   'Sharpe Ratio','Sortino Ratio','Calmar Ratio','MinSlope','Slope',\
                                   'VaR Residual','AbsSum Residual','Slope/VaR','Slope/AbsSum'))
        performdata.iloc[0,:] = list(self.MeanReturn())
        performdata.iloc[1,:] = list(self.CumReturn())
        performdata.iloc[2,:] = list(self.AnnualReturn(scale))
        performdata.iloc[3,:] = list(self.MaxDrawdown())
        performdata.iloc[4,:] = list(self.SharpeRatio(rfrate,scale))
        performdata.iloc[5,:] = list(self.SortinoRatio(MAR,scale))
        performdata.iloc[6,:] = list(self.CalmarRatio(scale))
        performdata.iloc[7,:] = list(self.MinSlope(scale))
        performdata.iloc[8:13,:] = self.LinearRegCoef(q)
        # performdata.to_csv(outputpath+'/PerformData.csv',index=True)
        self.performdata = performdata
    
    def CumDDPlot(self,outputfilename):
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import matplotlib.ticker as ticker
        cumretdata = self.return_portfolio.loc[:,['return_nofee','return_totalfee']].cumsum()
        drawdowndata = self.GetDrawdown(self.return_portfolio.loc[:,['return_nofee','return_totalfee']])
        calmar = self.CalmarRatio(250)
        minslope = self.MinSlope(250)
        figure = plt.figure(dpi=800,figsize=(10,10))
        axes1 = figure.add_subplot(2,1,1)
        axes2 = figure.add_subplot(2,1,2)
        axes1.plot(self.return_portfolio.index,cumretdata,linewidth=1,alpha=0.9)
        axes2.plot(self.return_portfolio.index,drawdowndata,linewidth=1,alpha=0.7)
        plt.subplot(2,1,1)
        plt.rc('grid',linestyle='--')
        plt.grid(True)
        plt.legend(['return_nofee','return_totalfee'])
        plt.title('NoFee Calmar='+str(round(calmar[0],4))+', AddFee Calmar='+str(round(calmar[3],4))\
                  +'\nNoFee MinSlope='+str(round(minslope[0],4))+', AddFee MinSlope='+str(round(minslope[3],4)))
        plt.ylabel('cumulative return')
        plt.gca().xaxis.set_major_locator(ticker.MultipleLocator(150))
        for tick in axes1.get_xticklabels():
            tick.set_rotation(30)
        plt.subplot(2,1,2)
        plt.rc('grid',linestyle='--')
        plt.grid(True)
        plt.ylabel('drawdown')
        plt.gca().xaxis.set_major_locator(ticker.MultipleLocator(150))
        for tick in axes2.get_xticklabels():
            tick.set_rotation(30)
        plt.savefig(outputfilename,dpi=800,bbox_inches='tight')
        plt.close()
        
    # 单一图像 - 仅累计收益曲线 
    def SingleCumPlot(self,outputpath):
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import matplotlib.ticker as ticker
        cumretdata = self.return_portfolio.cumsum()
        for i in self.return_portfolio.columns:
            plt.figure(dpi=800,figsize=(8,5))
            plt.rc('grid',linestyle='--')
            plt.grid()
            plt.plot(self.return_portfolio.index,cumretdata.loc[:,i],linewidth=1,alpha=0.9)
            plt.ylabel('cumulative return')
            plt.title(i)
            plt.gca().xaxis.set_major_locator(ticker.MultipleLocator(150))
            plt.gcf().autofmt_xdate()
            plt.savefig(outputpath+'/Cumreturn_'+i+'.jpg',dpi=800,bbox_inches='tight')
    
    def SingleCumDDPlot(self,outputpath):
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import matplotlib.ticker as ticker
        cumretdata = self.return_portfolio.cumsum()
        drawdowndata = self.GetDrawdown(self.return_portfolio)
        calmar = self.CalmarRatio(250)
        for i in self.return_portfolio.columns:
            figure = plt.figure(dpi=800,figsize=(10,10))
            axes1 = figure.add_subplot(2,1,1)
            axes2 = figure.add_subplot(2,1,2)
            axes1.plot(self.return_portfolio.index,cumretdata.loc[:,i],linewidth=1,alpha=0.9)
            axes2.plot(self.return_portfolio.index,drawdowndata.loc[:,i],linewidth=1,alpha=0.7)
            plt.subplot(2,1,1)
            plt.rc('grid',linestyle='--')
            plt.grid(True)
            plt.title(i+', Calmar='+str(round(calmar.loc[i],4)))
            plt.ylabel('cumulative return')
            plt.gca().xaxis.set_major_locator(ticker.MultipleLocator(150))
            for tick in axes1.get_xticklabels():
                tick.set_rotation(30)
            plt.subplot(2,1,2)
            plt.rc('grid',linestyle='--')
            plt.grid(True)
            plt.ylabel('drawdown')
            plt.gca().xaxis.set_major_locator(ticker.MultipleLocator(150))
            for tick in axes2.get_xticklabels():
                tick.set_rotation(30)
            plt.savefig(outputpath+'/CumretDD_'+i+'.jpg',dpi=800,bbox_inches='tight')

    def TotalCumDDPlot(self,outputpath):
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import matplotlib.ticker as ticker
        cumretdata = self.return_portfolio.cumsum()
        drawdowndata = self.GetDrawdown(self.return_portfolio)
        # calmar = self.CalmarRatio(250)
        figure = plt.figure(dpi=800,figsize=(10,10))
        axes1 = figure.add_subplot(2,1,1)
        axes2 = figure.add_subplot(2,1,2)
        axes1.plot(self.return_portfolio.index,cumretdata,linewidth=1,alpha=0.9)
        axes2.plot(self.return_portfolio.index,drawdowndata,linewidth=1,alpha=0.7)
        plt.subplot(2,1,1)
        plt.rc('grid',linestyle='--')
        plt.grid(True)
        temptitle = 'Compare Different Asset Weight Allocation'
        # for i in self.return_portfolio.columns:
        #     temptitle += ' '+i+'-Calmar='+str(round(calmar.loc[i],4))
        plt.title(temptitle)
        plt.legend(self.return_portfolio.columns)
        plt.ylabel('cumulative return')
        plt.gca().xaxis.set_major_locator(ticker.MultipleLocator(150))
        for tick in axes1.get_xticklabels():
            tick.set_rotation(30)
        plt.subplot(2,1,2)
        plt.rc('grid',linestyle='--')
        plt.grid(True)
        plt.ylabel('drawdown')
        plt.gca().xaxis.set_major_locator(ticker.MultipleLocator(150))
        for tick in axes2.get_xticklabels():
            tick.set_rotation(30)
        plt.savefig(outputpath+'/CumretDD_Total.jpg',dpi=800,bbox_inches='tight')
        
    def CompareEqualCumDDPlot(self,outputpath):
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import matplotlib.ticker as ticker
        cumretdata = self.return_portfolio.cumsum()
        drawdowndata = self.GetDrawdown(self.return_portfolio)
        calmar = self.CalmarRatio(250)
        for i in self.return_portfolio.columns:
            if i == 'EqualWeight':
                continue
            else:
                figure = plt.figure(dpi=800,figsize=(10,10))
                axes1 = figure.add_subplot(2,1,1)
                axes2 = figure.add_subplot(2,1,2)
                axes1.plot(self.return_portfolio.index,cumretdata.loc[:,['EqualWeight',i]],linewidth=1,alpha=0.9)
                axes2.plot(self.return_portfolio.index,drawdowndata.loc[:,['EqualWeight',i]],linewidth=1,alpha=0.7)
                plt.subplot(2,1,1)
                plt.rc('grid',linestyle='--')
                plt.grid(True)
                plt.legend(['EqualWeight',i])
                plt.title('EqualWeight, Calmar='+str(round(calmar.loc['EqualWeight'],4))+' '+i+', Calmar='+str(round(calmar.loc[i],4)))
                plt.ylabel('cumulative return')
                plt.gca().xaxis.set_major_locator(ticker.MultipleLocator(150))
                for tick in axes1.get_xticklabels():
                    tick.set_rotation(30)
                plt.subplot(2,1,2)
                plt.rc('grid',linestyle='--')
                plt.grid(True)
                plt.ylabel('drawdown')
                plt.gca().xaxis.set_major_locator(ticker.MultipleLocator(150))
                for tick in axes2.get_xticklabels():
                    tick.set_rotation(30)
                plt.savefig(outputpath+'/CumretDD_'+i+'withEqual.jpg',dpi=800,bbox_inches='tight')