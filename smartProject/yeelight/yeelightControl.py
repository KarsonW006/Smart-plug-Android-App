'''

Objective:
		- Control your Yeelight smart lights
			- trigger actions
			- retrieve device information such as status and settings.
			- update backend database


	usage: yeelightControl.py [-h] --userid USERID --ip IP --operation {ON,OFF,TEST} 
		   optional arguments:
				-h, --help			  show this help message and exit
				--userid USERID		  The user tapo ID
				--ip IP				  The IP address of device
				--operation {ON,OFF,TEST}
									  The mode of operation (e.g., ON, OFF, TEST).
				--schedule SCHEDULE	  Accepting schedule ID of the caller's process.
				--quiet				  Suppress logging output


	Dependency:
		pip install yeelight
		pip install pymysql
		pip install pytz


	Version: 20241230_v001 [Released]


	Changelog:
		- 20241224_v001		--> Initial Version. Trigger smart plug on/off and get device status
		- 20241225_v002		--> Initial Version 2.  Project directory structural revamp
		- 20241230_v001		--> [Change] Remove UpdateAll feature


	Functions List:
		def connect_with_retry():
		def isDeviceRegistered(userid, ip):
		def isOverThreshold(schedule_id):
		def YL_setName(ip):
		def YL_rtnDetails(ip, retries=3, base_delay=1, max_delay=1):
		def turnON(ip):
		def turnOFF(ip):
		def updateDevice(device_on, nickname, type, userid, ip):
		def isNotify(userid):
		def sendNotification(userid, ip, messageID):
		def main(argUserid, argIP, argOperation, argScheduleID):


	Remark:
		For Deployment:
			1. Update Version number
			2. Set the Indicator from '[Developing]' to '[Released]'
			3. Ensure ChangeLog is correct
			4. Copy from Sandbox to Production by eliminating '_vX' suffix

'''

import pymysql
import sys
from yeelight import Bulb, BulbException
import logging
from logging.handlers import TimedRotatingFileHandler
import argparse
import time
from datetime import datetime, timedelta
import pytz
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os


# Define constants
SLEEP_DURATION = 60	 # Time to sleep in seconds
SLEEP_SHORT = 1	# Time to sleep in seconds
MAX_RETRIES = 5	 # Maximum number of retries for database connection
RETRY_DELAY = 5	 # Delay in seconds between retries

SYSTEM_NAME = 'yeelightControl [Series.2][Yeelight]'
SYSTEM_VER = '20241230_v001'
DEVELOPER_MODE = 0			#  Developer mode: ON (1) | OFF (0)
ENVIRONMENT = "Sandbox" if "Sandbox" in os.path.abspath(os.path.dirname(__file__)) else "Production"
    

# Set log level: use logging.INFO for production and logging.DEBUG for development
LOG_LEVEL = logging.DEBUG  if "Sandbox" in os.path.abspath(os.path.dirname(__file__)) else logging.INFO 

# Email configuration
SMTP_SERVER = 'smtp.gmail.com'	# Gmail SMTP server
SMTP_PORT = 465					 # Port for SSL
EMAIL_USER = 'your-email@example.com'	 # Your email
EMAIL_PASSWORD = 'MASKED_PASSWORD'	# Your app password
RECIPIENT_EMAIL = 'your-email@example.com'  # Recipient email


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
	"./Sandbox/smartProject/.logs/yeelightControl.log" if ENVIRONMENT == 'Sandbox' else "./Production/smartProject/.logs/yeelightControl.log",
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
	raise Exception("[connect_with_retry]: <Failed to connect to the database after several attempts.>")

	logger.info("[connect_with_retry][I02]: OUT")


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
def YL_setName(ip):

	# Set the name of a device
	# Return: Success | Fail

	logger.info("[YL_setName][I01]:IN;")
	logger.debug(f"[YL_setName][D01]: ip:{ip};")

	try:
		bulb = Bulb(ip)
		last_segment = ip.split('.')[-1]

		properties = bulb.get_properties()
		beforeName = properties.get("name", "unknown")

		bulb.set_name(f'Yeelight_{last_segment}')
		properties = bulb.get_properties()
		afterName = properties.get("name", "unknown")

		logger.debug(f"[YL_setName][D02]: beforeName:{beforeName}; afterName:{afterName};")
		
		if (beforeName != afterName) and (afterName == f'Yeelight_{last_segment}'):
			return 'Success'
		else:
			return 'Fail'
			
	except BulbException as e:
		logger.debug(f"[YL_setName][E01]: An error occurred while communicating with the Yeelight device: {e}")
		
	except Exception as e:
		logger.debug(f"[YL_setName][E02]: Unexpected error: {e}")
		
	finally:
		logger.info("[YL_setName][I02]: OUT;")


#  Completed
def YL_rtnDetails(ip, retries=3, base_delay=1, max_delay=1):
	
	#  This function is used to retrieve smart device attributes by using API call
	#  Return: DICT (nickname, device_on, type)
	
	logger.info("[YL_rtnDetails][I01]:IN;")
	logger.debug(f"[YL_rtnDetails][D01]: ip:{ip};")
	
	attempt = 0
	
	while attempt <= retries:
		try:
			bulb = Bulb(ip)
			properties = bulb.get_properties()
			
			nickname = properties.get("name", "unknown")
			device_on = 1 if properties.get("power", "unknown") == 'on' else 0
			
			result = {
					"nickname": nickname,
					"device_on": device_on,
					"type": 'YEELIGHT.LIGHT'
				}
				
			logger.debug(f"[YL_rtnDetails][D02]: result:{result}")
			logger.info("[YL_rtnDetails][I02]: OUT")
			return result
		
		except Exception as e:
			attempt += 1
			logger.error(f"[YL_rtnDetails][E01]: Attempt {attempt} failed with error: {e}")
			
			if attempt > retries:
				logger.error(f"[YL_rtnDetails][E02]: All retries exhausted.")
				break
			
			# Implement exponential backoff with jitter
			delay = min(base_delay * (2 ** (attempt - 1)) + uniform(0, 1), max_delay)
			logger.debug(f"[YL_rtnDetails][D03]: Retrying in {delay:.2f} seconds...")
			time.sleep(delay)
	
	logger.debug(f"[YL_rtnDetails][D04]: <None>")
	logger.info("[YL_rtnDetails][I02]:OUT;")
	return {"nickname": None, "device_on": False, "type": None}



def turnON(ip):

	# Turn on a lighting device specified by IP
	# Return: Success / Fail

	logger.info("[turnON][I01]:IN;")
	logger.debug(f"[turnON][D01]: ip:{ip};")

	beforeStatus = YL_rtnDetails(ip)

	if not beforeStatus.get('device_on'):
		try:
			bulb = Bulb(ip)
			bulb.turn_on()
		except BulbException as e:
			logger.error(f"[turnON][E01]: An error occurred while communicating with the Yeelight device: {e}")
		except Exception as e:
			logger.error(f"[turnON][E02]: Unexpected error: {e}")

		afterStatus = YL_rtnDetails(ip)
		logger.debug(f"[checkStatus][D02]: beforeStatus:{beforeStatus}; afterStatus:{afterStatus}")

		if beforeStatus.get('device_on') == afterStatus.get('device_on'):
			logger.debug("[turnON][D03]: return:Fail")
			logger.info("[turnON][I02]: OUT;")
			return 'Fail'
		else:
			logger.debug("[turnON][D04]: return:Success")
			logger.info("[turnON][I03]:OUT;")
			return 'Success'

	else:
		logger.debug("[turnON][D05]: return:Success")
		logger.info("[turnON][I04]:OUT;")
		return 'Success'


# Completed
def turnOFF(ip):

	# Turn off a lighting device specified by IP
	# Return: Success / Fail

	logger.info("[turnOFF][I01]:IN;")
	logger.debug(f"[turnOFF][D01]: ip:{ip};")

	beforeStatus = YL_rtnDetails(ip)

	if beforeStatus.get('device_on'):
		
		try:
			bulb = Bulb(ip)
			bulb.turn_off()
		except BulbException as e:
			logger.error(f"[turnOFF][E01]: An error occurred while communicating with the Yeelight device: {e}")
		except Exception as e:
			logger.error(f"[turnOFF][E02]: Unexpected error: {e}")

		afterStatus = YL_rtnDetails(ip)
		
		logger.debug(f"[checkStatus][D02]: beforeStatus.get('device_on'):{beforeStatus.get('device_on')}; afterStatus.get('device_on'):{afterStatus.get('device_on')}")

		if beforeStatus.get('device_on') == afterStatus.get('device_on'):
			logger.debug("[turnOFF][D03]: return:Fail")
			logger.info("[turnOFF][I02]:OUT;")
			return 'Fail'
		else:
			logger.debug("[turnOFF][D04]: return:Success")
			logger.info("[turnOFF][I03]:OUT;")
			return 'Success'

	else:
		logger.debug("[turnOFF][D05]: return:Success")
		logger.info("[turnOFF][I04]:OUT;")
		return 'Success'



#  Completed
def updateDevice(device_on, nickname, type, userid, ip):
	
	#  This function is updating device details to the database
	#  Return: None
	
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


#  Completed
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



# Completed
def sendNotification(userid, ip, messageID):

	#  This function is used to send email notification out of the selective operation result.
	#  Return: None

	logger.info(f"[sendNotification][I01]: IN;")
	logger.debug(f"[sendNotification][D01]: IN; userid:{userid}; IP:{ip}; messageid:{messageID}")

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

		# User declares to receive notification
		device_info = YL_rtnDetails(ip)
		varNickname = device_info.get('nickname')
		varStatus = device_info.get('device_on')
		varType = 'Lighting Device'

		varStatus1 = "On" if varStatus == 1 else "Off"

		logger.debug(f"[sendNotification][D02]: varStatus:{varStatus}; varStatus1:{varStatus1}; varType:{varType};")

		formatted_time = datetime.now(pytz.timezone('Europe/London')).strftime('%Y-%m-%d %H:%M:%S%z')
		formatted_time = formatted_time[:-2] + ':' + formatted_time[-2:]

		msg = MIMEMultipart()
		msg['From'] = EMAIL_USER
		msg['To'] = userid
		msg['Subject'] = (f"{varNickname} [{varType}] {STATEMENTS[messageID]} at " f"{formatted_time}")

		body = f"Device: {varNickname} [{varType}]\n"
		body += f"Current Status: {varStatus1}\n"

		body += f"Remark: {STATEMENTS[messageID]}\n"

		body += "Time: " f"{formatted_time}"
		msg.attach(MIMEText(body, 'plain'))

		logger.debug(f"[sendNotification][D03]: Body: \n{body}")

		try:
			with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
				server.login(EMAIL_USER, EMAIL_PASSWORD)
				server.send_message(msg)
				logger.debug(f"[sendNotification][D04]: <Notification sent to {userid}.>")
		except Exception as e:
			logger.error(f"[sendNotification][E01]: Failed to send notification: {e}")
			
		logger.debug("[sendNotification][D05]: <OUT with email_sent>")
	else:
		logger.debug("[sendNotification][D06]: <OUT without email_sent>")
	
	logger.info(f"[sendNotification][I02]: OUT")
	return



def main(argUserid, argIP, argOperation, argScheduleID):

	logger.info(f"------>  ")
	logger.info(F"------>  yeelightControl started  ---")
	logger.info(f"------>  {SYSTEM_NAME} . Version {SYSTEM_VER}  <------")
	logger.info(f"------>  Last Updated: {datetime.fromtimestamp(os.path.getmtime(__file__))}  <------")
	logger.info(f"------>  ")
	
	logger.info(f"[main[I01]:IN;")
	

	if DEVELOPER_MODE == 1:
		logger.info(f"------>  ")
		logger.info(f"------>  ~ ~ ~ ~ ~ ~   D E V E L O P E R   M O D E   ~ ~ ~ ~ ~ ~ ")
		logger.info(f"------>  ")
		
		
		print(f"ENVIRONMENT:{ENVIRONMENT}")
		
		logger.info(f"------>  ")
		logger.info(f"------>  ~ ~ ~ ~ ~ ~   D E V E L O P E R   M O D E   E n d e d   ~ ~ ~ ~ ~ ~ ")
		logger.info(f"------>  ")
		
		exit()
		
	logger.debug(f"[main[D01]: argUserid:{argUserid}; argIP:{argIP}; argOperation:{argOperation}; argScheduleID:{argScheduleID}")


	if argOperation.upper() == 'TEST':

		logger.info("[main][D02]: TEST Section")

		
	elif (isDeviceRegistered(argUserid, argIP)):

		# ON + No Schedule --> CLI
		# F_ON --> Forcing ON
		if (argOperation.upper() == 'ON' and argScheduleID is None) or argOperation.upper() == 'F_ON':

			# On without other affecting factors
			beforeStatus = YL_rtnDetails(argIP)	# Get Device Status
			
			
			if not beforeStatus.get('device_on'):
				#  Device is off and send command to turn on device
				response = turnON(argIP)
				
				#  Get the after operation status of the device
				afterStatus = YL_rtnDetails(argIP)	# Get Device Status
	
				# Update Status to database
				if response == 'Success':
					updateDevice(afterStatus.get('device_on'), afterStatus.get('nickname'), afterStatus.get('type'), argUserid, argIP)
					logger.debug(f"[main][D04]: <Operation {argOperation} Success.	Device ON + Updated>")
				else:
					logger.debug(f"[main][D05]: <Operation {argOperation} failed.  Device can't turn on.	 Current status = {afterStatus}>")
				
				#  Sending Notification to user			
				if argOperation.upper() == 'ON':
					# Called from CLI
					print(f"\tCLI Prompt: Yeelight [{afterStatus.get('nickname')}|{argIP}] is {afterStatus.get('device_on')}")
					sendNotification(argUserid, argIP, 4)
	
				elif argOperation.upper() == 'F_ON':
					# Called from Scheduler F_ON
					# Schedule ID will not be care
					sendNotification(argUserid, argIP, 2)
					
				elif response == 'Fail':
					sendNotification(argUserid, argIP, 10)
					
			else:
				#  Device is already ON .. OPeration skipped
				sendNotification(argUserid, argIP, 12)

				
		# ON + Schedule --> Scheduler call			
		elif argOperation.upper() == 'ON' and argScheduleID is not None:
			
			# On by Schedule Trigger 
			# - General Schedule call
			#
			
			beforeStatus = YL_rtnDetails(argIP)	# Get Device Status
			
			if not beforeStatus.get('device_on'):  

				# Currently OFF
				# Checking Threshold 
				if isOverThreshold(argScheduleID):
					# High Price  --> Skip ON Trigger 
					# Sending notification to user
					sendNotification(argUserid, argIP, 9)
				else:
					
					# Low Price	 --> Trigger ON
						
					# On without other affecting factors 
					response = turnON(argIP)
					
					# Get Device Status
					afterStatus = YL_rtnDetails(argIP)	# Get Device Status
	
					# Update Status to database
					if response == 'Success':
						updateDevice(afterStatus.get('device_on'), afterStatus.get('nickname'), afterStatus.get('type'), argUserid, argIP)
						logger.debug(f"[main][D06]: <Operation {argOperation} Success.	Device ON + Updated>")
							
						# Sending notification to user
						sendNotification(argUserid, argIP, 1)
					else:
						sendNotification(argUserid, argIP, 10)
						logger.debug(f"[main][D07]: <Operation {argOperation} failed.  Device can't turn on.	 Current status = {afterStatus}>")
			else:
				#  Device is already ON .. OPeration skipped
				sendNotification(argUserid, argIP, 12)
				
				
		# AUTO --> Call from Scheduler with Threshold Factors During Schedule
		elif argOperation.upper() == 'AUTO':

			# AUTO
			# Checking current state of device
			beforeStatus = YL_rtnDetails(argIP)	# Get Device Status
			
			# Checking whether over threshold
			threshold = isOverThreshold(argScheduleID)

			if (beforeStatus.get('device_on'), threshold) == (True, True):

				logger.debug("[Main][D08]: <Current Price > Threshold: ON --> OFF>")

				# Turn Off: Current Price > Threshold: ON --> OFF
				response = turnOFF(argIP)

				# Get Device Status
				afterStatus = YL_rtnDetails(argIP)	# Get Device Status

				#	Update Status to database
				if response == 'Success':
					updateDevice(afterStatus.get('device_on'), afterStatus.get('nickname'), afterStatus.get('type'), argUserid, argIP)
					logger.debug(f"[main][D09]: <Operation {argOperation} Success.	Device ON + Updated>")
						
					#  Sending Notification to user
					sendNotification(argUserid, argIP, 7)
				else:
					#  Sending Notification to user
					sendNotification(argUserid, argIP, 10)
					logger.debug(f"[main][D10]: <Operation {argOperation} failed.  Device can't turn off. Current status = {afterStatus}>")
					
			elif (beforeStatus.get('device_on'), threshold) == (True, False):
				# Skip : Current Price < Threshold: ON --> ON
				logger.debug("[Main][D11]: <Current Price < Threshold: ON --> ON>")

			elif (beforeStatus.get('device_on'), threshold) == (False, True):
				# Skip : Current Price > Threshold: OFF --> OFF
				logger.debug("[Main][D12]: <Current Price > Threshold: OFF --> OFF>")

			elif (beforeStatus.get('device_on'), threshold) == (False, False):
				# Turn On: Current Price < Threshold: OFF -->  ON
				logger.debug("[Main][D13]: <Price < Threshold: OFF -->	ON>")

				response = turnON(argIP)
				# Get Device Status
				afterStatus = YL_rtnDetails(argIP)	# Get Device Status

				if response == 'Success':
					updateDevice(afterStatus.get('device_on'), afterStatus.get('nickname'), afterStatus.get('type'), argUserid, argIP)
					logger.debug(f"[main][D14]: <Operation {argOperation} Success.	Device ON + Updated>")
					
					# Sending notification to user
					sendNotification(argUserid, argIP, 3)
				
				else:
					sendNotification(argUserid, argIP, 10)
					logger.debug(f"[main][D15]: <Operation {argOperation} failed.  Device can't turn on.	 Current status = {afterStatus}>")

		# OFF / F_OFF --> Call by CLI and Scheduler
			# OFF + No Schedule ID --> CLI calls
			# OFF + Schedule ID --> Scheduler calls
			# F_OFF --> Forcing OFF
		elif argOperation.upper() == 'OFF' or argOperation.upper() == 'F_OFF':

			#  OFF by CLI or Forcing On from Apps
			# 
			
			# Get Before Device Status
			beforeStatus = YL_rtnDetails(argIP)
			
			if beforeStatus.get('device_on'):
				
				# Device is ON
				# On without other affecting factors
				response = turnOFF(argIP)
				
				#Get AfterStatus
				afterStatus = YL_rtnDetails(argIP)
	
				if response == 'Success':
					updateDevice(afterStatus.get('device_on'), afterStatus.get('nickname'), afterStatus.get('type'), argUserid, argIP)
					logger.debug(f"[main][D16]: <Operation {argOperation} Success. Device OFF + Updated>")
						
					if argOperation.upper() == 'OFF':
						if argScheduleID is None:
							
							# Called from CLI
							print(f"\tCLI Prompt: Yeelight [{afterStatus.get('nickname')}|{argIP}] is {afterStatus.get('device_on')}")
							sendNotification(argUserid, argIP, 8)
							logger.debug("[main][D17]: <Turned off device by CLI command>")
						else:
							sendNotification(argUserid, argIP, 5)
							logger.debug("[main][D18]: <Turned off device by scheduler>")
	
					elif argOperation.upper() == 'F_OFF':
						# Called from Scheduler F_OFF
						# Schedule ID will not be care
						sendNotification(argUserid, argIP, 6)
						logger.debug("[main][D19]: <Turned by device by Schedular Forcing-Off>")
				
				else:
					sendNotification(argUserid, argIP, 10)
					logger.debug(f"[main][D20]: <Operation {argOperation} failed.  Device can't turn off. Current status = {afterStatus}>")
			else:
				sendNotification(argUserid, argIP, 11)
				logger.debug(f"[main][D21]: <Device is currently OFF.  Operation Skipped>")
				
	else:

		# Return .. Device not belonging to this user
		logger.debug("[Main][D22]: <User Device not Found>")

	logger.info(f"[main][I02]: OUT")
	logger.info("---  yeelightControl Ended	 ---")


if __name__ == "__main__":
	parser = argparse.ArgumentParser(
		description='Control your Yeelight smart lighting: trigger actions and retrieve device information such as status and settings.'
	)
	parser.add_argument('-userid', type=str, help='The user ID')
	parser.add_argument('-ip', type=str, help='The IP address of device')
	parser.add_argument(
		'-operation',
		type=str.upper,
		required=True,
		choices=['ON', 'OFF', 'AUTO', 'F_ON', 'F_OFF', 'TEST'],  # Allowed operations
		help='The mode of operation (e.g., ON, OFF).'  # AUTO, F_ON, F_OFF - a hidden subfunction of ON toggling with threshold
	)
	parser.add_argument('-schedule', type=str, help='Accepting schedule ID of the caller\'s process.')
	args = parser.parse_args()

	# Custom validation logic for conditional arguments
	if args.operation != 'TEST':
		# For operations other than UPDATEALL, -userid and -ip are required
		if not args.userid:
			print("Error: -userid is required for this operation.", file=sys.stderr)
			sys.exit(1)
		if not args.ip:
			print("Error: -ip is required for this operation.", file=sys.stderr)
			sys.exit(1)
	
	# Call the main function
	main(args.userid, args.ip, args.operation, args.schedule)




###########################
##	Obsoleted Functions	 ##
###########################
