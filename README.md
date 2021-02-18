# multifactor_model
## First of all, great thanks to my manager, Shenjia Yi, colleborating with me to work on the whole project and to my company, yuyan capital, offering me opportunities and resources for this whole project.

### This is a multifactor investing model using for commodity futures traded in Shanghai Futures Exchange (including AL, CU, NI, PB, SN, ZN) and we use factors like Basisratio, CapitalFlow, Momentum, Reverse, RollYeild, Stocks, WarrantChange. The model first evaluates single factor's performance, uses it as indicators to give weight for each factor, and finally generates multi-factor scores for each assets and construct long-short portfolio based on it. 

### Description for each .py file:
MultiFactor.py: read the factor data files and output pandas data structure and factor rank

AssetReturn.py: read the asset data files and output pandas data structure

SingleFactorReturn.py: construct single factor portfolio based on factor rank, and output the portfolio performance data

FactorSocre.py: Based on SingeFactorReturn.py output, add the weighted single factors together to give total score. Different parameters, 'EqualWeight','GroupEqualWeight','MaxIR','MeanVariance','RiskParity','GroupRiskParity','VolReverse', can be choose to decide the weights

MeanVariance.py: a helper class for mean-variance optimization

MultiFactorReturn_PPA.py: output the final portfolio performance metrices, like returns, volatility, VaR, Calmar ratio, drawdown, etc.

NONO_FactorRank_MultiScore_Main.py: the main class to run all the functions and classes

### Due to company's policy, I cannot post classes like MarginRatio.py, AssetRealLot.py, MinutePrice.py, PortfolioReturn.py, which are about how the company would execute the portofolio in reality. I also cannot disclose the factor and asset data because they are company's properties, which are not meant to be public. I can only post some sample outputs to show what the code can do.

## Therefoe, the whole codes are only for domenstration and reference purpose. In reality, many active analysis and modification needs to make the model profitable.
