import unittest
from datetime import datetime
from EquityOptionPricer import SimpleOptionPricer


class TestEquityOptionPricer(unittest.TestCase):

    def test_vol_supplied(self):
        # the volatility is based on a supplied parameter
        print 'Baseline test of dummy security'
        self.pricer = SimpleOptionPricer(sec_id='DummySecurity'
                                         , option_type='call'
                                         , strike=130
                                         , maturity_d=datetime(2016, 1, 15)
                                         , rfr=0.001
                                         , spot_price=127.62
                                         , vol=0.2
                                         , div_rate=0.0163
                                         , iterations=200
                                         )
        eo, ao = self.pricer.calculate(datetime(2015, 5, 8))

        self.assertEqual(eo, 6.749271812460607, 'European Option with vol supplied matching')
        self.assertEqual(ao, 6.84210328728556, 'American Option with vol supplied matching')

    def test_vol_not_supplied(self):
        # volatility is not supplied hence needs to calculated via quandl data service

        print 'Test of historical volatility calculation'
        self.pricer = SimpleOptionPricer(sec_id='IBM'
                                         , option_type='call'
                                         , strike=130
                                         , maturity_d=datetime(2016, 1, 15)
                                         , rfr=0.001
                                         , spot_price=127.62
                                         , div_rate=0.0163
                                         , iterations=200
                                         )
        eo, ao = self.pricer.calculate(datetime(2015, 5, 8))
        quandl_vol = self.pricer.vol
        self.assertEqual(quandl_vol, 0.18843927034451727, 'Volatility is matching')
        self.assertEqual(eo, 6.268062243196524, 'European Option w/o vol supplied matching')
        self.assertEqual(ao, 6.357908806189591, 'American Option w/o vol supplied matching')

    def test_future_cash_dividends_schedule_provided(self):
        print 'Test of scheduled dividends'
        self.pricer = SimpleOptionPricer(sec_id='IBM'
                                    , option_type='call'
                                    , strike=140
                                    , maturity_d=datetime(2018, 7, 20)
                                    , rfr=0.001
                                    , spot_price=145.2
                                    , div_sched=[datetime(2018, 6, 15)]
                                    , div_amounts=[0.12]
                                    , iterations=200
                                    )
        eo, ao = self.pricer.calculate(datetime(2018, 6, 14))
        self.assertEqual(eo, 7.816059175341424, 'European Option with scheduled dividends matching')
        self.assertEqual(ao, 7.816059175341424, 'American Option with scheduled dividends matching')