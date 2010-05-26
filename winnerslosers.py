# coding:UTF-8

import sys
import math
import csvparser
import logging
import logging.config
from datetime import datetime, date
from pprint import pprint
from optparse import OptionParser

logging.config.fileConfig("logging.conf")
logger = logging.getLogger("WinnersLosers")

def main(argv):
	# Parse the command line args and options
	parser = createOptions()
	(options, args) = parser.parse_args(argv)
	if len(args) < 5:
		parser.print_help()
		return

	inputFile = args[1]
	outputFile = args[2]
	startDate = datetime.strptime(args[3], "%m/%Y").date()
	portfolioMonths = int(args[4])
	N = int(args[5])
	if options.outputMonths is None:
		outputMonths = portfolioMonths
	else:
		outputMonths = options.outputMonths

	# Parse the CSV file
	(dates, shareCodes) = csvparser.parseCsvFile(inputFile, options.dateformat)

	numWinnersLosers = calcNumWinnersLosers(shareCodes, N, options.isPercentage)
		
	# Create a portfolio and pick the winners and losers	
	winnersAndLosers = pickWinnersLosers(dates, shareCodes, startDate, portfolioMonths, numWinnersLosers)

	# Output performance data for the winners and losers
	outputWinnersLosersData(dates, winnersAndLosers, outputMonths, startDate)


def outputWinnersLosersData(dates, winnersAndLosers, monthsToOutput, startDate):
	"""
	Given the lists of winners and losers, output performance data
	for those shares and for the market as a whole, for a given number
	of months starting from startDate.

	dates is a list of (month, {shareCode->price}) tuples in ascending date order.
	winnersAndLosers is a dict of the form {"winners"->[winner1,winner2,...], "losers"->[loser1,loser2,...]}
	where winnerN, loserN are share codes. 
	"""
	startDateIndex = findDate(dates, startDate)
	lastIndex = calcOutputLastIndex(dates, monthsToOutput, startDateIndex)
	pricesBeforeStart = dates[startDateIndex-1][1]
	relevantMonths = dates[startDateIndex:lastIndex] 	
	logger.info("Outputting winners and losers performance data from %s to %s", relevantMonths[0][0], relevantMonths[-1][0])

	# Prices of each share and market total in the month before startDate
	prevPrices = pricesBeforeStart
	prevMarketTotal = sumDictValues(pricesBeforeStart)
	
	# TODO for now, copy-paste the code from pickWinnersLosers.
	# Still not sure exactly what we should be outputting
	for (date, prices) in relevantMonths:
		marketTotal = sumDictValues(prices) 
		marketReturn = calcPercentReturn(prevMarketTotal, marketTotal)	
		prevMarketTotal = marketTotal
		logger.info("Market return for %s = %s%%", date, marketReturn)
		logger.info("Market total price = %s", marketTotal)	
		for winner in winnersAndLosers['winners']:
			if winner not in prices:
				logger.info("%s: Price missing for share code %s. Setting equal to previous price %s", date, winner, prevPrices[winner])
				prices[winner] = prevPrices[winner]

			shareReturn = calcPercentReturn(prevPrices[winner], prices[winner])
			prevPrices[winner] = prices[winner]
			logger.info("Winner [%s] return: %s%%", winner, shareReturn)	
		for loser in winnersAndLosers['losers']:
			if loser not in prices:
				logger.info("%s: Price missing for share code %s. Setting equal to previous price %s", date, loser, prevPrices[loser])
				prices[loser] = prevPrices[loser]

			shareReturn = calcPercentReturn(prevPrices[loser], prices[loser])
			prevPrices[loser] = prices[loser]
			logger.info("Loser [%s] return: %s%%", loser, shareReturn)	
	

def pickWinnersLosers(dates, shareCodes, startDate, months, numWinnersLosers):
	"""
	Create a portfolio, i.e. calculate the winners and losers for a
	given number of months before startDate.

	dates is a list of (month, {shareCode->price}) tuples in ascending date order.
	months is the number of months to generate the portfolio.
	numWinnersLosers is the number of winners (and losers) to return.
	"""
	startDateIndex = findDate(dates, startDate)
	firstIndex = calcPortfolioStartIndex(months, startDateIndex)
	pricesBeforeStart = dates[firstIndex-1][1]
	relevantMonths = dates[firstIndex:startDateIndex]
	logger.info("Calculating winners and losers from %s to %s", relevantMonths[0][0], relevantMonths[-1][0])

	# Prices of each share and market total in the month before portfolio generation
	prevPrices = pricesBeforeStart
	prevMarketTotal = sumDictValues(pricesBeforeStart)
	
	# All cumulative residuals start at 0
	cumResiduals = dict.fromkeys(pricesBeforeStart.keys(), 0.0)	

	# For each month
	for (date, prices) in relevantMonths:
	# TODO Rm should be based on average of all shares, not total?
		# Calculate market return Rm
		marketTotal = sumDictValues(prices)
		marketReturn = calcPercentReturn(prevMarketTotal, marketTotal)	
		prevMarketTotal = marketTotal
		logger.info("Market return for %s = %s%%", date, marketReturn)
		
		# For each share	
		for shareCode in cumResiduals.keys():
			# Deal with missing prices
			if shareCode not in prices:
				logger.info("%s: Price missing for share code %s. Setting equal to previous price %s", date, shareCode, prevPrices[shareCode])
				prices[shareCode] = prevPrices[shareCode]
	
			# Calculate share return Rj
			shareReturn = calcPercentReturn(prevPrices[shareCode], prices[shareCode])
			prevPrices[shareCode] = prices[shareCode]

			# Calculate residual Rj - Rm
			residual = shareReturn - marketReturn

			# Add to cumulate residual for this share
			cumResiduals[shareCode] += residual

	logger.debug("Cumulative residuals after portfolio generation: %s", cumResiduals)
	
	# Sort shares in order of cumulative residual
	sortedShareCodes = sorted(cumResiduals, key=lambda s: cumResiduals[s])		
 
	return {"losers":sortedShareCodes[0:numWinnersLosers], "winners":sortedShareCodes[-numWinnersLosers:]}

def calcPercentReturn(prevValue, currValue):
	"""
	Calculate a share's return (difference between last
	month's value and this month's value) as a percentage.
	"""
	return ((currValue - prevValue) / prevValue) * 100.0

def calcNumWinnersLosers(shareCodes, N, isPercentage):
	"""
	Calculate the required number of winners and losers.
	Either a fixed number or a percentage of the total number of share codes.
	"""
	if isPercentage:
		nPercent = N * 0.01
		return int(math.ceil(nPercent * len(shareCodes)))
	else:
		return min(N, len(shareCodes))

def sumDictValues(dict):
	""" 
	Calculate the sum of all the values	in a dictionary.
	"""
	return reduce(lambda x, y: x+dict[y], dict, 0.0)

def findDate(dates, startDate):
	"""
	In dates list, find index of the date startDate.
	"""
	logger.debug("Looking for date %s", startDate)
	for index, (date, dict) in enumerate(dates):
		if date == startDate:
			return index
	raise IndexError("Couldn't find the specified date in this file")

def calcOutputLastIndex(dates, monthsToOutput, startDateIndex):
	"""
	Given the index of the startDate
	and the number of months we want to output data for,
	calc the index of the last month to output.
	Ensure that we do not go past the end of the list.
	"""
	return min(len(dates) - 1, startDateIndex + monthsToOutput)

def calcPortfolioStartIndex(months, startDateIndex):
	"""
	Given the index of the startDate
	and the number of months we want to build the portfolio,
	calc the index of the first portfolio-building month.
	Ensure that we do not go further back than the start of the list.
	"""
	return max(1, startDateIndex - months)


def createOptions():
	usage = "usage: %prog [options] inputFile outputFile startDate(MM/YYYY) portfolioMonths N"
	parser = OptionParser(usage=usage)
	parser.add_option("-d", "--dateformat", dest="dateformat", default="%b-%y",
                help="Date format string in Python format (e.g. 'Mar-09' is %b-%y, '10/2005' is %m-%Y)")
	parser.add_option("-p", "--percentage", action="store_true", dest="isPercentage",
				help="Choose N% of stocks as winners/losers")
	parser.add_option("-m", "--months", dest="outputMonths", type="int", 
				help="Months of data to output. Default: equal to portfolioMonths")
	return parser

# Allow file to be run as "python winnerslosers.py <optionsAndArgs>"
if __name__ == "__main__":
    main(sys.argv)
