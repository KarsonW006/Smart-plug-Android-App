'''
	Program: dataSync.py [aka dataSync_v16.py]

	Objective:
		- Get pricing data from Octopus Energy through the API call provided by the services provider
		- Fetch Octopus pricing data and update MySQL database.


	Usage: dataSync.py [-h] [--no_email] [--quiet] [--date date]

		   optional arguments:
				-h, --help			  show this help message and exit
				-no_email			  Suppress in  sending email with the fetched pricing data
				-date date			  Fetch data for a specific date (YYYY-MM-DD)


	Dependency:
		pip install requests
		pip install pymysql
		pip install pytz


	Version: 20250220_v001 [Released]


	Changelog:
		- 20240228_v001		--> Initial Version. Call and display Octopus API to get the JSON data
		- 20240831_v003		--> [Add] Allow current date data to insert into database
		- 20240908_v005		--> [Add] Allow user to get a period of data
		- 20240923_v001		--> [Add] Log function
		- 20240929_v002		--> [Update] Bug fixed - Time zone and Daylight saving time
		- 20241002_v001		--> [Add] Allow mute the Log event display
		- 20241015_v013		--> [Add] Enhance the script to get a specific date's data
		- 20241016_v001		--> [Add] Export all executed insert queries to a plain text file
		- 20241018_v013		--> [Add] Email a execution report to user
		- 20241023_v002		--> [Add] Take Log into table _status
		- 20241024_v001		--> [Add] Add a control flag to ensure latest update collected
		- 20241026_v002		--> [Amend] Cope with datebase field change: DateTime-2-TimeStamp
		- 20241101_v001		--> [Update] Change the algorithm in detecting records are captured correctly.
		- 20241115_v001		--> [Change] Fixing unstable database server issue (Connection V2)
		- 20241117_v001		--> [Change] Implemented retry mechanism in getting data from API
		- 20241118_v001		--> [Add] Add more Debug level logging
		- 20241225_v001		--> Initial Version 2.	Project directory structural revamp
		- 20250130_v001		--> [Change] Enhance the start date and end date calculation algorithm
		- 20250220_v001		--> [Change] Reengine sync algorithm
		- 20250316_v001		--> [Publish] Finalized and Released for production


	Functions List:
		def connect_with_retry():
		def rtnLastDate():
		def isCutOff():
		def isToday(inputDate):
		def convert_utc_to_london_time(utc_time_str):
		def getPricingInfo(start_date):
		def sendEmail(prices):
		def storeData2DB(prices):
		def cleanup_old_backups():
		def main():


	REMARK:
	`	SELECT * FROM rates WHERE date(valid_from) = CURDATE()+1  AND (select COUNT(*) FROM rates WHERE DATE(valid_from) = CURDATE()+1) = 46;


'''

import requests
import pymysql
from datetime import datetime, timedelta, date
import pytz
import logging
from logging.handlers import TimedRotatingFileHandler
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import argparse
import time
import os


# Define constants for the Octopus API
PRODUCT_CODE = "AGILE-FLEX-22-11-25"
TARIFF_CODE = "E-1R-AGILE-FLEX-22-11-25-A"
PRODUCT_CODE = "AGILE-24-10-01"
TARIFF_CODE = "E-1R-AGILE-24-10-01-A"
CUTOFF_TIME = "16:00"

OCTOPUS_API_URL = f"https://api.octopus.energy/v1/products/{PRODUCT_CODE}/electricity-tariffs/{TARIFF_CODE}/standard-unit-rates/"

#https://api.octopus.energy/v1/products/AGILE-24-10-01/electricity-tariffs/E-1R-AGILE-24-10-01-A/standard-unit-rates/

# Database connection parameters
DB_CONFIG = {
	'host': 'YOUR_DATABASE_HOST',
	'user': 'YOUR_DATABASE_USER',
	'password': 'YOUR_DB_PASSWORD',
	'database': 'YOUR_DATABASE_NAME',
}


# Email configuration
SMTP_SERVER = 'smtp.gmail.com'	# Gmail SMTP server
SMTP_PORT = 465					 # Port for SSL
EMAIL_USER = 'your-email@example.com'	 # Your email
EMAIL_PASSWORD = 'MASKED_PASSWORD'	# Your app password
RECIPIENT_EMAIL = 'your-email@example.com'  # Recipient email
EMAIL_SUBJECT = 'Octopus Pricing Data: ' + str(datetime.now(pytz.timezone('Europe/London')))


# Constants
SLEEP_DURATION = 60		# Time to sleep in seconds
MAX_RETRIES = 5			# Maximum number of retries for database connection
RETRY_DELAY = 5			# Delay in seconds between retries
RETRY_LIMIT = 30		# Max retries for API requests
BACKOFF_TIME = 60		# Seconds to wait between retries after an error
MAX_BACKUP_FILES = 7	# Number of backups to retain


SYSTEM_NAME = 'dataSync [Series.2]'
SYSTEM_VER = '20250316_v001'
DEVELOPER_MODE = 0			#  Developer mode: ON (1) | OFF (0)
ENVIRONMENT = "Sandbox" if "Sandbox" in os.path.abspath(os.path.dirname(__file__)) else "Production"


# File to export SQL statements
SQL_BACKUP_DIR = "./Sandbox/smartProject/.logs" if ENVIRONMENT == 'Sandbox' else "./Production/smartProject/.logs"
SQL_FILE_SUFFIX = "_insertQuery"  # Suffix for SQL backup files


# Set log level: use logging.INFO for production and logging.DEBUG for development
LOG_LEVEL = logging.DEBUG  if "Sandbox" in os.path.abspath(os.path.dirname(__file__)) else logging.INFO


# Configure logging
log_handler = TimedRotatingFileHandler(
	"./Sandbox/smartProject/.logs/dataSync.log" if ENVIRONMENT == 'Sandbox' else "./Production/smartProject/.logs/dataSync.log",
	when="midnight",  # Rotate logs daily at midnight
	interval=1,		  # Every 1 day
	backupCount=MAX_BACKUP_FILES
)
log_handler.setLevel(LOG_LEVEL)
log_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

logging.basicConfig(
	level=LOG_LEVEL,
	format='%(asctime)s - %(levelname)s - %(message)s',	 # Format of the log messages
	handlers=[
		log_handler,
		logging.StreamHandler()	 # Log to console as well
	]
)
logger = logging.getLogger(__name__)



######################
##	Functions Area	##
######################


# Function to connect to the database with retry mechanism
def connect_with_retry():

	#  This function is used to make a database connection
	#  Return: conn (database connection object)


	logger.info("[connect_with_retry][I01]: IN")

	"""Attempt to connect to the database, retrying if necessary."""
	for attempt in range(MAX_RETRIES):
		try:
			conn = pymysql.connect(**DB_CONFIG)	 # Use pymysql.connect() instead of mysql.connector.connect()
			if conn.open:
				logger.debug("[connect_with_retry][D01]: <Database connection successful>")
				logger.info("[connect_with_retry][I02]: OUT;")
				return conn
		except pymysql.MySQLError as e:
			logger.error(f"[connect_with_retry][E01]: Attempt {attempt + 1} - Database connection failed: {e}")
			time.sleep(RETRY_DELAY)
	raise Exception("[connect_with_retry][E02]: Failed to connect to the database after several attempts.")



# Updated
# Function to return the latest date of pricing data
def rtnLastDate():

	#  This function is used to get the latest date of available pricing information
	#  Return: date (datetime)

	logger.info(f"[rtnLastDate][I01]: IN")
	logger.debug(f'[rtnLastDate][D01]: None')

	try:
		conn = connect_with_retry()
		cursor = conn.cursor()

		sql = 'select max(valid_from) from rates'
		cursor.execute(sql)
		result = cursor.fetchall()

		logger.debug(f'[rtnLastDate][D02]: sql:{sql}')
		logger.debug(f'[rtnLastDate][D03]: result[0][0]:{result[0][0]}')
		return result[0][0]

	except pymysql.MySQLError as err:
		logger.error(f"[storeData2DB][E01]: <Error executing SQL statement: {err}>")

	finally:
		if conn.open:
			conn.close()
		logger.info(f"[rtnLastDate][I02]: OUT")



# Function to check whether current time is later than 22:00 of current date
def isCutOff():

	#  This function is used to check whether current time is later than 22:00
	#  Return: True | False

	logger.info("[isCutOff][I01]: IN")
	current_time = datetime.now().time()  # Get the current time
	cutoff_time = datetime.strptime(CUTOFF_TIME, "%H:%M").time()  # Define 22:00 as a time object

	logger.debug(f'[isCutOff][D01]: current_time:{current_time}; cutoff_time:{cutoff_time}')
	logger.info("[isCutOff][I02]: OUT")

	return current_time >= cutoff_time



# Function to check whether current date of run time is today
def isToday(inputDate):

	#  This function is used to check whether current date is today
	#  Return: -1 | 0 | 1  (Past | Current | Future)
	
	logger.info("[isToday][I01]: IN")
	logger.debug(f'[isToday][D01]: inputDate:{inputDate}')
	
	"""Check if the given date is today's date."""
	if inputDate.date() == date.today():
		logger.debug(f'[isToday][D01]: 0:0')
		logger.info("[isToday][I02]: OUT")
		return 0

	elif inputDate.date() < date.today():
		logger.debug(f'[isToday][D01]: -1:-1')
		logger.info("[isToday][I03]: OUT")
		return -1

	elif inputDate.date() > date.today():
		logger.debug(f'[isToday][D01]: 1:1')
		logger.info("[isToday][I04]: OUT")
		return 1



# Function to check whether the current date 
def isSummer(inputDate, timezone="Europe/London"):
	"""
	Returns:
		bool: True if inputDate is in DST, False otherwise.
	"""
	logger.info("[isSummer][I01]: IN")
	logger.debug(f'[isSummer][D01]: inputDate:{inputDate}')

	if isinstance(inputDate, str):
		try:
			# Handle ISO 8601 format and extract only date part
			if inputDate.endswith("Z"):	 # Convert UTC 'Z' to '+00:00' for parsing
				inputDate = inputDate.replace("Z", "+00:00")
			inputDate = datetime.fromisoformat(inputDate)
		except ValueError:
			raise ValueError("Invalid date format. Use ISO 8601 format: YYYY-MM-DDTHH:MM:SS[Z] or YYYY-MM-DD.")
	
	# Ensure inputDate is timezone-aware
	tz = pytz.timezone(timezone)
	inputDate = inputDate.astimezone(tz)
	
	logger.debug(f'[isSummer][D02]: localized_date:{inputDate}; bool(inputDate.dst()):{bool(inputDate.dst())}')
	logger.info("[isSummer][I02]: OUT")
	
	return bool(inputDate.dst())


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

	london_time = utc_time.astimezone(london_timezone)#

	#logger.debug(f"[convert_utc_to_london_time][D06]: london_time:{london_time} ({type(london_time)})")
	logger.info("[convert_utc_to_london_time][I02]: OUT")

	return london_time


def getPricingInfo(start_date):

	#  This function is used to get pricing data from Energy Provider by using API call.
	#  Return: prices (Dict)

	logger.info(f"[getPricingInfo][I01]: IN")
	logger.debug(f'[getPricingInfo][D01]: start_date:{start_date}')
	
	attempts = 0

	#  Preparing API Connection String
	#
	
	if isToday(start_date) == 0:
		request_url = f"{OCTOPUS_API_URL}"
		
	elif isToday(start_date) == -1:

		end_date = start_date + timedelta(days=1)

		period_from = start_date.strftime("%Y-%m-%d")
		period_to = end_date.strftime("%Y-%m-%d")

		request_url = f"{OCTOPUS_API_URL}?period_from={period_from}&period_to={period_to}"
		logger.debug(f"[getPricingInfo][D02]: {start_date} to {end_date}>")

	
	logger.debug(f"[getPricingInfo[D03]: request_url:{request_url}")

	while attempts < RETRY_LIMIT:
		try:
			
			response = requests.get(request_url)
			response.raise_for_status()
			data = response.json()
			
			exitReason = "Error-Free"
			
			# Check if there's at least one result
			if not data.get('results'):
				attempts +=1
				exitReason = "No data returned from the API"
				logger.debug(f"[getPricingInfo][D04]: (No data returned from the API)")
				
			elif isToday(start_date) == -1:
				
				first_entry_valid_from = data['results'][0].get('valid_from')
				
				if isSummer(first_entry_valid_from):
					expected_record = (start_date).replace(hour=22, minute=30, second=0, microsecond=0)
				else:
					expected_record = (start_date).replace(hour=23, minute=30, second=0, microsecond=0)
					
				if first_entry_valid_from:
					# Convert `valid_from` to a datetime object
					
					first_entry_valid_from = first_entry_valid_from.replace("T", " ").replace("Z", "").replace("+00:00", "").replace("+01:00", "")
					first_entry_datetime = datetime.fromisoformat(first_entry_valid_from.replace('Z', '+00:00'))

					if first_entry_datetime == expected_record:
						logger.debug("[getPricingInfo][D05]: Valid records Downloaded [-1|2330]")
						break  # Exit the loop and proceed with processing
					else:
						logger.debug("[getPricingInfo][D06]: Invalid records returned. [-1|2330]")
						attempts +=1
						exitReason = "First entry does not match [-1|23:30]"
					
			elif isToday(start_date) == 0 and isCutOff():
				#expected_record = (datetime.now() + timedelta(days=1)).replace(hour=22, minute=30, second=0, microsecond=0)
				first_entry_valid_from = data['results'][0].get('valid_from')
				
				if isSummer(first_entry_valid_from):
					expected_record = (start_date).replace(hour=21, minute=30, second=0, microsecond=0)
				else:
					expected_record = (start_date).replace(hour=22, minute=30, second=0, microsecond=0)
				
				if first_entry_valid_from:
					# Convert `valid_from` to a datetime object
					
					first_entry_valid_from = first_entry_valid_from.replace("T", " ").replace("Z", "").replace("+00:00", "").replace("+01:00", "")
					first_entry_datetime = datetime.fromisoformat(first_entry_valid_from.replace('Z', '+00:00'))

					if first_entry_datetime == expected_record:
						logger.debug("[getPricingInfo][D07]: Valid records Downloaded [0|2230+1]")
						break  # Exit the loop and proceed with processing
					else:
						logger.debug("[getPricingInfo][D08]: Invalid records returned. [-1|2230+1]")
						attempts +=1
						exitReason = "First entry does not match [0|22:30+1]"
						
			elif isToday(start_date) == 0 and not isCutOff():
				#expected_record = datetime.now().replace(hour=22, minute=30, second=0, microsecond=0)
				first_entry_valid_from = data['results'][0].get('valid_from')
				
				if isSummer(first_entry_valid_from):
					expected_record = (start_date).replace(hour=21, minute=30, second=0, microsecond=0)
				else:
					expected_record = (start_date).replace(hour=22, minute=30, second=0, microsecond=0)
				
				logger.debug(f"[getPricingInfo][Dxx]: expected_record:{expected_record}; first_entry_valid_from:{first_entry_valid_from}")
				
				if first_entry_valid_from:
					# Convert `valid_from` to a datetime object
					
					first_entry_valid_from = first_entry_valid_from.replace("T", " ").replace("Z", "").replace("+00:00", "").replace("+01:00", "")
					first_entry_datetime = datetime.fromisoformat(first_entry_valid_from.replace('Z', '+00:00'))

					if first_entry_datetime == expected_record:
						logger.debug("[getPricingInfo][D09]: Valid records Downloaded [0|2230]")
						break  # Exit the loop and proceed with processing
					else:
						logger.debug("[getPricingInfo][D10]: Invalid records Downloaded [0|2230+1]")
						attempts +=1
						exitReason = "First entry does not match [0|22:30]"
						
			else:
				attempts +=1
				logger.debug("[getPricingInfo][D11]: Unknown Error")
				exitReason = "Unknown Error"

		except requests.exceptions.HTTPError as e:
			attempts += 1
			logger.error(f"[getPricingInfo][E01]: <HTTPError encountered: {e}. Attempt {attempts}/{RETRY_LIMIT}. Retrying in {BACKOFF_TIME} seconds>")
			time.sleep(BACKOFF_TIME)

		except requests.exceptions.RequestException as e:
			logger.error(f"[getPricingInfo][E02]: <Request failed: {e}. Retrying in {BACKOFF_TIME} seconds>")
			time.sleep(BACKOFF_TIME)

		# Wait before retrying if no match found
		time.sleep(SLEEP_DURATION)

	if attempts >= RETRY_LIMIT:
		logger.debug(f"[getPricingInfo][D12]: Return None")
		logger.info("[getPricingInfo][I02]: OUT")
		return[]
		
	#  After successful match, process data
	#
	prices = [
		(result.get('valid_from'), result.get('valid_to'), result.get('value_inc_vat'), result.get('value_exc_vat'))
		for result in data.get('results', [])
	]
	logger.debug(f"[getPricingInfo][D13]: prices:{prices}")
	logger.info("[getPricingInfo][I03]: OUT")
	return prices



# Function to send an email with the pricing data
def sendEmail(prices):

	#  This function is used to send out email notification to admin about data synchronized
	#  Return: None

	logger.info(f"[sendEmail][I01]: IN")
	logger.debug(f'[sendEmail][D01]: prices:{prices}')
	logger.debug("[sendEmail][D02]: <Preparing email with Octopus pricing data>")


	# Create the email message
	msg = MIMEMultipart()
	msg['From'] = EMAIL_USER
	msg['To'] = RECIPIENT_EMAIL
	msg['Subject'] = EMAIL_SUBJECT

	# Create a table as HTML content
	html_content = "<h3>Octopus Pricing Data (From, To, Price (p / kWh))</h3>"
	html_content += "<table border='1' style='border-collapse: collapse;'>"
	html_content += "<tr><th>From (London Time)</th><th>To (London Time)</th><th>Price (p / kWh)</th><th>From (UTC Time)</th><th>To (UTC Time)</th></tr>"

	for valid_from_utc, valid_to_utc, value_inc_vat, value_exc_vat in prices:

		valid_from_london = convert_utc_to_london_time(valid_from_utc)
		valid_to_london = convert_utc_to_london_time(valid_to_utc)

		valid_from_utc = valid_from_utc.replace("T", " ").replace("Z", "+00:00")
		valid_to_utc = valid_to_utc.replace("T", " ").replace("Z", "+00:00")

		# Convert timestamps back to datetime for display
		html_content += f"<tr><td>{valid_from_london}</td><td>{valid_to_london}</td><td align=right>{value_inc_vat}</td><td>{valid_from_utc}</td><td>{valid_to_utc}</td></tr>"

	html_content += "</table>"

	# Add the "Last updated" timestamp with date and time at the bottom of the HTML content
	last_updated = datetime.now(pytz.timezone('Europe/London')).strftime('%Y-%m-%d %H:%M')
	html_content += f"<p style='margin-top: 20px;'>Last updated: {last_updated}</p>"

	msg.attach(MIMEText(html_content, 'html'))

	# Send the email using SMTP
	try:
		logger.debug(f"[sendEmail][D03]: <Sending email to {RECIPIENT_EMAIL}>")

		with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
			server.login(EMAIL_USER, EMAIL_PASSWORD)
			server.send_message(msg)
			logger.debug(f"[sendEmail][D04]: <Email sent to {RECIPIENT_EMAIL}>")

	except Exception as e:
		logger.error(f"[sendEmail][E01]: <Failed to send email: {e}>")

	logger.info("[sendEmail][I02]: OUT")



# Updated
# Function to save and execute SQL statements
def storeData2DB(prices):

	#  This function is used to save pricing data into the database
	#  Return: sql_file_name (plain text file)

	logger.info(f"[storeData2DB][I01]: IN")
	logger.debug(f"[storeData2DB][D01]: price:{prices}")

	# Generate the backup file name with a timestamp prefix
	today_date = datetime.now().strftime("%Y%m%d")
	sql_file_name = f"{today_date}_{SQL_FILE_SUFFIX}.sql"
	sql_file_path = os.path.join(SQL_BACKUP_DIR, sql_file_name)

	try:
		conn = connect_with_retry()
		cursor = conn.cursor()

		with open(sql_file_path, 'a') as sql_file:	# Append mode
			for valid_from, valid_to, value_inc_vat, value_exc_vat in prices:
				# Handle None for value_exc_vat if necessary
				value_exc_vat_str = f"NULL" if value_exc_vat is None else value_exc_vat

				valid_from = valid_from.replace("T", " ").replace("Z", "")
				valid_to = valid_to.replace("T", " ").replace("Z", "")
				# Create the SQL insert statement for the 'rates' table
				insert_statement = (
					f"INSERT INTO rates (valid_from, valid_to, value_inc_vat, value_exc_vat) "
					f"VALUES ('{valid_from}', '{valid_to}', {value_inc_vat}, {value_exc_vat_str}) "
					f"ON DUPLICATE KEY UPDATE "
					f"value_inc_vat = VALUES(value_inc_vat), value_exc_vat = VALUES(value_exc_vat);\n"
				)

				sql_file.write(insert_statement)  # Write to the SQL file

				try:
					cursor.execute(insert_statement)  # Execute the SQL insert
					conn.commit()
					logger.debug(f"[storeData2DB][D03]: insert_statement:{insert_statement}")

				except pymysql.MySQLError as err:
					logger.error(f"[storeData2DB][E01]: <Error executing SQL statement: {err}>")

		# Cleanup old backups
		cleanup_old_backups()

		logger.debug("[storeData2DB][D04]: <Pricing data successfully committed to the database>")

	finally:
		if conn.open:
			conn.close()
		logger.info(f"[storeData2DB][I02]: OUT")



def cleanup_old_backups():

	#  This function is used to remove old sql backup files from the drive
	#  Return: None

	"""
	Removes old backup files, keeping only the most recent ones up to MAX_BACKUP_FILES.
	"""

	logger.info("[cleanup_old_backups][I01]: IN")

	try:
		# List all files in the backup directory with the prefix
		backup_files = [
			f for f in os.listdir(SQL_BACKUP_DIR)
			if f.endswith('__insertQuery.sql')
		]

		# Sort the files by modification time (oldest first)
		backup_files.sort(key=lambda f: os.path.getmtime(os.path.join(SQL_BACKUP_DIR, f)))

		# Remove files if there are more than MAX_BACKUP_FILES
		while len(backup_files) > MAX_BACKUP_FILES:
			oldest_file = backup_files.pop(0)
			os.remove(os.path.join(SQL_BACKUP_DIR, oldest_file))
			logger.debug(f"[cleanup_old_backups][D01]: Removed old backup file: {oldest_file}")

	except Exception as e:
		logger.error(f"[cleanup_old_backups][E01]: <Error during cleanup: {e}>")

	finally:
		logger.info('[cleanup_old_backups][I02]: OUT')



# Main function to control the flow of the program
def main():

	logger.info(f"------>  ")
	logger.info("------>  DataSync Started	  ---")
	logger.info(f"------>  {SYSTEM_NAME} . Version {SYSTEM_VER}	 <------")
	logger.info(f"------>  Last Updated: {datetime.fromtimestamp(os.path.getmtime(__file__))}  <------")
	logger.info(f"------>  ")

	logger.info("[main][I01]: IN")

	parser = argparse.ArgumentParser(description="Get Octopus Energy pricing data.")
	parser.add_argument("-no_email", action="store_true", help="Suppress sending email with the fetched pricing data")
	parser.add_argument("-date", type=str, help="Fetch data for a specific date (YYYY-MM-DD)")

	args = parser.parse_args()


	#
	#  Start of Developer Mode Section
	#

	if DEVELOPER_MODE == 1:
		logger.info(f"------>  ")
		logger.info(f"------>  ~ ~ ~ ~ ~ ~	 D E V E L O P E R	 M O D E   ~ ~ ~ ~ ~ ~ ")
		logger.info(f"------>  ")

		'''
		if args.date == None:
			logger.debug(f"[DEVELOPER]: args.date == None")
		else:
			logger.debug(f"[DEVELOPER]: args.date != None")
		
		if args.date: 
			start_date = datetime.strptime(args.date, "%Y-%m-%d")	# Converting str to datetime 
			end_date = start_date + timedelta(days=1)
			
			logger.debug(f"[DEVELOPER]: start_date:{start_date}; end_date:{end_date};")
		
		else:
			
			# Get the datetime of last record
			lastRecDate = rtnLastDate()
			
			# Check whether current time is after cut-off time or not
			if isCutOff():
				logger.debug(f"[DEVELOPER]: Cutoff = YES")
			else:
				logger.debug(f"[DEVELOPER]: Cutoff = NO")

			if isToday(lastRecDate) == -1:
				
				# Data is seriously out-of-dated
				start_date = lastRecDate
	
				if isCutOff():
					end_date = datetime.now() + timedelta(days=1)
				else:
					end_date = datetime.now()
	
				logger.debug(f"[DEVELOPER]: start_date:{start_date}; end_date:{end_date}; Data is outdated.")
				
				
			elif isToday(lastRecDate) == 0:
				start_date = datetime.now()
				
				if isCutOff():
					logger.debug(f"[DEVELOPER]: start_date:{start_date}; Data is not latest. After cutoff data is not loaded.")
				else:
					logger.debug(f"[DEVELOPER]: start_date:{start_date}; Data is latest.")
	
			elif isToday(lastRecDate) == 1:
				logger.debug(f"[DEVELOPER]: Data is latest.")
	
			else:
				logger.debug(f"[DEVELOPER]: Error.")
		'''
		
		start_date = args.date
		start_date = datetime.strptime(start_date, "%Y-%m-%d")
		prices = getPricingInfo(start_date)
		#logger.debug(f"[DEVELOPER]: prices:{prices}")

		logger.info(f"------>  ")
		logger.info(f"------>  ~ ~ ~ ~ ~ ~	 D E V E L O P E R	 M O D E   E n d e d   ~ ~ ~ ~ ~ ~ ")
		logger.info(f"------>  ")

		exit()

	#
	#  End of Developer Mode Section
	#


	#
	#  Start of this program
	#
	
	
	#  Determine the Start Date in loading data 
	#
	
	if args.date:
		start_date = datetime.strptime(args.date, "%Y-%m-%d")
		end_date = start_date + timedelta(days=1)
		logger.debug(f"[main][D01]: Load Specific Date; start_date:{start_date}; end_date:{end_date}")
		
		# Fetch pricing data from the Octopus API
		prices = getPricingInfo(start_date)	# args.date is used as a flag to show in loading specific date's data
		
	else:
		lastRecDate = rtnLastDate()
		
		if isToday(lastRecDate) == -1:
			start_date = lastRecDate
			end_date = datetime.now()
			
			logger.debug(f"[main][D02]: Data is outdated. lastRecDate:{lastRecDate}; start_date:{start_date}; end_date:{end_date}")
			
			prices = []
			
			while (start_date.date() <= end_date.date()):
				tmpDict = getPricingInfo(start_date)
				prices = prices + tmpDict
				logger.debug(f"[main][D03]: start_date:{start_date}; len(prices):{len(prices)}")
				start_date += timedelta(days=1)
			
		elif isToday(lastRecDate) == 0:
			if isCutOff():
				start_date = datetime.now()
				logger.debug(f"[main][D04]: Latest data is not loaded. lastRecDate:{lastRecDate}; start_date:{start_date}; isCutOff():{isCutOff()}")
				
				prices = getPricingInfo(start_date)	# args.date is used as a flag to show in loading specific date's data
		
			else:
				logger.debug(f"[main][D05]: Data is latest. lastRecDate:{lastRecDate}; isCutOff():{isCutOff()}")
				logger.info("[main][I02]: OUT")
				logger.info("---  DataSync Ended  ---")
				exit()

		elif isToday(lastRecDate) == 1:

			logger.debug(f"[main][D06]: Data is latest. lastRecDate:{lastRecDate}; isCutOff():{isCutOff()}")
			logger.info("[main][I03]: OUT")
			logger.info("---  DataSync Ended  ---")
			exit()
	
	if prices:
		logger.debug(f"[main][D03]: <{len(prices)} records retrieved. Storing to database>")
		
		storeData2DB(prices)

		if not args.no_email:
			logger.debug("[main][D04]: <Sending email report>")
			sendEmail(prices)
			
	else:
		logger.debug("[main][D05]: <No pricing data retrieved. Process will end without data storage or email>")

	logger.info("[main][I02]: OUT")
	logger.info("---  DataSync Ended  ---")



if __name__ == "__main__":
	main()




##################################
##	Obsoleted Functions Section ##
##################################
'''


Algoritm:


determine SD and ED

if lrd < today:
	sd = lrd

	if afterCutoff:
		ed = today + 1
	else:
		ed = today

else lrd = today:
	if beforeCutOff:
		skip
	elif afterCutOff:
		sd = today
		ed = today + 1




'''
