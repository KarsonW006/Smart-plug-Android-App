'''
	Program: updater.py  [aka updater_v1.py]

	Objective:
		- Update status of all smart devices
			- Update the nickname
			- update the device_on status


	usage:	updater.py


	Dependency:
		pip install pymysql
		pip install pytz (if no apschedule, sqlalchemy installed)
		pip install tapo
		pip install yeelight


	Version: 20241225_v001 [Released]


	Changelog:
		- 20241224_v001		--> Initial Version. Using Python-schedule 
		- 20241225_v001		--> Initial Version 2.  Project directory structural revamp


	Functions List:
		def connect_with_retry():
		def updateDevice(device_on, nickname, type, userid, ip):
		async def TP_rtnDetails(userid, ip, pin, retries=3, base_delay=1, max_delay=1):
		async def TP_updateAll():
		def YL_setName(ip):
		def YL_rtnDetails(ip, retries=3, base_delay=1, max_delay=1):
		def YL_updateAll():
		async def main():


	Remark:
		For Deployment:
			1. Update Version number
			2. Set the Indicator from '[Developing]'/'[Pre-Released]' to '[Released]'
			3. Ensure ChangeLog is correct
			4. Copy from Sandbox to Production by eliminating '_vX' suffix

		For Daemon actions:
			sudo systemctl start updater.service
			sudo systemctl stop updater.service
			sudo systemctl restart updater.service
			sudo systemctl status updater.service


	Setup as System Services:
		1. Create a system daemon
			bash> sudo nano /etc/systemd/system/updater.service
				[Unit]
				Description=Python Devices Updater Service
				After=network.target

				[Service]
				Type=simple
				ExecStart=./Production/smartProject/updater/venv/bin/python3 ./Production/smartProject/updater/updater.py
				Restart=on-failure
				RestartSec=5s
				User=YOUR_SERVICE_USER

				[Install]
				WantedBy=multi-user.target

		2. Reload systemd to pick up the new service file
			bash> sudo systemctl daemon-reload

		3. Enable the service to start on boot
			bash> sudo systemctl enable updater.service


	Daily Operation for the system services:
		--> Start the service from CLI
			bash> sudo systemctl start updater.service

		--> Check the status to make sure it's running
			bash> sudo systemctl status updater.service

		--> Check the status to make sure it's running
			bash> sudo systemctl status updater.service

		--> Stop the service
			bash> sudo systemctl stop updater.service

		--> Restart the service
			bash> sudo systemctl restart updater.service

		--> Disable the service from starting at boot
			bash> sudo systemctl disable updater.service


	Proper Remove a Services:

		1. Stop the Service
			bash> sudo systemctl stop updater.service

		2. Disable the Service
			bash> sudo systemctl disable updater.service

		3. Delete the Service File
			bash> sudo rm /etc/systemd/system/updater.service

		4. Reload systemd Daemon
			bash> sudo systemctl daemon-reload

		5. Check for Any Residual Service Links
			bash> systemctl list-unit-files | grep updater.service


'''


import pymysql
import os
import time
from datetime import datetime, timedelta
import logging
from logging.handlers import TimedRotatingFileHandler
from yeelight import Bulb, BulbException
from tapo import ApiClient
from random import uniform  # randomize timer
import asyncio  # Import asyncio to use asyncio.run

# Define constants
SLEEP_DURATION = 180		# Time to sleep in seconds
SLEEP_SHORT = 3
MAX_RETRIES = 5	 # Maximum number of retries for database connection
RETRY_DELAY = 5	 # Delay in seconds between retries

SYSTEM_NAME = 'updater [Series.2]'
SYSTEM_VER = '20241225_v001'
DEVELOPER_MODE = 0			#  Developer mode: ON (1) | OFF (0)
ENVIRONMENT = "Sandbox" if "Sandbox" in os.path.abspath(os.path.dirname(__file__)) else "Production"


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
	"./Sandbox/smartProject/.logs/updater.log" if ENVIRONMENT == 'Sandbox' else "./Production/smartProject/.logs/updater.log",
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


##########################################################################
##  Shared Modules

# Completed
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



##########################################################################
##  TAPO Uses only

#  Completed
async def TP_rtnDetails(userid, ip, pin, retries=3, base_delay=1, max_delay=1):
	
	# This function is used to get selective attributes of the smart device
	# Return: DICT (nickname, device_on, type)
	
	logger.info("[TP_rtnDetails][I01]: IN")
	logger.debug(f"[TP_rtnDetails][D01]: userid:{userid}; ip:{ip}; pin:{pin}")
	
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
			
			logger.debug(f"[TP_rtnDetails][D02]: result:{result}")
			logger.info("[TP_rtnDetails][I02]: OUT")
			return result
			
		except Exception as e:
			attempt += 1
			logger.error(f"[TP_rtnDetails][E01]: Attempt {attempt} failed with error: {e}")
			
			if attempt > retries:
				logger.error(f"[TP_rtnDetails][E02]: All retries exhausted.")
				break
			
			# Implement exponential backoff with jitter
			delay = min(base_delay * (2 ** (attempt - 1)) + uniform(0, 1), max_delay)
			logger.debug(f"[TP_rtnDetails][D03]: Retrying in {delay:.2f} seconds...")
			await asyncio.sleep(delay)
		
	# Return a default value if an exception occurs
	logger.info("[TP_rtnDetails][I03]: OUT")
	return {"nickname": None, "device_on": False, "type": None}
	
	
# Completed 
async def TP_updateAll():
	
	#  This is a caller function in trigging the update of the status of all TAPO smart devices to the database table: userDevices
	#  Return: None

	logger.info("[TP_updateAll][I01]:IN")
		
	conn = None	 # Ensure conn is initialized
	conn = connect_with_retry()
	cursor = conn.cursor(pymysql.cursors.DictCursor) 
	
	cursor.execute("SELECT userDevices.userid as userid, userDevices.ip as ip, userProfiles.tpin as tpin FROM userDevices, userProfiles WHERE userDevices.userid = userProfiles.userid AND userDevices.type LIKE '%TAPO%'")
	results = cursor.fetchall()

	logger.debug(f"[Main][D01]: <Fetched {len(results)} schedules from the database.>")

	if results:
		for result in results:
			
			userid = result.get('userid')
			ip = result.get('ip')
			pin = result.get('tpin')

			device_info = await TP_rtnDetails(userid, ip, pin)
			
			device_on = 1 if device_info.get('device_on') else 0
			nickname = device_info.get('nickname')
			type = device_info.get('type')
			
			logger.debug(f"[TP_updateAll][D02]: device_on:{device_on}; nickname:{nickname}; type:{type}; userid:{userid}; ip:{ip};")
			
			if nickname != None:
				updateDevice(device_on, nickname, type, userid, ip)
			else:
				logger.warning(f"[TP_updateAll][W01]: device_on:{device_on}; ip:{ip}; <Device Connection Error>")
			
			logger.debug(f"TP_updateAll][D03]: <Wait for {SLEEP_SHORT} seconds to update next device>")
			time.sleep(SLEEP_SHORT)
	else:
		logger.debug(f"[TP_updateAll][D04]: <No TAPO Device Found>")
		
	if conn and conn.open:
		conn.close()
		logger.debug("[TP_updateAll][D05]: <Database:disconnected>")
	
	logger.info("[TP_updateAll][I02]:OUT;")




##########################################################################
##  Yeelight Uses only

# Completed
def YL_setName(ip):

	# Check the current ON/OFF status of a lighting device(IP)
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
	


#  Completed
def YL_updateAll():

	#  This is a caller function in trigging the update of the status of all yeelight lighting devices to the database table: userDevices
	#  Return: None
	
	logger.info("[YL_updateAll][I01]:IN")

	conn = connect_with_retry()
	cursor = conn.cursor(pymysql.cursors.DictCursor)
	cursor.execute("SELECT userDevices.userid as userid, userDevices.ip as ip FROM userDevices where type like 'YEELIGHT%'")
	results = cursor.fetchall()

	logger.debug(f"[YL_updateAll][D01]: <Fetched {len(results)} schedules from the database.>")

	if results:
		for result in results:

			logger.debug(f"[YL_updateAll][D02]: result.get('ip'):{result.get('ip')};")

			#  Get Device Information
			userid = result.get('userid')
			device_info = YL_rtnDetails(result.get('ip'))

			logger.debug(f"[YL_updateAll][D03]: result.get('ip'):{result.get('ip')}; device_info.get('nickname'):{device_info.get('nickname')}; device_info.get('device_on'):{device_info.get('device_on')}; device_info.get('type'):{device_info.get('type')}; type(device_info.get('nickname')):{type(device_info.get('nickname'))};  ")

			
			# Check whether NickName == None
			# If None --> Set a default Name
			if (device_info.get('nickname') == None):
				
				logger.debug(f"[YL_updateAll][D04]: <Set Device Name>")
				
				response = YL_setName(result.get('ip'))
				if response == 'Success':
					#  Get and update device details
					device_info = YL_rtnDetails(result.get('ip'))
				
				logger.debug(f"[YL_updateAll][D05]: response:{response}; result.get('ip'):{result.get('ip')}; device_info.get('nickname'):{device_info.get('nickname')}; device_info.get('device_on'):{device_info.get('device_on')}; device_info.get('type'):{device_info.get('type')}; type(device_info.get('nickname')):{type(device_info.get('nickname'))};  ")

			#  Update device details into database
			if device_info.get('nickname') != None:
				updateDevice(device_info.get('device_on'), device_info.get('nickname'), device_info.get('type'), result.get('userid'), result.get('ip'))
			else:
				logger.warning(f"[YL_updateAll][W01]: device_on:{device_on}; ip:{ip}; <Device Connection Error>")
		
			#  Precaution Step  -->  avoid jamming of API and relief system loading
			logger.debug(f"TP_updateAll][D06]: <Wait for {SLEEP_SHORT} seconds to update next device>")
			time.sleep(SLEEP_SHORT)

	else:
		logger.debug(f"[YL_updateAll][D07]: <No Yeelight Device Found>")
		
	if conn and conn.open:
		conn.close()
		logger.debug("[YL_updateAll][D08]: Database:disconnected")

	logger.info("[YL_updateAll][I02]:OUT")



async def main():

	logger.info(F"------>")
	logger.info(F"------>  updater started  ---")
	logger.info(f"------>  {SYSTEM_NAME} . Version {SYSTEM_VER}  <------")
	logger.info(f"------>  Last Updated: {datetime.fromtimestamp(os.path.getmtime(__file__))}  <------")
	logger.info(F"------>")
	
	logger.info("[main][I01]: IN")

	if DEVELOPER_MODE == 1:
		logger.info(f"------>  ")
		logger.info(f"------>  ~ ~ ~ ~ ~ ~   D E V E L O P E R   M O D E   ~ ~ ~ ~ ~ ~ ")
		logger.info(f"------>  ")
		
		TP_updateAll()
		YL_updateAll()
		#print(f"ENVIRONMENT:{ENVIRONMENT}")
		
		logger.info(f"------>  ")
		logger.info(f"------>  ~ ~ ~ ~ ~ ~   D E V E L O P E R   M O D E   E n d e d   ~ ~ ~ ~ ~ ~ ")
		logger.info(f"------>  ")
		
		exit()


	#  Main Function
	#

	##############################
	##	Development Settings:
	
	DEVELOPER_COUNT = 0


	logger.debug("[main][D02]: <Starting infinite loop until receiving Keyboard Interrupt>")

	"""Main function to start the scheduler and polling loop."""
	while True:

		##########################################
		##	DEVELOPMENT MODE control mechanism	##
		##
		if DEVELOPER_MODE == 1:
			logger.debug(f"[main][D03]: DEVELOPER_COUNT:{DEVELOPER_COUNT}")
			if DEVELOPER_COUNT == 1:
				logger.debug("[main][D04]: <DEVELOPMENT QUIT>")
				break
		

		# Update all TAPO devices
		logger.debug("[main][D05]: <Update TAPO devices status>")
		await TP_updateAll()
		logger.debug(f"[main][06]: <TP Updated>")


		# Update all Yeelight devices
		logger.debug("[main][D07]: <Update Yeelight devices status>")
		YL_updateAll()
		logger.debug(f"[main][D08]: <YL updated>")


		if DEVELOPER_MODE == 1:
			DEVELOPER_COUNT+=1
			logger.debug(f"[main][D09]: DEVELOPER_COUNT:{DEVELOPER_COUNT}")
		
		logger.debug(f"[main][D10]: <Waiting for {SLEEP_DURATION} seconds for next polling.>")
		logger.info(F"------>")
		logger.info(F"------>")
		time.sleep(SLEEP_DURATION)	# Wait before checking again
	
	logger.info("[main][I03]: OUT")



if __name__ == "__main__":

	try:
		asyncio.run(main())
		
	except (KeyboardInterrupt, SystemExit):
		logger.info("------>")
		logger.info("------>  updater stopped  ---")
		logger.info("------>")

'''
	# Remark:
	# Stop the service
	sudo systemctl stop scheduler.service

	# Restart the service
	sudo systemctl restart scheduler.service

	# Disable the service from starting at boot
	sudo systemctl disable scheduler.service

'''



###########################
##	Obsoleted Functions	 ##
###########################
