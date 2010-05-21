import csvparser
import unittest
from datetime import date, datetime

class TestSequenceFunctions(unittest.TestCase):

	def test_parseHeader(self):
		result = csvparser.parseHeader(['Date', 'ABC ', 'DEF ', ' AAPL ', ' QWER'])
		self.assertEqual(result, ['ABC', 'DEF', 'AAPL', 'QWER'])

	def test_parseRow(self):
		(theDate, dict) = csvparser.parseRow(['Aug-09', '123.001', '456.5'], ['ABC', 'DEF'])
		self.assertEqual(theDate, (date(2009, 8, 1)))
		self.assertEqual(dict, {'ABC': 123.001, 'DEF': 456.5})

	def test_parseRow_specifiedDateFormat(self):
		(theDate, dict) = csvparser.parseRow(['8/1/2009', '123.001', '456.5'], ['ABC', 'DEF'], '%m/%d/%Y')
		self.assertEqual(theDate, (date(2009, 8, 1)))
		self.assertEqual(dict,  {'ABC': 123.001, 'DEF': 456.5})

if __name__ == '__main__':
    unittest.main()
