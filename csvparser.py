# coding:UTF-8

import os
import sys
import re
import logging
import logging.config
import string
import time
import csv
from datetime import datetime, date
from pprint import pprint
from operator import itemgetter

# Set up logging using config file
logging.config.fileConfig(os.path.join(sys.path[0], "logging.conf"))
logger = logging.getLogger("WinnersLosers")

def parseCsvFile(csvFile, dateFormat='%b-%y'):
	"""
	Read a CSV file, parse the share codes
	from the header, then parse the remaining lines
	into a list of (date, {shareCode->price}) tuples.
	Return the list of tuples and the list of share codes.
	The list of tuples is guaranteed to be in ascending date order
	(i.e. newest date is last in the list)
	"""
	logger.info("Opening CSV file %s", csvFile)
	with open(csvFile) as f:
		csvReader = csv.reader(f)

		# Parse the list of share codes from first line
		shareCodes = parseHeader(csvReader.next())
		logger.debug('Share codes: %s', shareCodes)

		# Create a list of (date, dict{shareCode->price}) tuples from remaining lines
		dates = []
		for row in csvReader:
			(date, shareAndPrice) = parseRow(row, shareCodes, dateFormat)
			logger.debug("Shares and prices for date %s", date)
			logger.debug(shareAndPrice)
			dates.append((date,shareAndPrice))

	logger.info("Successfully parsed CSV file %s. Found %i dates and %i share codes", csvFile, len(dates), len(shareCodes))
	return (sorted(dates, key=itemgetter(0)), shareCodes)

def parseHeader(cells):
	"""
	 Ignore the first cell, which will be empty
	 or will just say 'Date' or something like that.
	Trim spaces from the remaining cells.
	"""
	return [s.strip() for s in cells[1:]]

def parseRow(cells, shareCodes, dateFormat='%b-%y'):
	"""
	Parse a CSV row of the form 'date,price1,price2,...'
	into a tuple (date, {share1->price1,share2->price2,...})

	Default dateformat is e.g. 'Mar-09'
	"""
	theDate = datetime.strptime(cells[0].strip(), dateFormat).date()
	# To make sure we compare dates correctly, set date to first day of month
	theDate = date(theDate.year, theDate.month, 1)

	sharePrices = dict()
	for shareCode,priceString in zip(shareCodes, [s.strip() for s in cells[1:]]):
		if len(priceString) > 0:
			try:
				sharePrices[shareCode] = float(priceString)
			except ValueError:
				logger.debug("Failed to parse price '%s' for share code %s", priceString, shareCode) 
	return (theDate,sharePrices)


