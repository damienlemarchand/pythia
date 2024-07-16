import unittest
from datetime import date
from pythia.finance.product import create_product_registry
from pythia.finance.receivables import create_invoice


class FinanceTestCase(unittest.TestCase):
    def test_something(self):
        product_registry = create_product_registry()
        self.assertIsNotNone(product_registry)
        self.assertFalse("INVOICE" in product_registry)
        invoice_date = date(2017, 4, 20)
        trade = create_invoice(product_registry,"test","id_creditor","id_debtor"
                               , invoice_date,"EUR", float(100),0,"ptf", None, "1M")
        self.assertIsNotNone(trade)
        self.assertTrue("INVOICE" in product_registry)


if __name__ == '__main__':
    unittest.main()
