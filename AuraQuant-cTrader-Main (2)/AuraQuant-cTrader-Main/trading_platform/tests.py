from django.test import TestCase
import pandas as pd
from .quant_engine.strategies.base_strategy import BaseStrategy

class BaseStrategyTestCase(TestCase):
    def setUp(self):
        # Create a sample dataframe for testing
        self.df = pd.DataFrame({
            'time': pd.to_datetime(['2023-01-01', '2023-01-02', '2023-01-03', '2023-01-04', '2023-01-05']),
            'open': [100, 101, 102, 103, 104],
            'high': [105, 106, 107, 108, 109],
            'low': [99, 100, 101, 102, 103],
            'close': [104, 105, 106, 107, 108],
            'volume': [1000, 1100, 1200, 1300, 1400],
        })
        self.params = {}

    def test_add_indicators(self):
        """
        Test that the add_indicators method in BaseStrategy adds the expected columns.
        """
        df_featured = BaseStrategy.add_indicators(self.df, self.params)

        # Check that the expected columns have been added
        self.assertIn('ema_curta', df_featured.columns)
        self.assertIn('ema_longa', df_featured.columns)
        self.assertIn('atr', df_featured.columns)
        self.assertIn('rsi', df_featured.columns)
        self.assertIn('nivel_liquidez_sup', df_featured.columns)
        self.assertIn('nivel_liquidez_inf', df_featured.columns)
