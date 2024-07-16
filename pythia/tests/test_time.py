import unittest
from pythia.time.dateroll import build_roll
from datetime import date


class TimeCase(unittest.TestCase):
    def test_roll(self):
        dr = build_roll("EOQ")
        dt = date(2017, 4, 20)
        dt1 = dr.roll(dt)
        self.assertEqual(date(2017, 6, 30), dt1)  # add assertion here


if __name__ == '__main__':
    unittest.main()
