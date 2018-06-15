# quantlib-python-option-pricer
Version Python: 2.7 - hard requirement or use older version of pip to install below libraries
Libraries: 
- Quantlib-Python 1.13 { pip install Quantlib }
- Quandl 3.3   { pip install quandl }
- numpy 1.14.4   { pip install numpy }
- pandas 0.23 { pip install pandas-datareader }
- pandas-datareader 0.6 { pip install pandas-datareader }

There are two files in this project.

1. EquityOptionPricer.py
    class #1: SimpleOptionPricer
              Calibrates and runs the functions to calculate the NPV for equity options
    class #2: QuandlRealizedStockVol
              Pulls adjusted EOD equity prices from Quandl into dataframe and calculates 92-day log-normal volatility
              
2. TestEquityOptionPricer.py
    Various test cases to calculate the volatility and NPV
    
    
Assumptions:
  - Volatility formula is based on realized volatility of 92 days of historical prices
  - Actual 365 fixed day count used for calcualtions
  - United States trading calendar used
  - Risk-free-rate is always supplied 
