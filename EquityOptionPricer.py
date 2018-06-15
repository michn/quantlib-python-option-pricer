from datetime import datetime, timedelta
import QuantLib as ql
import numpy as np
import quandl


class SimpleOptionPricer():
    def __init__(self, sec_id, option_type, strike, maturity_d, rfr, spot_price, div_rate=None, div_sched=[], div_amounts=[], iterations=200, vol=None):
        self.sec_id = sec_id
        self.option_type = option_type
        self.strike = strike
        self.maturity_d = maturity_d
        self.risk_free_rate = rfr
        self.spot_price = spot_price
        self.dividend_rate = div_rate
        self.div_sched = div_sched
        self.div_amounts = div_amounts
        self.iterations = iterations
        self.calc_date = None
        self.vol = vol


    def calculate(self, calc_date):
        self.calc_date =calc_date
        if self.vol == None:
            timeVol = datetime.now()
            self.vol = self.calculateVol()

        calc_date_ql, mat_date_ql, bsm_process, payoff_ql = self.calibrateQL()

        eo = self.calcEuropeanOption(calc_date_ql, mat_date_ql, bsm_process, payoff_ql )
        ao = self.calcAmericanOption(calc_date_ql, mat_date_ql, bsm_process, payoff_ql )
        return eo, ao

    def calibrateQL(self):
        # Assumptions
        day_count_ql = ql.Actual365Fixed()
        calendar_ql = ql.UnitedStates()

        calculation_date_ql = ql.Date(self.calc_date.day, self.calc_date.month, self.calc_date.year )
        maturity_date_ql = ql.Date(self.maturity_d.day, self.maturity_d.month, self.maturity_d.year)

        # Black-Scholes-Merton process constructred
        spot_handle_ql = ql.QuoteHandle(
            ql.SimpleQuote(self.spot_price)
        )
        flat_ts = ql.YieldTermStructureHandle(
            ql.FlatForward(calculation_date_ql, self.risk_free_rate, day_count_ql)
        )
        flat_vol_ts = ql.BlackVolTermStructureHandle(
            ql.BlackConstantVol(calculation_date_ql, calendar_ql, self.vol, day_count_ql)
        )

        if self.dividend_rate is not None:
            dividend_yield = ql.YieldTermStructureHandle(
               ql.FlatForward(calculation_date_ql, self.dividend_rate, day_count_ql)
            )
            bsm_process = ql.BlackScholesMertonProcess(spot_handle_ql,
                                                       dividend_yield,
                                                       flat_ts,
                                                       flat_vol_ts)
        else:
            bsm_process = ql.BlackScholesProcess(spot_handle_ql,
                                                       flat_ts,
                                                       flat_vol_ts)

        ql.Settings.instance().evaluationDate = calculation_date_ql

        # options
        if self.option_type.lower() in ['call', 'c']:
            option_type_ql = ql.Option.Call
        elif self.option_type.lower() in ['put', 'p']:
            option_type_ql = ql.Option.Put
        else:
            raise ValueError('Payoff function not well defined')

        payoff_ql = ql.PlainVanillaPayoff(option_type_ql, self.strike)

        return calculation_date_ql, maturity_date_ql, bsm_process, payoff_ql

    def calcEuropeanOption(self, calculation_date_ql, maturity_date_ql, bsm_process, payoff_ql):
        # European option
        eu_exercise_ql = ql.EuropeanExercise(maturity_date_ql)

        #european_option_ql = None
        if len(self.div_sched) == 0:
            european_option_ql = ql.VanillaOption(payoff_ql, eu_exercise_ql)
            european_option_ql.setPricingEngine(ql.AnalyticEuropeanEngine(bsm_process))

        else:
            steps = self.iterations
            div_sched_ql = [ql.Date(d.day, d.month, d.year) for d in self.div_sched]
            european_option_ql = ql.DividendVanillaOption(payoff_ql, eu_exercise_ql, div_sched_ql, self.div_amounts)
            engine = ql.FDDividendEuropeanEngine(bsm_process, steps, steps -1)
            european_option_ql.setPricingEngine(engine)


        print "European theoretical price is ", european_option_ql.NPV()
        print " -->Delta: ", european_option_ql.delta()
        print " -->Gamma: ", european_option_ql.gamma()

        return european_option_ql.NPV()

    def calcAmericanOption(self, calculation_date_ql, maturity_date_ql, bsm_process, payoff_ql):
        # American option

        settlement = calculation_date_ql
        am_exercise_ql = ql.AmericanExercise(settlement, maturity_date_ql)
        steps = self.iterations

        if len(self.div_sched) == 0:
            american_option_ql = ql.VanillaOption(payoff_ql, am_exercise_ql)
            binomial_engine = ql.BinomialVanillaEngine(bsm_process, "crr", steps)
            american_option_ql.setPricingEngine(binomial_engine)
        else:
            div_sched_ql = [ql.Date(d.day, d.month, d.year) for d in self.div_sched]
            american_option_ql = ql.DividendVanillaOption(payoff_ql, am_exercise_ql, div_sched_ql, self.div_amounts)
            engine = ql.FDDividendAmericanEngine(bsm_process, steps, steps -1)
            american_option_ql.setPricingEngine(engine)

        print "American theoretical price is ", american_option_ql.NPV()
        print " -->Delta: ", american_option_ql.delta()
        print " -->Gamma: ", american_option_ql.gamma()
        return american_option_ql.NPV()


    def calculateVol(self):
        return QuandlRealizedStockVol().getStockVol(self.sec_id, self.calc_date)


class QuandlRealizedStockVol():
    def __init__(self):
        quandl.ApiConfig.api_key = "pkAbWZh3LHUzGwje7Ub1"

    def getStockVol(self, security, date):
        days = 92
        end_time = date.strftime('%Y-%m-%d')  # current date
        start_time = (date - timedelta(days=days)).strftime('%Y-%m-%d')

        prices = quandl.get_table('WIKI/PRICES', qopts={'columns': ['ticker', 'date', 'adj_close']},
                                  ticker=[security],
                                  date={'gte': start_time, 'lte': end_time})

        # sort dates in descending order
        prices.sort_index(ascending=False, inplace=True)

        # calculate daily logarithmic return
        prices['Return'] = (np.log(prices['adj_close'] /
                                   prices['adj_close'].shift(-1)))

        # calculate daily standard deviation of returns
        d_std = np.std(prices.Return)

        # annualize daily standard deviation
        std = d_std * 252 ** 0.5

        return std

if __name__ == "__main__":
    start = datetime.now()
    pricer = SimpleOptionPricer(sec_id='DummySecurity'
                                ,option_type='call'
                                ,strike=130
                                ,maturity_d=datetime(2016, 1, 15)
                                ,rfr=0.001
                                ,spot_price=127.62
                                ,vol=0.2
                                ,div_rate=0.0163
                                ,iterations=200
                                )
    pricer.calculate(datetime(2015, 5, 8))
    print "***** Total calculation time", (datetime.now() - start).total_seconds(), 'seconds ***** \n'

    start = datetime.now()
    pricer = SimpleOptionPricer(sec_id='IBM'
                                ,option_type='call'
                                ,strike=140
                                ,maturity_d=datetime(2018, 7, 20)
                                ,rfr=0.001
                                ,spot_price=145.2
                                ,div_sched=[datetime(2018, 6, 15)]
                                ,div_amounts=[0.12]
                                #,div_rate=0.0429
                                ,iterations=200
                                )
    pricer.calculate(datetime(2018,6, 14))
    print "***** Total calculation time", (datetime.now() - start).total_seconds(), 'seconds ***** \n'
