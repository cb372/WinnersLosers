# coding:UTF-8

import os
import sys
import math
import csvparser
import csv
import csvoutput
import logging
import logging.config
from datetime import datetime, date
from pprint import pprint
from optparse import OptionParser

logging.config.fileConfig(os.path.join(sys.path[0], "logging.conf"))
logger = logging.getLogger("WinnersLosers")

def main(argv):
	# Parse the command line args and options
	parser = createOptions()
	(options, args) = parser.parse_args(argv)
	if len(args) < 6:
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
	winnersAndLosers = pickWinnersLosers(dates, shareCodes, startDate, portfolioMonths, numWinnersLosers, options.useMarketTotalReturn)

	# Output performance data for the winners and losers
	outputWinnersLosersData(outputFile, dates, winnersAndLosers, outputMonths, startDate, options.useMarketTotalReturn)


def outputWinnersLosersData(outputFile, dates, winnersAndLosers, monthsToOutput, startDate, useMarketTotalReturn):
	"""
	Given the lists of winners and losers, output performance data
	for those shares and for the market as a whole, for a given number
	of months starting from startDate.

	dates is a list of (month, {shareCode->price}) tuples in ascending date order.
	winnersAndLosers is a dict of the form {"winners"->[winner1,winner2,...], "losers"->[loser1,loser2,...]}
	where winnerN, loserN are share codes. 
	useMarketTotalReturn is a boolean. 
		true = use the market's total percentage return to calculate each share's residual.
		false = use the average percentage return of all the shares in the market.
	"""
	startDateIndex = findDate(dates, startDate)
	lastIndex = calcOutputLastIndex(dates, monthsToOutput, startDateIndex)
	pricesBeforeStart = dates[startDateIndex-1][1]
	relevantMonths = dates[startDateIndex:lastIndex] 	
	logger.info("Outputting winners and losers performance data from %s to %s.", relevantMonths[0][0], relevantMonths[-1][0]) 
	logger.info("Using %s to calc residuals.", "market total return" if useMarketTotalReturn else "market average return")
	logger.info("Writing to file %s...", outputFile)

	# Prices of each share and market total in the month before startDate
	prevPrices = pricesBeforeStart
	lastKnownPrices = pricesBeforeStart
	
	with open(outputFile, 'w') as f:
		writer = csv.writer(f)
		csvoutput.writeCsvHeader(writer, winnersAndLosers)
		logger.info("Wrote CSV header")

		for (date, prices) in relevantMonths:
			row = [date.strftime('%b-%Y')]
			
			# Calculate market average return 
			marketAvgReturn = calcMarketAverageReturn(date, prevPrices, prices)
			row += [marketAvgReturn]

			# Also calculate the market total return
			marketTotalReturn = calcMarketTotalReturn(date, prevPrices, prices)
			row += [marketTotalReturn]

			# Choose appropriate Rm based on user setting
			if useMarketTotalReturn:
				Rm = marketTotalReturn
			else:
				Rm = marketAvgReturn
	
			for winner in winnersAndLosers['winners']:
				# Calculate return Rj and residual Rj - Rm for this share 
				(absoluteReturn, percentReturn, residual) = calcShareResidual(date, winner, lastKnownPrices, prices, Rm)
				
				logger.debug("Winner [%s]\tAbsolute return = %s,\tPercentage return = %s%%\tResidual = %s%%", winner, absoluteReturn, percentReturn, residual)	
				row += [absoluteReturn, percentReturn, residual]

			for loser in winnersAndLosers['losers']:
				# Calculate return Rj and residual Rj - Rm for this share 
				(absoluteReturn, percentReturn, residual) = calcShareResidual(date, loser, lastKnownPrices, prices, Rm)
				
				logger.debug("Loser [%s]\tAbsolute return = %s,\tPercentage return = %s%%\tResidual = %s%%", loser, absoluteReturn, percentReturn, residual)	
				row += [absoluteReturn, percentReturn, residual]

			# Update prevPrices before moving on to next month
			prevPrices = prices

			# Output row to CSV file
			writer.writerow(row)

			logger.info("Wrote data for %s", date)
		
		logger.info("Finished! Now open the file in Excel and crunch those numbers.")

def pickWinnersLosers(dates, shareCodes, startDate, months, numWinnersLosers, useMarketTotalReturn):
	"""
	Create a portfolio, i.e. calculate the winners and losers for a
	given number of months before startDate.

	dates is a list of (month, {shareCode->price}) tuples in ascending date order.
	months is the number of months to generate the portfolio.
	numWinnersLosers is the number of winners (and losers) to return.
	useMarketTotalReturn is a boolean. 
		true = use the market's total percentage return to calculate each share's residual.
		false = use the average percentage return of all the shares in the market.
	"""
	startDateIndex = findDate(dates, startDate)
	firstIndex = calcPortfolioStartIndex(months, startDateIndex)
	pricesBeforeStart = dates[firstIndex-1][1]
	relevantMonths = dates[firstIndex:startDateIndex]
	logger.info("Calculating winners and losers from %s to %s.", relevantMonths[0][0], relevantMonths[-1][0])
	logger.info("Using %s to calc residuals.", "market total return" if useMarketTotalReturn else "market average return")

	# Prices of each share in the month before portfolio generation
	prevPrices = pricesBeforeStart
	lastKnownPrices = pricesBeforeStart
	
	# All cumulative residuals start at 0
	cumResiduals = dict.fromkeys(pricesBeforeStart.keys(), 0.0)	

	# For each month
	for (date, prices) in relevantMonths:
		# Calculate market average return
		marketAvgReturn = calcMarketAverageReturn(date, prevPrices, prices)
		
		# Also calculate the market total return
		marketTotalReturn = calcMarketTotalReturn(date, prevPrices, prices)

		# Choose appropriate Rm based on user setting
		if useMarketTotalReturn:
			Rm = marketTotalReturn
		else:
			Rm = marketAvgReturn
 
		# For each share	
		for shareCode in cumResiduals:
			# Calculate return Rj and residual Rj - Rm for this share 
			(absoluteReturn, percentReturn, residual) = calcShareResidual(date, shareCode, lastKnownPrices, prices, Rm)

			# Add to cumulate residual for this share
			cumResiduals[shareCode] += residual

		# Update prevPrices before moving on to next month
		prevPrices = prices

	logger.debug("Cumulative residuals after portfolio generation: %s", cumResiduals)
	
	# Sort shares in order of cumulative residual
	sortedShareCodes = sorted(cumResiduals, key=lambda s: cumResiduals[s])		

	logger.info("Finished picking winners and losers.")
 
	return {"losers":sortedShareCodes[0:numWinnersLosers], "winners":sortedShareCodes[-numWinnersLosers:]}


def calcShareResidual(date, shareCode, lastKnownPrices, prices, marketPercentReturn):
	"""
	Calculate a share's:
		- absolute return (difference between previous value and current value)
		- percentage return (absolute return as a percentage of previous value)
		- residual (percentage return - market percentage return)

	The date is only used for logging.
	lastKnownPrices is a {shareCode->price} dict of the last known prices of each share.
	It is updated by this method.
	prices is a {shareCode->price} dict of this month's prices of each share.
	marketPercentReturn is the average or total percentage return of all shares in the market this month. 
	"""
	if shareCode in prices:
		sharePrice = prices[shareCode]
	else:
		# Deal with missing prices
		logger.info("%s: Price missing for share code %s. Setting equal to last known price %s", date, shareCode, lastKnownPrices[shareCode])
		sharePrice = lastKnownPrices[shareCode]

	# Calculate share return Rj
	absoluteReturn = sharePrice - lastKnownPrices[shareCode]
	percentReturn = calcPercentReturn(lastKnownPrices[shareCode], sharePrice)

	# Update the last known price for this share
	lastKnownPrices[shareCode] = sharePrice

	# Calculate residual Rj - Rm
	residual = percentReturn - marketPercentReturn

	return (absoluteReturn, percentReturn, residual)


def calcMarketAverageReturn(date, prevPrices, currPrices):
	"""
	Calculate the average percentage return for all
	the shares that were in the market in both the previous month and this month.
	Skip any shares which have dropped out of the market this month.

	The date is only used for logging. 
	"""
	marketSumReturn = 0.0
	marketSharesCount = 0
	for shareCode in prevPrices:
		if shareCode in currPrices:
			marketSumReturn += calcPercentReturn(prevPrices[shareCode], currPrices[shareCode])
			marketSharesCount += 1
		else:
			logger.info("%s: Share code %s appears to have dropped out of the market.", date, shareCode)
	marketAvgReturn = marketSumReturn / marketSharesCount	

	logger.info("Market avge return for %s = %s%% (%s shares)", date, marketAvgReturn, marketSharesCount)
	return marketAvgReturn


def calcMarketTotalReturn(date, prevPrices, currPrices):
	"""
	Calculate the percentage return for the market, i.e. the total of all
	the shares that were in the market in both the previous month and this month.
	Skip any shares which have dropped out of the market this month.

	The date is only used for logging. 
	"""
	marketPrevSum = 0.0
	marketCurrSum = 0.0
	marketSharesCount = 0
	for shareCode in prevPrices:
		if shareCode in currPrices:
			marketPrevSum += prevPrices[shareCode]
			marketCurrSum += currPrices[shareCode]
			marketSharesCount += 1
		else:
			logger.info("%s: Share code %s appears to have dropped out of the market.", date, shareCode)
	marketTotalReturn = marketCurrSum - marketPrevSum
	marketTotalPercentReturn = calcPercentReturn(marketPrevSum, marketCurrSum)

	logger.info("Market total return for %s = %s%% (%s) (%s shares)", date, marketTotalPercentReturn, marketTotalReturn, marketSharesCount)
	return marketTotalPercentReturn

	
	
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
	parser.add_option("-t", "--totalreturn", action="store_true", dest="useMarketTotalReturn",
				help="Use market total % return to calculate residuals. (Default: use market average % return)")
	return parser

# Allow file to be run as "python winnerslosers.py <optionsAndArgs>"
if __name__ == "__main__":
    main(sys.argv)
