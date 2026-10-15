'''

	Objective:
		- Get customer's usages details from Energy Provider thro API calls


	usage: get.py [-h] [-date DATE]

		Download customer's usages from Energy Provider

		optional arguments:
			-h, --help  show this help message and exit
			-date DATE  Fetch data for a specific date (YYYY-MM-DD)


	Dependency:
		pip install requests
		pip install pymysql
		pip install pytz



	Version: 20250101_v001 [Developing]


	Changelog:
		- 20250101_v001		--> Initial Version. 
		

	Functions List:
		def main(argUserid, argIP, argOperation, argScheduleID):


	Remark:
		For Deployment:
			1. Update Version number
			2. Set the Indicator from '[Developing]' to '[Released]'
			3. Ensure ChangeLog is correct
			4. Copy from Sandbox to Production by eliminating '_vX' suffix

'''



import requests
from datetime import datetime
import pymysql
import logging
from logging.handlers import TimedRotatingFileHandler
import os
import argparse
from datetime import datetime, timedelta
import pytz

# Define constants
SLEEP_DURATION = 60		# Time to sleep in seconds
MAX_RETRIES = 5	 # Maximum number of retries for database connection
RETRY_DELAY = 5	 # Delay in seconds between retries

SYSTEM_NAME = 'Scheduler [Series.2]'
SYSTEM_VER = '20241225_v001'
DEVELOPER_MODE = 0			#  Developer mode: ON (1) | OFF (0)
ENVIRONMENT = "Sandbox" if "Sandbox" in os.path.abspath(os.path.dirname(__file__)) else "Production"

BASE_URL = "https://api.octopus.energy/v1"
APIKEY = 'MASKED_PASSWORD'
E_MPAN = 'MASKED_PASSWORD'
E_MSN = 'MASKED_PASSWORD'
E_TARIFF = 'MASKED_PASSWORD'
G_MPAN = 'MASKED_PASSWORD'
G_MSN = 'MASKED_PASSWORD'
G_TARIFF = 'MASKED_PASSWORD'


# Set log level: use logging.INFO for production and logging.DEBUG for development
LOG_LEVEL = logging.DEBUG  if "Sandbox" in os.path.abspath(os.path.dirname(__file__)) else logging.INFO 

# Database connection parameters
DB_CONFIG = {
	'host': 'YOUR_DATABASE_HOST',
	'user': 'YOUR_DATABASE_USER',
	'password': 'YOUR_DB_PASSWORD',
	'database': 'YOUR_DATABASE_NAME',
}


########################################################################

# Configure logging
log_handler = TimedRotatingFileHandler(
	"./Sandbox/smartProject/.logs/getUsage.log" if ENVIRONMENT == 'Sandbox' else "./Production/smartProject/.logs/getUsage.log",
	when="midnight",		 # Rotate at midnight every day
	interval=1,				 # Every 1 day
	backupCount=7			 # Keep logs for the last 7 days
)

log_handler.setLevel(LOG_LEVEL)	 # Use logging.DEBUG here, not logging.debug
log_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

logging.basicConfig(

	# For Release, set logging.INFO;
	# For development, set logging.DEBUG
	level=LOG_LEVEL,
	format='%(asctime)s - %(levelname)s - %(message)s',	 # Format of the log messages
	handlers=[
		log_handler,
		logging.StreamHandler()	 # Log to console as well
	]
)

# Create logger instance
logger = logging.getLogger(__name__)


#################################################
##	This section is used to load other modules ##
#################################################

# Completed
def connect_with_retry():
	
	# Function to connect to the database with retry mechanism
	# Return: conn
	
	logger.info("[connect_with_retry][I01]:IN")
		
	"""Attempt to connect to the database, retrying if necessary."""
	for attempt in range(MAX_RETRIES):
		try:
			conn = pymysql.connect(**DB_CONFIG)	 # Use pymysql.connect() instead of mysql.connector.connect()
			if conn.open:
				logger.debug("[connect_with_retry][D01]: <Database connection successful>")
				logger.info("[connect_with_retry][I02]:OUT")
				return conn
				
		except pymysql.MySQLError as e:
			logger.error(f"[connect_with_retry][E01]: <Attempt {attempt + 1} - Database connection failed: {e}>")
			time.sleep(RETRY_DELAY)

		except Exception as e:
			logger.error(f"[connect_with_retry][E02]: <Unexpected error during connection attempt {attempt + 1}: {e}>")
			time.sleep(RETRY_DELAY)

	logger.error("[connect_with_retry][E03]: <Failed to connect to the database after several attempts.>")
	logger.info("[connect_with_retry][I03]:OUT")
	return False



# Function to convert UTC timestamps to Europe/London timezone
def convert_utc_to_london_time(utc_time_str):
	
	#  This function is used to convert UTC timestamp to local time
	#  Return: london_time (datetime)
	
	logger.info(f"[convert_utc_to_london_time][I01]: IN")
	#logger.debug(f'[convert_utc_to_london_time][D01]: utc_time_str:{utc_time_str}')
	#logger.debug(f"[convert_utc_to_london_time][D02]: <Converting UTC timestamp '{utc_time_str}' to London time>")
	
	utc_time = datetime.fromisoformat(utc_time_str.replace("Z", "+00:00"))
	utc_timezone = pytz.utc
	
	#logger.debug(f"[convert_utc_to_london_time][D03]: utc_timezone:{utc_timezone}")
	
	london_timezone = pytz.timezone("Europe/London")

	if utc_time.tzinfo is None:
		#logger.debug(f"[convert_utc_to_london_time][D04]: utc_time(Before):{utc_time}")
		utc_time = utc_timezone.localize(utc_time)
		#logger.debug(f"[convert_utc_to_london_time][D05]: utc_time(After):{utc_time}")

	london_time = utc_time.astimezone(london_timezone)
	
	#logger.debug(f"[convert_utc_to_london_time][D06]: london_time:{london_time} ({type(london_time)})")
	logger.info("[convert_utc_to_london_time][I02]: OUT")
	
	return london_time


def getUsage(date):
	
	# Function to download energy consumption from Energy Provider
	# Return: Success | Fail
	
	
	logger.info("[getUsage][I01]:IN")
	logger.debug(f"[getUsage][D01]: date:{date}; type(date):{type(date)}");
	
	
	# Define time range for the data
	start_date = date.isoformat() + "T00:00:00Z"  # ISO 8601 format
	end_date = date.isoformat() + "T23:59:59Z"

	categories = ['E', 'G']

	
	for category in categories:
		
		if category == 'E':
			url = f"{BASE_URL}/electricity-meter-points/{E_MPAN}/meters/{E_MSN}/consumption/"
		else:
			url = f"{BASE_URL}/gas-meter-points/{G_MPAN}/meters/{G_MSN}/consumption/"
	
		logger.debug(f"[getUsage][D01]: start_date:{start_date}; end_date:{end_date}; category:{category}; url:{url}")
		
		response = requests.get(
			url,
			params={"period_from": start_date, "period_to": end_date},
			auth=(APIKEY, "")  # API Key as the username; password is left blank
		)
	
		# Make the API request
		if response.status_code == 200:
			
			data = response.json()
			
			conn = connect_with_retry()
			cursor = conn.cursor(pymysql.cursors.DictCursor)  # Use pymysql cursor for dictionary results
			
			for item in data["results"]:
				sql = """
					INSERT INTO usages (start, consumption, category)
					VALUES (%s, %s, %s)
					ON DUPLICATE KEY UPDATE
						consumption = VALUES(consumption),
						category = VALUES(category)
				"""
				params = (item['interval_start'], item['consumption'], category)
				
				try:
					cursor.execute(sql, params)
					#logger.debug(f"[getUsage][D02]: Time:{item['interval_start']}; LocalTime:{convert_utc_to_london_time(item['interval_start'])}; Consumption:{item['consumption']} kWh; category:{category}")
					logger.debug(f"[getUsage][D02]: Time:{item['interval_start']}; Consumption:{item['consumption']} kWh; category:{category}")
					
				except pymysql.MySQLError as e:
					logger.error(f"[getUsage][E01]: SQL Error: {e}")
			
			conn.commit()
			cursor.close()
			conn.close()
		else:
			logger.error(f"[getUsage][E02]: <Failed to fetch data: {response.status_code} - {response.text}>")
			logger.info("[getUsage][I02]:OUT")
			return 'Fail'
			
	logger.info("[getUsage][I03]:OUT")
	return 'Success'
	

def getLatestDate():
	
	#  This function is used to get the latest record date
	#  Return: date::datetime
	
	
	logger.info("[getLatestDate][I01]: IN")
	
	conn = connect_with_retry()
	cursor = conn.cursor(pymysql.cursors.DictCursor)  # Use pymysql cursor for dictionary results
		
	sql = "select date(start) as start from usages ORDER BY start DESC LIMIT 1"
	
	logger.debug(f"[getLatestDate][D01]: sql:{sql}")
	
	cursor.execute(sql)
	result = cursor.fetchone()	# Fetch the result
	
	if result:
		latestDate = result['start']  # Fetch the start date from the result
		logger.debug(f"[getLatestDate][D02]: latestDate:{latestDate}; type(latestDate):{type(latestDate)}")
	
		if conn.open:
				conn.close()
			
		logger.info("[getLatestDate][I02]: OUT;")
		return latestDate
	else:
		logger.info("[getLatestDate][I03]: OUT;")
		return None


def main(argDate):
		
	logger.info(f"------>  ")
	logger.info("------>  DataSync Started	  ---")
	logger.info(f"------>  {SYSTEM_NAME} . Version {SYSTEM_VER}	 <------")
	logger.info(f"------>  Last Updated: {datetime.fromtimestamp(os.path.getmtime(__file__))}  <------")
	logger.info(f"------>  ")
	
	logger.info("[main][I01]: IN")
	logger.debug(f"[main][D01]: args.date:{args.date}; type(args.date):{type(args.date)}")
	
	if DEVELOPER_MODE == 1:
		logger.info(f"------>  ")
		logger.info(f"------>  ~ ~ ~ ~ ~ ~	 D E V E L O P E R	 M O D E   ~ ~ ~ ~ ~ ~ ")
		logger.info(f"------>  ")
		
		
		print(f"getLatestDate:{getLatestDate()}; type(getLatestDate):{type(getLatestDate())}")
		#getUsage(getLatestDate())
	
		logger.info(f"------>  ")
		logger.info(f"------>  ~ ~ ~ ~ ~ ~	 D E V E L O P E R	 M O D E   E n d e d   ~ ~ ~ ~ ~ ~ ")
		logger.info(f"------>  ")
		
		exit()
		
	if args.date:
		
		start_date = datetime.strptime(args.date, "%Y-%m-%d").date()
		logger.debug(f"[main][D01]: start_date:{start_date};")
		result = getUsage(start_date)
		logger.debug(f"[main][D01]: result:{result}; start_date:{start_date};")
		
	else:
		
		# Prepare to loop in getting usage data
		start_date = getLatestDate()
		if not start_date:
			start_date = '2024-01-24'
			start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
			
		end_date = datetime.now() + timedelta(days=1)
		end_date = end_date.date()
		
		current_date = start_date
		
		logger.debug(f"[main][D02]: start_date:{start_date}:{type(start_date)}; end_date:{end_date}:{type(end_date)}; current_date:{current_date}:{type(current_date)};")
		
		while current_date <= end_date:
			result = getUsage(current_date)
			current_date += timedelta(days=1)
			logger.debug(f"[main][D03]: result:{result}; current_date:{current_date};")
	
	logger.info(f"[main][I02]: OUT")
	logger.info("---  getUsage Ended  ---")


if __name__ == "__main__":
	
	
	parser = argparse.ArgumentParser(
		description='Download customer\'s usages from Energy Provider'
	)
	parser.add_argument("-date", type=str, help="Fetch data for a specific date (YYYY-MM-DD)")
	args = parser.parse_args()

	# Custom validation logic for conditional arguments
	
	# Call the main function
	main(args.date)

