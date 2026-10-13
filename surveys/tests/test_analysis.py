import io

import pandas as pd
from django.test import SimpleTestCase

from ..data.analysis import age_group_stats, kpis, net_promoter_score, summarize
from ..data.importer import read_and_clean
from .samples import CSV, HEADER, row


class NetPromoterScoreTests(SimpleTestCase):
    def test_promoters_minus_detractors(self):
        # 2 promoters (10, 9), 1 detractor (0) out of 4 -> 50 % - 25 % = 25
        self.assertEqual(net_promoter_score(pd.Series([10, 9, 8, 0])), 25.0)

    def test_ignores_missing_values(self):
        self.assertEqual(net_promoter_score(pd.Series([10, None], dtype="Int8")), 100.0)

    def test_no_scores(self):
        self.assertIsNone(net_promoter_score(pd.Series([None], dtype="Int8")))


class SummaryTests(SimpleTestCase):
    def test_summary(self):
        df, _ = read_and_clean(io.StringIO(CSV))
        summary = summarize(df)
        self.assertEqual(summary["kpis"]["responses"], 3)
        self.assertEqual(summary["brands"][0]["brand"], "Bohnenwerk")
        self.assertEqual(summary["brands"][0]["responses"], 2)

    def test_age_groups_use_real_nps(self):
        # Promoter (10) and detractor (0) in the same age group -> NPS 0, not the mean of 5.
        df, _ = read_and_clean(io.StringIO(HEADER + row(1, nps_score=10) + row(2, nps_score=0)))
        groups = age_group_stats(df)
        self.assertEqual(groups.loc[0, "age_group"], "30–39")
        self.assertEqual(groups.loc[0, "nps"], 0.0)

    def test_all_missing_column_gives_none_not_nan(self):
        df, _ = read_and_clean(io.StringIO(HEADER + row(1, monthly_spend_eur=None, satisfaction=None)))
        result = kpis(df)
        self.assertIsNone(result["avg_monthly_spend"])
        self.assertIsNone(result["avg_satisfaction"])
