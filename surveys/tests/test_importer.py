import io

import pandas as pd
from django.test import SimpleTestCase

from ..data.importer import SurveyImportError, normalize_region, read_and_clean
from .samples import CSV, HEADER, row


class ReadAndCleanTests(SimpleTestCase):
    def test_cleaning_report(self):
        df, report = read_and_clean(io.StringIO(CSV))
        self.assertEqual(report.rows_read, 5)
        self.assertEqual(report.duplicates_removed, 1)
        self.assertEqual(report.invalid_dates_removed, 1)
        self.assertEqual(report.values_set_missing["monthly_spend_eur"], 1)
        self.assertEqual(report.values_set_missing["nps_score"], 1)
        self.assertEqual(report.rows_saved, 3)
        self.assertEqual(len(df), 3)

    def test_rejects_missing_columns(self):
        with self.assertRaises(SurveyImportError):
            read_and_clean(io.StringIO("response_id,age\n1,30\n"))

    def test_large_outliers_do_not_overflow(self):
        # Reading as Int8 silently turned 300 into 44, a seemingly valid age.
        csv = HEADER + row(1, age=300) + row(2, age=150) + row(3, age=45)
        df, report = read_and_clean(io.StringIO(csv))
        self.assertTrue(df["age"].iloc[:2].isna().all())
        self.assertEqual(df["age"].iloc[2], 45)
        self.assertEqual(report.values_set_missing["age"], 2)
        self.assertEqual(str(df["age"].dtype), "Int8")

    def test_fractional_values_in_integer_columns_become_missing(self):
        df, report = read_and_clean(io.StringIO(HEADER + row(1, satisfaction=3.5)))
        self.assertTrue(df["satisfaction"].isna().all())
        self.assertEqual(report.values_set_missing["satisfaction"], 1)


class NormalizeRegionTests(SimpleTestCase):
    def test_aliases_and_spelling_variants(self):
        regions = pd.Series(["NRW", " bayern", "Baden-Wuerttemberg", "Atlantis"])
        self.assertEqual(
            normalize_region(regions).tolist()[:3], ["Nordrhein-Westfalen", "Bayern", "Baden-Württemberg"]
        )
        self.assertTrue(pd.isna(normalize_region(regions).iloc[3]))
