# coding:UTF-8

import sys
import math
import csv
import logging
import logging.config
from datetime import datetime, date

logging.config.fileConfig("logging.conf")
logger = logging.getLogger("WinnersLosers")

suffixes = [
		' absolute return',
		' % return',
		' % residual'
		]

def writeCsvHeader(writer, winnersAndLosers):
	header = [  
		'Date',
		'Market avge return (%)',
		'Market total return (%)',
		]
	for winner in winnersAndLosers['winners']:
		header += map(lambda str: 'Winner [' + winner + ']' + str, suffixes) 
	for loser in winnersAndLosers['losers']:
		header += map(lambda str: 'Loser [' + loser + ']' + str, suffixes) 

	writer.writerow(header)


