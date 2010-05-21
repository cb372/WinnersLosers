import winnerslosers
import unittest
from datetime import date

class TestSequenceFunctions(unittest.TestCase):

	def test_findDate(self):
		index = winnerslosers.findDate([(date(1,2,3),{}), (date(4,5,6),{}), (date(7,8,9),{})], date(4,5,6))
		self.assertEqual(index, 1)

	def test_findDate_unknownDateThrowsException(self):
		self.assertRaises(IndexError, winnerslosers.findDate, [(date(1,2,3),{}), (date(4,5,6),{}), (date(7,8,9),{})], date(5,4,3))

	def test_calcPercentReturn(self):
		self.assertEqual(winnerslosers.calcPercentReturn(1000.0, 1010.0), 1.0)
		self.assertEqual(winnerslosers.calcPercentReturn(1000.0, 1000.0), 0.0)
		self.assertEqual(winnerslosers.calcPercentReturn(1000.0, 990.0), -1.0)

	def test_calcNumWinnersLosers(self):
		self.assertEqual(winnerslosers.calcNumWinnersLosers(range(50), 10, False), 10)
		self.assertEqual(winnerslosers.calcNumWinnersLosers(range(5), 10, False), 5)
		self.assertEqual(winnerslosers.calcNumWinnersLosers(range(50), 10, True), 5)
		self.assertEqual(winnerslosers.calcNumWinnersLosers(range(5), 10, True), 1)

	def test_sumDictValues(self):
		myDict = {'xyz':10.0, 'abc':15.5}
		self.assertEqual(winnerslosers.sumDictValues(myDict), 25.5)
		self.assertEqual(winnerslosers.sumDictValues(dict()), 0.0)

	def test_calcPortfolioStartIndex(self):
		self.assertEqual(winnerslosers.calcPortfolioStartIndex(5,10), 5) 
		self.assertEqual(winnerslosers.calcPortfolioStartIndex(10,5), 1)

	def test_calcOutputLastIndex(self):
		self.assertEqual(winnerslosers.calcOutputLastIndex(range(10),5,3), 8) 
		self.assertEqual(winnerslosers.calcOutputLastIndex(range(10),5,5), 9)
 

if __name__ == '__main__':
    unittest.main()
