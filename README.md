# multifactor_model
## First of all, great thanks to my manager, Shenjia Yi, colleborating with me to work on the whole project and to my company, yuyan capital, offering me opportunities and resource.

### This is a multifactor investing model using for commodity futures traded in Shanghai Futures Exchange (including AL, CU, NI, PB, SN, ZN) and we use factors like Basisratio, CapitalFlow, Momentum, Reverse, RollYeild, Stocks, WarrantChange. The model first evaluates single factor's performance, uses it as indicators to give weight for each factor, and finally generates multi-factor scores for each assets and construct long-short portfolio based on it. 

### Description for each .py file:
MultiFactor.py: read the factor data files and output pandas data structure and factor rank

AssetReturn.py: read the asset data files and output pandas data structure

SingleFactorReturn.py: construct single factor portfolio based on factor rank, and output the portfolio performance data

FactorSocre.py: Based on SingeFactorReturn.py output, add the single factor together to 
