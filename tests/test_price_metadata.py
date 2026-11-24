import unittest
from datetime import datetime, timezone

from Projeto.price_metadata import format_price_timestamp, parse_unix_timestamp


class PriceTimestampTests(unittest.TestCase):
    def test_source_time_and_query_fallback_are_labeled_in_sao_paulo(self) -> None:
        timestamp = datetime(2026, 11, 21, 0, 0, tzinfo=timezone.utc)

        self.assertEqual(
            format_price_timestamp(timestamp, None, "CheapShark"),
            "Atualização informada pela CheapShark: 20/11/2026 às 21:00",
        )
        self.assertEqual(
            format_price_timestamp(None, timestamp, "Steam"),
            "Consultado pelo ComparaKeys: 20/11/2026 às 21:00",
        )

    def test_unix_timestamp_parser_rejects_missing_and_invalid_values(self) -> None:
        self.assertEqual(
            parse_unix_timestamp(1794817753),
            datetime.fromtimestamp(1794817753, timezone.utc),
        )
        for value in (None, True, 0, -1, "not-a-time", 10**30):
            with self.subTest(value=value):
                self.assertIsNone(parse_unix_timestamp(value))


if __name__ == "__main__":
    unittest.main()
