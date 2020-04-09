import logging
import sys
from datetime import datetime

PATH_OF_CHROME_DRIVER = 'chromedriver_linux64/chromedriver'
JOBS_IN_ISRAEL = 'https://www.glassdoor.com/Job/israel-jobs-SRCH_IL.0,6_IN119.htm?fromAge=1&radius=25'
JOBS_IN_UK = 'https://www.glassdoor.com/Job/uk-jobs-SRCH_IL.0,2_IN2.htm?fromAge=1&radius=25'
DATA_SCIENTISTS_USA = 'https://www.glassdoor.com/Job/us-data-scientist-jobs-SRCH_IL.0,2_IN1_KO3,' \
                      '17.htm?fromAge=1&radius=25'
INITIAL_LINKS = [JOBS_IN_ISRAEL, DATA_SCIENTISTS_USA, JOBS_IN_UK]
START_OF_LOCATION = 3
RELOAD_TRIALS = 3

logger = logging.getLogger("glassdoor_scraper")
logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler(f'GDScraper_{datetime.now()}.log')
file_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
logger.addHandler(logging.StreamHandler(sys.stdout))
