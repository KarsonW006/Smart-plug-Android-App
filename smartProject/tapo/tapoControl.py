'''
	Program: tapoControl.py  [aka smartPlug_v13.py]

	Objective:
		- Control your Tapo smart plug
			- trigger actions
			- retrieve device information such as status and settings.
			- update backend database


	 usage: tapoControl.py [-h] [-userid USERID] [-ip IP] -operation {ON,OFF,AUTO,F_ON,F_OFF,TEST} [-schedule SCHEDULE]
			
			Control your Tapo smart plug: trigger actions and retrieve device information such as status and settings.
			
			optional arguments:
			-h, --help			  show this help message and exit
			-userid USERID		  The user tapo ID
			-ip IP				  The IP address of device
			-operation {ON,OFF,AUTO,F_ON,F_OFF,TEST}
								  The mode of operation (e.g., ON, OFF).
			-schedule SCHEDULE	  Accepting schedule ID of the caller's process.



	Dependency:
		pip install pymysql
		pip install tapo
		pip install pytz (if no apschedule, sqlalchemy installed)




	Version: 20241230_v002 [Released]

	Changelog:
		- 20240921_v001		--> Initial Version. Trigger smart plug on/off and get device status
		- 20240925_v003		--> [Add] Allow user to enquiry the status without trigger action [GET]
		- 20240927_v001		--> [Update] Bug fixed
		- 20240928_v003		--> [Add] Change to use generic_device method
		- 20240929_v001		--> [Update] Added Tapo Smart Bulb support
		- 20240930_v007		--> [Add] Added Logs support
		- 20241015_v013		--> [Update] Bug Fixed.	 Log error level issue
		- 20241016_v001		--> [Add] Allow suppresing Log messages
		- 20241018_v013		--> [Change] Changed embedded queries fields name
		- 20241018_v017		--> [Update] Bug fixed
		- 20241022_v002		--> [Add] Added send notification [thro email] feature
		- 20241024_v001		--> [Amend] Obsoleted field 'tid'
		- 20241025_v001		--> [Add] Accepting Schedule_ID --> deal with checking device price threshold matter
		- 20241028_v001		--> [Add] UPDATEALL --> allow update all devices status in single execution
		- 20241110_v001		--> [Change] Fixing unstable database server issue (Connection V2)
		- 20241114_v001		--> [Change] Changed LOG method
		- 20241130_v001		--> [Change] Add Debug logging
		- 20241220_v001		--> [Add] Add support to client's requested Energy Saving Requirements [after 2nd iteration]
		- 20241224_v001		--> [Change] Structural Changes.
		- 20241225_V001			[Change] Enhanced email notification type in supporting schedule action fails
		- 20241225_V002		--> Initial Version 2.	Project directory structural revamp
		- 20241230_v001		--> [Change] Remove UPDATEALL
		- 20241230_v002		--> [Change] Standardize program name: smartPlug.py --> tapoControl.py

	Remark:
		For Deployment:
			1. Update Version number
			2. Set the Indicator from '[Developing]' to '[Released]'
			3. Ensure ChangeLog is correct
			4. Copy from Sandbox to Production by eliminating '_vX' suffix

	Functions:
		def connect_with_retry():
		def isOverThreshold(schedule_id):
		def isDeviceRegistered(userid, ip):
		def isNotify(userid):
		async def sendNotification(userid, ip, pin, messageID):
		def getTapoPIN(userid):
		async def rtnDetails(userid, ip, pin, retries=3, base_delay=1, max_delay=1):
		async def turnON(userid, ip, pin):
		async def turnOFF(userid, ip, pin):
		def updateDevice(device_on, nickname, type, userid, ip):
		async def main(argUserid, argIP, argOperation, argScheduleID):


'''

import asyncio	# Import the asyncio module
import os
import sys
import pymysql
from datetime import datetime, timedelta
import pytz
import logging
from logging.handlers import TimedRotatingFileHandler
import argparse
from tapo import ApiClient
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import time
from random import uniform		# randomize timer

# Define constants
SLEEP_DURATION = 60	 # Time to sleep in seconds
SLEEP_SHORT = 1	# Time to sleep in seconds
MAX_RETRIES = 5	 # Maximum number of retries for database connection
RETRY_DELAY = 5	 # Delay in seconds between retries

SYSTEM_NAME = 'smartPlug [Series.2][TAPO]'
SYSTEM_VER = '20241230_v002'
DEVELOPER_MODE = 0			#  Developer mode: ON (1) | OFF (0)
ENVIRONMENT = "Sandbox" if "Sandbox" in os.path.abspath(os.path.dirname(__file__)) else "Production"


# Email configuration
SMTP_SERVER = 'smtp.gmail.com'	# Gmail SMTP server
SMTP_PORT = 465					 # Port for SSL
EMAIL_USER = 'your-email@example.com'	 # Your email
EMAIL_PASSWORD = 'MASKED_PASSWORD'	# Your app password
RECIPIENT_EMAIL = 'your-email@example.com'  # Recipient email


# Set log level: use logger.info for production and logger.debug for development
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
	"./Sandbox/smartProject/.logs/tapoControl.log" if ENVIRONMENT == 'Sandbox' else "./Production/smartProject/.logs/tapoControl.log",
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

####################################################################################################################



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



# Completed
def isOverThreshold(schedule_id):

	#  Check for threshold restriction of schedule
	#  Return: Ture / False
	
	logger.info("[isOverThreshold][I01]:IN;")
	logger.debug(f"[isOverThreshold][D01]: schedule_id:{schedule_id};")
	
	try:
		conn = connect_with_retry()
		cursor = conn.cursor()
		
		# Find Current Enengy Price
		#
		cursor.execute("SELECT value_inc_vat FROM rates WHERE valid_from <= CURTIME() AND valid_to > CURTIME()")
		result = cursor.fetchone()
		
		logger.debug("[isOverThreshold][D02]: SQL:SELECT value_inc_vat FROM rates WHERE valid_from <= CURTIME() AND valid_to > CURTIME();")
		logger.debug(f"[isOverThreshold][D03]: result:{result};")

		if result:
			currentPrice = result[0]
		else:
			currentPrice = -999


		# Find the Threshold value Defined in the Schedule
		#
		cursor.execute(f"select threshold from schedules where schedule_id = {schedule_id}")		
		result = cursor.fetchone()
		
		logger.debug(f"[isOverThreshold][D04]: SQL:select threshold from schedules where schedule_id = {schedule_id};")
		logger.debug(f"[isOverThreshold][D05]: result:{result};")

		if result:
			deviceThreshold = result[0]
		else:
			deviceThreshold = 999


		logger.debug(f"[isOverThreshold][D06]: currentPrice:{currentPrice}; deviceThreshold:{deviceThreshold};")

		
		# Compare the Current Price against Schedule's Threshold
		#
		if currentPrice > deviceThreshold:
			logger.debug(f"[isOverThreshold][D07]:OUT; <Price > Threshold:True>;")
			logger.info("[isOverThreshold][I02]: <OUT:True>")
			return True
		else:
			logger.debug(f"[isOverThreshold][D08]:OUT; <Price < Threshold:False>;")
			logger.info("[isOverThreshold][I03]: <OUT:False>")
			return False

	finally:
		
		# Disconnect from database
		if conn:
			conn.close()
			logger.debug("[isOverThreshold][D09]: <Database Disconnected>")



# Completed
def isDeviceRegistered(userid, ip):

	# Check whether user owns this device
	# Return: True / False

	logger.info(f"[isDeviceRegistered][I01]:IN;")
	logger.debug(f"[isDeviceRegistered][D01]: userid:{userid}; ip:{ip};")

	try:
		conn = connect_with_retry()
		cursor = conn.cursor()

		varSQL = "select count(*) from userDevices where userid = %s and ip = %s"
		params = (userid, ip)

		logger.debug(f"[isDeviceRegistered][D02]: sql:{varSQL}; params:{params}")

		cursor.execute(varSQL, params)
		result = cursor.fetchone()

		logger.debug(f"[isDeviceRegistered][D03]: result:{result};")

		if conn:
			conn.close()
			logger.debug("[isDeviceRegistered][D04]: Database:Disconnected")

		if result[0] == 0:
			logger.debug(f"[isDeviceRegistered][D05]: result[0]:{result[0]}(False)")	# Log the executed	statement
			return(False)
		else:
			logger.debug(f"[isDeviceRegistered][D06]: result[0]:{result[0]}(True)")	 # Log the executed
			return(True)

	except Exception as e:
		logger.error(f"[isDeviceRegistered][E01]: <Error executing SQL statement: {e}>")
	finally:
		logger.info("[isDeviceRegistered][I02]: OUT")



def isNotify(userid):
	
	#  Check whether user is accepting system notification
	#  Return: True / False

	logger.info("[isNotify][I01]:IN")
	logger.debug(f"[isNotify][D01]: userid:{userid}")
	
	conn = None
	
	try:
		conn = connect_with_retry()
		cursor = conn.cursor()
		
		SQL = (f"select notify from userProfiles where userid = '{userid}'")
		cursor.execute(SQL)
		result = cursor.fetchone()
		
		logger.debug(f"[sendNotification][D02]: SQL:{SQL}")
		logger.debug(f"[sendNotification][D03]: result:{result}")
	
	finally:
		if conn:
			conn.close()
			logger.debug("[sendNotification][D04]: Database:Disconnected")
	
	logger.debug(f"[isNotify][D05]: result[0]:{result[0]}")		
	logger.info("[isNotify][I02]: OUT")
	return True if result[0] == 'Y' else False
		
		
		
async def sendNotification(userid, ip, pin, messageID):
	
	#  This function is used to prepare and send the email content based on the operation result.
	#  Return: None
	
	
	logger.info("[sendNotification][I01]:IN")
	logger.debug(f"[sendNotification][D01]: userid:{userid}; ip:{ip}; pin:{pin}; messageid:{messageID}")

	STATEMENTS = {
		1: "Turned on according to the schedule.",
		2: "Turned on manually via a trigger.",
		3: "Turned on again due to being below the threshold.",
		4: "Turned on via CLI command.",
		5: "Turned off according to the schedule.",
		6: "Turned off manually via a trigger.",
		7: "Turned off due to exceeding the threshold.",
		8: "Turned off via CLI command.",
		9: "Schedule skipped due to exceeding the threshold.",
		10: "Device encountered an issue. The scheduled action could not be initiated successfully. Please inspect the device to address the problem.",
		11: "The device is already powered off. The scheduled action was skipped, and the schedule concluded successfully.",
		12: "The device is already powered on. The scheduled action was skipped, and the schedule concluded successfully."
	}

	if isNotify(userid):
		
		#  Get Device Details
		result = await rtnDetails(userid, ip, pin)
		
		# User declares to receive notification
		
		devStatus = 'ON' if result.get('device_on') else 'OFF'
		devType = 'Bulb' if result.get('type') == 'SMART.TAPOBULB' else 'Plug'
		
		logger.debug(f"[sendNotification][D02]: devStatus:{devStatus}; devType:{devType}")

		formatted_time = datetime.now(pytz.timezone('Europe/London')).strftime('%Y-%m-%d %H:%M:%S%z')
		formatted_time = formatted_time[:-2] + ':' + formatted_time[-2:]

		msg = MIMEMultipart()
		msg['From'] = EMAIL_USER
		msg['To'] = userid
		msg['Subject'] = (f"{result.get('nickname')} [{devType}] {STATEMENTS[messageID]} at " f"{formatted_time}")

		body = f"Device: {result.get('nickname')} [{devType}]\n"
		body += f"Current Status: {devStatus}\n"

		body += f"Remark: {STATEMENTS[messageID]}\n"

		body += "Time: " f"{formatted_time}"
		msg.attach(MIMEText(body, 'plain'))

		logger.debug(f"[sendNotification][D03]: Body: \n{body}")

		try:
			with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
				server.login(EMAIL_USER, EMAIL_PASSWORD)
				server.send_message(msg)
				logger.info(f"[sendNotification][I02]: <Notification sent to {userid}.>")
		except Exception as e:
			logger.error(f"[sendNotification][E01]: Failed to send notification: {e}")
		logger.debug("[sendNotification][D04]: <OUT with email_sent>")
	else:
		logger.debug("[sendNotification][D05]: <OUT without email_sent>")
		return



# Completed
def getTapoPIN(userid):
	logger.info("[getTapoPIN][I01]:IN;")
	logger.debug(f"[getTapoPIN][D01] userid:{userid};")
	
	conn = None	 # Initialize conn variable
	
	try:
		conn = connect_with_retry()
		cursor = conn.cursor()
		
		try:
			varSQL = f"select tpin from userProfiles where userid = '{userid}'"
			cursor.execute(varSQL)
		except Exception as e:
			logger.error(f"[getTapoPIN][E01]: <Error executing SQL statement: {e}>")
		
		result = cursor.fetchone()
		
		logger.debug(f"[getTapoPIN][D02]: varSQL:{varSQL};")						  
		logger.debug(f"[getTapoPIN][D03]: result[0]:{str(result[0])};")
	
	except Exception as e:
		logger.error(f"[getTapoPIN][E02]: <Error: {e}>")
	
	finally:
		if conn and conn.open:	# Check if conn exists and is open
			conn.close()
			logger.debug("[getTapoPIN][D04]: <Database disconnected>")
		
		logger.debug(f"[getTapoPIN][D05]: <result[0]:{result[0]}>;")
		logger.info("[getTapoPIN][I02]:OUT")
		return result[0]  # Directly return result[0]



# Completed
async def rtnDetails(userid, ip, pin, retries=3, base_delay=1, max_delay=1):
	
	# This function is used to get selective attributes of the smart device
	# Return: dict
	
	logger.info("[rtnDetails][I01]: IN")
	logger.debug(f"[rtnDetails][D01]: userid:{userid}; ip:{ip}; pin:{pin}")
	
	attempt = 0
	
	while attempt <= retries:
		try:
			client = ApiClient(userid, pin)
			device = await client.generic_device(ip)
			device_info = await device.get_device_info()
			device_info_dict = device_info.to_dict()
			
			result = {
				"nickname": device_info_dict.get("nickname"),
				"device_on": device_info_dict.get("device_on"),
				"type": device_info_dict.get("type")
			}
			
			logger.debug(f"[rtnDetails][D02]: result:{result}")
			logger.info("[rtnDetails][I02]: OUT")
			return result
			
		except Exception as e:
			attempt += 1
			logger.error(f"[rtnDetails][E01]: Attempt {attempt} failed with error: {e}")
			
			if attempt > retries:
				logger.error(f"[rtnDetails][E02]: All retries exhausted.")
				break
			
			# Implement exponential backoff with jitter
			delay = min(base_delay * (2 ** (attempt - 1)) + uniform(0, 1), max_delay)
			logger.debug(f"[rtnDetails][D03]: Retrying in {delay:.2f} seconds...")
			await asyncio.sleep(delay)
		
	# Return a default value if an exception occurs
	return {"nickname": None, "device_on": False, "type": None}
	
	

# Completed
async def turnON(userid, ip, pin):
	
	#  This function is used to turn on a smart device
	#  Return: Success / Fail
	
	logger.info("[turnON][I01]:IN;")
	logger.debug(f"[turnON][D01]: userid:{userid}; ip:{ip};")
	
	try:
		#  Build connection to the smart device
		client = ApiClient(userid, pin)
		device = await client.generic_device(ip)
		
		#  Get all attributes from smart device
		#
		device_info = await device.get_device_info()
		device_info_dict = device_info.to_dict()
		
		#  Get Before Status
		#
		beforeStatus = True if device_info_dict.get("device_on") == 1 else	False
		
		logger.debug(f"[turnON][D02]: beforeStatus:{beforeStatus}")
		
		if not beforeStatus:
		
			#  Power On device
			#
			await device.on()
		
			#  Get After Status
			#
			device_info = await device.get_device_info()
			device_info_dict = device_info.to_dict()
			afterStatus = True if device_info_dict.get("device_on") == 1 else False
			
			logger.debug(f"[turnON][D03]: afterStatus:{afterStatus}")
		
			if afterStatus == True:
				logger.debug("[turnON][D04]: <Return Success with action done>")
				logger.info("[turnON][I02]:OUT")
				return 'Success'
			else:
				logger.debug("[turnON][D05]: <Return Fail with action done>")
				logger.info("[turnON][I03]:OUT;")
				return 'Fail'
		else:
			logger.debug("[turnON][D06]: <Return Success. Already ON>")
			logger.info("[turnON][I04]:OUT;")
			return 'Success'
	except Exception as e:
		# Handle exceptions and log the error
		logger.error(f"[turnON][E01]: Exception occurred: {e}")
		logger.info("[turnON][I05]:OUT;")
		return 'Fail'


# Completed
async def turnOFF(userid, ip, pin):
	
	#  This function is used to turn off a smart device
	#  Return: Success / Fail
	
	logger.info("[turnOFF][I01]:IN;")
	logger.debug(f"[turnOFF][D01]: userid:{userid}; ip:{ip};")
	
	try:
		#  Build connection to the smart device
		client = ApiClient(userid, pin)
		device = await client.generic_device(ip)
		
		#  Get all attributes from smart device
		#
		device_info = await device.get_device_info()
		device_info_dict = device_info.to_dict()
		
		#  Get Before Status
		#
		beforeStatus = True if device_info_dict.get("device_on") == 1 else	False
		
		logger.debug(f"[turnOFF][D02]: beforeStatus:{beforeStatus}")
		
		if beforeStatus:
		
			#  Power On device
			#
			await device.off()
		
			#  Get After Status
			#
			device_info = await device.get_device_info()
			device_info_dict = device_info.to_dict()
			afterStatus = True if device_info_dict.get("device_on") == 1 else False
			
			logger.debug(f"[turnOFF][D03]: afterStatus:{afterStatus}")
			
			if afterStatus == False:
				logger.debug("[turnOFF][D04]: <Return Success with action done>")
				logger.info("[turnOFF][I02]:OUT;")
				return 'Success'
			else:
				logger.debug("[turnOFF][D05]: <Return Fail with action done>")
				logger.info("[turnOFF][I03]:OUT;")
				return 'Fail'
		else:	
			logger.debug("[turnOFF][D06]: <Return Success. Already OFF>")
			logger.info("[turnOFF][I04]:OUT;")
			return 'Success'
	except Exception as e:
		# Handle exceptions and log the error
		logger.error(f"[turnOFF][E01]: Exception occurred: {e}")
		logger.info("[turnOFF][I05]:OUT;")
		return 'Fail'

# Completed 
def updateDevice(device_on, nickname, type, userid, ip):
	
	# This function is updating device details
	
	logger.info("[updateDevice][I01]: IN")
	logger.debug(f"[updateDevice][D01]: device_on:{device_on}; nickname:{nickname}; type:{type}; userid:{userid}; ip:{ip}")
	
	try:
		conn = connect_with_retry()
		cursor = conn.cursor()
		
		if nickname == None:
			logger.warning(f"[updateDevice][W01]: device_on:{device_on}; nickname:{nickname}; type:{type}; userid:{userid}; ip:{ip}; <Invalid Device Information>")
			varSQL = ("UPDATE YOUR_DATABASE_NAME.userDevices "
				"SET device_on = %s "
				"WHERE userid = %s AND ip = %s")
			cursor.execute(varSQL, (device_on, userid, ip))
		
		else:
			varSQL = ("UPDATE YOUR_DATABASE_NAME.userDevices "
				"SET device_on = %s, nickname = %s, type = %s "
				"WHERE userid = %s AND ip = %s")
			cursor.execute(varSQL, (device_on, nickname, type, userid, ip))
		
		
		# Execute the parameterized query
		cursor.execute(varSQL, (device_on, nickname, type, userid, ip))
		conn.commit()
		logger.debug(f"[updateDevice][D02]: varSQL:{varSQL}; device_on:{device_on}; nickname:{nickname}; type:{type}; userid:{userid}; ip:{ip}")

	except Exception as e:
		logger.error(f"[updateDevice][E01] Error executing SQL statement: {e}")

	finally:
		if conn:
			conn.close()
		logger.info("[updateDevice][I02]:OUT")



async def main(argUserid, argIP, argOperation, argScheduleID):

	# Set up logging based on the quiet flag
	
	logger.info(F"------>")
	logger.info("------>  smartPlug Started	 <------")
	logger.info(f"------>  {SYSTEM_NAME} . Version {SYSTEM_VER}	 <------")
	logger.info(f"------>  Last Updated: {datetime.fromtimestamp(os.path.getmtime(__file__))}  <------")
	logger.info(F"------>")

	logger.info("[main][I01]: IN")


	if DEVELOPER_MODE == 1:
		logger.info(f"------>  ")
		logger.info(f"------>  ~ ~ ~ ~ ~ ~	 D E V E L O P E R	 M O D E   ~ ~ ~ ~ ~ ~ ")
		logger.info(f"------>  ")
		
		schedule_id = 13
		userid = 'your-email@example.com'
		ip = '192.168.1.X'
		pin = getTapoPIN(userid)
		
		device_on = 1
		nickname = 'TestDevice'
		type = 'TestType'
		
		logger.info(f"[DEVELOPER_MODE]: sendNotification:{await sendNotification(userid, ip, pin, 1)}")
		
		logger.info(f"------>  ")
		logger.info(f"------>  ~ ~ ~ ~ ~ ~	 D E V E L O P E R	 M O D E   E n d e d   ~ ~ ~ ~ ~ ~ ")
		logger.info(f"------>  ")
		
		exit()
		

	logger.debug(f"[Main][D01]: argUserid:{argUserid}; argIP:{argIP}; argOperation:{argOperation}; argScheduleID:{argScheduleID}")	# Log the executed


	# Update the status of all Devices Registered
	
	if argOperation.upper() == 'TEST':

		logger.debug("[main][D02]: <TEST>")
		
		userid = 'your-email@example.com'
		pin = 'YOUR_TAPO_PIN'
		ip = '192.168.1.X'
		
		result = await rtnDetails(userid, ip, pin)
		
		#print(result.get('nickname'))
		
		print(result.get('nickname'), result.get('device_on'), result.get('type'))
		#await turnON(userid, ip)
		#time.sleep(3)
		#await turnOFF(userid, ip)
		print(getTapoPIN('your-email@example.com'))
		beforeStatus = 'ON' if result.get("device_on") == 1 else 'OFF'
		
		print(f"result.get(\"device_on\"):{result.get('device_on')}; beforeStatus:{beforeStatus}")

	elif isDeviceRegistered(argUserid, argIP):
		
		logger.debug("[Main][D04]: Operation: <NOT UPDATEALL>")
		
		#  Get user TAPO PIN
		pin = getTapoPIN(argUserid)

		# ON + No Schedule --> CLI
		# F_ON --> Forcing ON
		if (argOperation.upper() == 'ON' and argScheduleID is None) or argOperation == 'F_ON':
			
			#  On by CLI or Forcing On from Apps
			#
			beforeResult = await rtnDetails(argUserid, argIP, pin)
			
			
			if not beforeResult.get('device_on'):

				# On without other affecting factors
				response = await turnON(argUserid, argIP, pin)
				
				# Get Device Status
				afterResult = await rtnDetails(argUserid, argIP, pin)

				if response == 'Success':
					# Update device Status to database
					updateDevice(afterResult.get('device_on'), afterResult.get('nickname'), afterResult.get('type'), argUserid, argIP)
					logger.debug(f"[main][D04]: <Operation {argOperation} Success.	Device ON + Updated>")
				else:
					logger.debug(f"[main][D05]: <Operation {argOperation} failed.  Device can't turn on.	 Current status = {afterResult.get('device_on')}>")
				
				#  Sending Notification to user
				if argOperation.upper() == 'ON':
					# Called from CLI
					print(f"\tCLI Prompt: TAPO [{afterResult.get('nickname')}|{argIP}] is {afterResult.get('device_on')}")	
					await sendNotification(argUserid, argIP, pin, 4)
					
				elif argOperation.upper() == 'F_ON':
					# Called from Scheduler F_ON
					# Schedule ID will not be care
					await sendNotification(argUserid, argIP, pin, 2)
					
				elif response == 'Fail':
					await sendNotification(argUserid, argIP, pin, 10)
			else:
				#  Device is already ON .. Skip Operation
				await sendNotification(argUserid, argIP, pin, 12)
				
		# ON + Schedule --> Scheduler call
		elif argOperation.upper() == 'ON' and argScheduleID is not None:
			
			# On by Schedule Trigger 
			# - General Schedule call
			#
			
			beforeResult = await rtnDetails(argUserid, argIP, pin)
			print(f"--------->	beforeResult.get('device_on'):{beforeResult.get('device_on')}:{type(beforeResult.get('device_on'))}")
			if not beforeResult.get('device_on'):

				# Checking Threshold 
				if isOverThreshold(argScheduleID):
					
					# High Price  --> Skip ON Trigger 
					# Sending notification to user
					await sendNotification(argUserid, argIP, pin, 9)

				else:
					# Low Price	 --> Trigger ON
					
					# On without other affecting factors
					response = await turnON(argUserid, argIP, pin)
					
					# Get Device Status
					afterResult = await rtnDetails(argUserid, argIP, pin)
						
					if response == 'Success':
						# Update device Status to database
						updateDevice(afterResult.get('device_on'), afterResult.get('nickname'), afterResult.get('type'), argUserid, argIP)
						logger.debug(f"[main][D06]: <Operation {argOperation} Success.	Device ON + Updated>")
						
						# Sending notification to user
						await sendNotification(argUserid, argIP, pin, 1)
						
					else:
						await sendNotification(argUserid, argIP, pin, 10)
						logger.debug(f"[main][D07]: <Operation {argOperation} failed.  Device can't turn on.	 Current status = {afterResult.get('device_on')}>")
			else:
				#  Device is already ON .. Skip Operation
				await sendNotification(argUserid, argIP, pin, 12)
				
				
		# AUTO --> Call from Scheduler with Threshold Factors During Schedule
		elif argOperation.upper() == 'AUTO':
			
			# Auto
			
			# Check Current Status
			# Get Device Status
			beforeResult = await rtnDetails(argUserid, argIP, pin)
			
			# Checking whether over Threshold
			#beforeStatus = True if result.get('device_on') == 1 else False
			threshold = isOverThreshold(argScheduleID)
			
			if (beforeResult.get('device_on'), threshold) == (True, True):
				
				logger.debug("[Main][D08]: <Current Price > Threshold: ON --> OFF>")
				
				#  Turn Off: Current Price > Threshold: ON --> OFF
				response = await turnOFF(argUserid, argIP, pin)
				
				# Get Device Status
				afterResult = await rtnDetails(argUserid, argIP, pin) 
				
				#	Update Status to database
				if response == 'Success':
					# Update device Status to database
					updateDevice(afterResult.get('device_on'), afterResult.get('nickname'), afterResult.get('type'), argUserid, argIP)
					logger.debug(f"[main][D09]: <Operation {argOperation} Success.	Device ON + Updated>")
					
					#  Sending Notification to user
					await sendNotification(argUserid, argIP, pin, 7)
					
				else:
					await sendNotification(argUserid, argIP, pin, 10)
					logger.debug(f"[main][D10]: <Operation {argOperation} failed.  Device can't turn off.	 Current status = {afterResult.get('device_on')}>")
			
			elif (beforeResult.get('device_on'), threshold) == (True, False):
				# Skip : Current Price < Threshold: ON --> ON
				logger.debug("[Main][D11]: <Current Price < Threshold: ON --> ON>")
				
			elif (beforeResult.get('device_on'), threshold) == (False, True):
				# Skip : Current Price > Threshold: OFF --> OFF
				logger.debug("[Main][D12]: <Current Price > Threshold: OFF --> OFF>")
				
			elif (beforeResult.get('device_on'), threshold) == (False, False):
				# Turn On: Current Price < Threshold: OFF -->  ON
				logger.debug("[Main][D13]: <Price < Threshold: OFF -->	ON>")
			
				response = await turnON(argUserid, argIP, pin)
				
				# Get Device Status
				afterResult = await rtnDetails(argUserid, argIP, pin) 
				
				if response == 'Success':
					# Update device Status to database
					updateDevice(afterResult.get('device_on'), afterResult.get('nickname'), afterResult.get('type'), argUserid, argIP)
					logger.debug(f"[main][D14]: <Operation {argOperation} Success.	Device ON + Updated>")
				
					# Sending notification to user
					await sendNotification(argUserid, argIP, pin, 3)
				
				else:
					await sendNotification(argUserid, argIP, pin, 10)
					logger.debug(f"[main][D15]: <Operation {argOperation} failed.  Device can't turn on.	 Current status = {afterResult.get('device_on')}>")
			
		# OFF / F_OFF --> Call by CLI and Scheduler
			# OFF + No Schedule ID --> CLI calls
			# OFF + Schedule ID --> Scheduler calls
			# F_OFF --> Forcing OFF
		elif argOperation.upper() == 'OFF' or argOperation.upper() == 'F_OFF':
			
			#  OFF by CLI or Forcing On from Apps
			#

			# Get Before Device Status
			result = await rtnDetails(argUserid, argIP, pin)
			beforeStatus = True if result.get('device_on') == 1 else False
			
			if beforeStatus:
				
				# Device is ON
				# On without other affecting factors
				response = await turnOFF(argUserid, argIP, pin)
				
				# Get Device Status
				result = await rtnDetails(argUserid, argIP, pin)
				
				logger.debug(f"[main][D16]: response:{response}")
				
				if response == 'Success':
					# Update device Status to database
					updateDevice(result.get('device_on'), result.get('nickname'), result.get('type'), argUserid, argIP)
					logger.debug(f"[main][D17]: <Operation {argOperation} Success. Device OFF + Updated>")
					
					if argOperation.upper() == 'OFF':
					
						if argScheduleID is None:
							# Called from CLI
							print(f"\tCLI Prompt: TAPO [{result.get('nickname')}|{argIP}] is {result.get('device_on')}")	
							await sendNotification(argUserid, argIP, pin, 8)
							logger.debug("[main][D18]: <Turned off device by CLI command>")
						else:
							# Called from Scheduler
							await sendNotification(argUserid, argIP, pin, 5)
							logger.debug("[main][D19]: <Turned off device by scheduler")
							
					elif argOperation.upper() == 'F_OFF':
						# Called from Scheduler F_OFF
						# Schedule ID will not be care
						await sendNotification(argUserid, argIP, pin, 6)
						logger.debug("[main][D20]: Turned by device by Schedular Forcing-Off")
						
				else:
					await sendNotification(argUserid, argIP, pin, 10)
					logger.debug(f"[main][D21]: <Operation {argOperation} failed.  Device can't turn off.	 Current status = {result.get('device_on')}>")
			
			else:
				await sendNotification(argUserid, argIP, pin, 11)
				logger.debug(f"[main][D22]: <Device is currently OFF.  Operation Skipped>")
				
	else:
		logger.debug(f"[main][D23]: <Device({argIP}) is not belonging to user ({argUserid})>")
		
	logger.info("[main][I01]:OUT")
	logger.info("---   smartPlug Ended	 ---")



if __name__ == "__main__":
	parser = argparse.ArgumentParser(description='Control your Tapo smart plug: trigger actions and retrieve device information such as status and settings.')
	parser.add_argument('-userid', type=str, help='The user tapo ID')
	parser.add_argument('-ip', type=str, help='The IP address of device')
	parser.add_argument(
		'-operation',
		type=str.upper,
		required=True,
		choices=['ON', 'OFF', 'AUTO', 'F_ON', 'F_OFF', 'TEST'],	 # Specify the allowed operations
		help='The mode of operation (e.g., ON, OFF).'  # AUTO, F_ON, F_OFF - a hidden subfunction of ON which toggling with threshold
	)
	parser.add_argument('-schedule', type=str, help='Accepting schedule ID of the caller\'s process.')
	args = parser.parse_args()

	# Custom validation logic for conditional arguments
	if args.operation != 'TEST':
		# For operations other than TEST, -userid and -ip are required
		if not args.userid:
			print("Error: -userid is required for this operation.", file=sys.stderr)
			sys.exit(1)
		if not args.ip:
			print("Error: -ip is required for this operation.", file=sys.stderr)
			sys.exit(1)
	# If UPDATEALL, -userid and -ip are optional; no further checks needed


	asyncio.run(main(args.userid, args.ip, args.operation, args.schedule))


