'''
	Program: scheduler.py  [aka scheduler_v10.py]

	Objective:
		- Manage and handle the user's schedules
			- Polling for schedules change
			- Add/Amend/Delete/Disable a schedule
			- Update schedule status


	usage:	scheduler.py


	Dependency:
		pip install pymysql
		pip install apscheduler
		pip install sqlalchemy



	Version: 20241225_v002 [Released]

	Changelog:
		- 20241011_v001		--> Initial Version. Using Python-schedule
		- 20241015_v001		--> [Change] Changed to use APScheduler
		- 20241020_v002		--> [Update] Bugs fixed
		- 20241022_v001		--> [Add] Cater Timezone and DST issues
		- 20241026_v005		--> [Change] Remove coding in using schedule_subtasks table
		- 20241114_v001		--> [Change] Fixing unstable database server issue (Connection V2 - MySQL)
		- 20241115_v001		--> [Change] Fixing unstable database server issue (Connection V2 - APScheduler)
		- 20241116_v001		--> [Change] Fixing unstable database server issue (Connection V2 - mySQL.Connector -> PyMySQL)
		- 20241120_v002		--> [Change] APScheduler uses local data file (SQLite)
		- 20241201_v001		--> [Add] Integrated dataSync daily routine run by using APScheduler
		- 20241203_v001		--> [Add] Add Debug Level
		- 20241220_v001		--> [Add] Add support to client's requested Energy Saving Requirements [after 2nd iteration]
		- 20241224_v001		--> [Add] Add support for Yeelight Smart Lightings [Xth iteration]
							--> [***] Have to work with smartPlug v11 or above and yeelight Control v1 or above
		- 20241225_v001		--> Initial Version 2.	Project directory structural revamp
		- 20241225_v002		--> [Change] Change Tapo Controller program name from smartPlug to tapoControl


	Functions List:
		def processRunner(venv, program, params):
		def dataSync_onLoad():
		def dataSync_load(max_retries=5, retry_delay=2):
		def dataMart_load(max_retries=5, retry_delay=2):
		def connect_with_retry():
		def fetch_schedules():
		def runScript(venv, program, params, operation, schedule_id, run_mode):
		def updateStatus(schedule_id, status):
		def adjustTime(input_time_str):
		def rtnExecutionSetting(ip):
		def processTaskTimes(start_time, end_time):
		def add_schedule_to_scheduler(schedule, max_retries=5, retry_delay=2):
		def remove_schedule_from_scheduler(schedule_id, max_retries=3, retry_delay=2):
		def main():


	Remark:
		For Deployment:
			1. Update Version number
			2. Set the Indicator from '[Developing]'/'[Pre-Released]' to '[Released]'
			3. Ensure ChangeLog is correct
			4. Copy from Sandbox to Production by eliminating '_vX' suffix

		For Daemon actions:
			sudo systemctl start scheduler.service
			sudo systemctl stop scheduler.service
			sudo systemctl restart scheduler.service
			sudo systemctl status scheduler.service


	Setup as System Services:
		1. Create a system daemon
			bash> sudo nano /etc/systemd/system/scheduler.service
				[Unit]
				Description=Python Scheduler Service
				After=network.target
				
				[Service]
				Type=simple
				ExecStart=./Production/smartProject/scheduler/venv/bin/python3 ./Production/smartProject/scheduler/scheduler.py
				Restart=on-failure
				RestartSec=5s
				User=YOUR_SERVICE_USER
				
				[Install]
				WantedBy=multi-user.target

		2. Reload systemd to pick up the new service file
			bash> sudo systemctl daemon-reload

		3. Enable the service to start on boot
			bash> sudo systemctl enable scheduler.service


	Daily Operation for the system services:
		--> Start the service from CLI
			bash> sudo systemctl start scheduler.service

		--> Check the status to make sure it's running
			bash> sudo systemctl status scheduler.service

		--> Check the status to make sure it's running
			bash> sudo systemctl status scheduler.service

		--> Stop the service
			bash> sudo systemctl stop scheduler.service

		--> Restart the service
			bash> sudo systemctl restart scheduler.service

		--> Disable the service from starting at boot
			bash> sudo systemctl disable scheduler.service


	Proper Remove a Services:

		1. Stop the Service
			bash> sudo systemctl stop scheduler.service

		2. Disable the Service
			bash> sudo systemctl disable scheduler.service

		3. Delete the Service File
			bash> sudo rm /etc/systemd/system/scheduler.service

		4. Reload systemd Daemon
			bash> sudo systemctl daemon-reload

		5. Check for Any Residual Service Links
			bash> systemctl list-unit-files | grep scheduler.service


'''


import pymysql
import os
import subprocess
import time
import logging
from logging.handlers import TimedRotatingFileHandler
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timedelta



# Define constants
SLEEP_DURATION = 60		# Time to sleep in seconds
MAX_RETRIES = 5	 # Maximum number of retries for database connection
RETRY_DELAY = 5	 # Delay in seconds between retries

SYSTEM_NAME = 'Scheduler [Series.2]'
SYSTEM_VER = '20241225_v002'
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
	"./Sandbox/smartProject/.logs/scheduler.log" if ENVIRONMENT == 'Sandbox' else "./Production/smartProject/.logs/scheduler.log",
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



# Initialize the scheduler
# Setup APScheduler with SQLAlchemyJobStore for MariaDB
db_path = './Sandbox/smartProject/.data/jobs.db' if ENVIRONMENT == 'Sandbox' else './Production/smartProject/.data/jobs.db'
scheduler = BackgroundScheduler({'apscheduler.timezone': 'Europe/London'})
scheduler.add_jobstore(
	SQLAlchemyJobStore(url=f'sqlite:///{db_path}'),	 # SQLite URL for the custom path
	alias='mariadb'
)
logger.debug(f"[APScheduler][D00]: db_path:{db_path}")



#################################################
##	This section is used to load other modules ##
#################################################

def dataSync_onLoad():
	
	#  This function is used to check and load missing scheduled sync-task
	#  Return: None
	
	logger.info("[dataSync_onLoad][I01]: IN;")
	
	now = datetime.now()
	
	conn = connect_with_retry()
	cursor = conn.cursor(pymysql.cursors.DictCursor)  # Use pymysql cursor for dictionary results
		
	sql = "select date(valid_from) as valid_from from rates ORDER BY valid_from DESC LIMIT 1"
	
	cursor.execute(sql)
	result = cursor.fetchone()  # Fetch the result
	
	start_date = result['valid_from']  # Fetch the start date from the result
	logger.debug(f"[dataSync_onLoad][D01]: start_date:{start_date}; type(start_date):{type(start_date)}")
	
	if conn.open:
			conn.close()
	
	today = datetime.today().date()
	tomorrow = today + timedelta(days=1)
	
	days_diff = (today + timedelta(days=1) - start_date).days
	logger.debug(f"[dataSync_onLoad][D02]: start_date:{start_date}; today:{today}; days_diff:{days_diff}")
	
	if start_date != tomorrow:
		if ENVIRONMENT == 'Sandbox':
			venv = './Sandbox/smartProject/dataSync/venv/bin/python'
			program = './Sandbox/smartProject/dataSync/dataSync.py'
		else:
			venv = './Production/smartProject/dataSync/venv/bin/python'
			program = './Production/smartProject/dataSync/dataSync.py'
	
		for i in range(days_diff + 1):
			inputDate = (start_date + timedelta(days=i)).strftime("%Y-%m-%d")
			
			# Prepare the params to pass to the program
			params = ['-date', inputDate]
			
			logger.debug(f"[dataSync_onLoad][D03]: params:{params}")
			
			# Run the process for the current date
			processRunner(venv, program, params)
	else:
		logger.debug(f"[dataSync_onLoad][D04]: <Data exist.  No need to reload>")
		
	logger.info("[dataSync_onLoad][I02]: OUT")


# Completed
def dataSync_load(max_retries=5, retry_delay=2):

	#  This function is used to create/load dataSync into APScheduler
	#  Return: None

	logger.info("[dataSync_load][I01]: IN;")
	logger.debug("[dataSync_load][D01]: <Attempting to schedule dataSync for schedule ID dataSync>")

	try:

		#  Execution Details
		if ENVIRONMENT == 'Sandbox':
			venv = './Sandbox/smartProject/dataSync/venv/bin/python'
			program = './Sandbox/smartProject/dataSync/dataSync.py'
			params = []
		else:
			venv = './Production/smartProject/dataSync/venv/bin/python'
			program = './Production/smartProject/dataSync/dataSync.py'
			params = []

		logger.debug(f"[dataSync_load][D02]: venv:{venv}; program:{program}; params:{params}")


		# Adding Job to the APSchedule
		for attempt in range(max_retries):
			try:
				scheduler.add_job(
					processRunner,
					args=[venv, program, params],
					#trigger=CronTrigger(hour=17, minute=38, second=0),
					trigger=CronTrigger(hour=15, minute=58, second=0),
					id='dataSync',
					jobstore='mariadb',
					replace_existing=True
				)
				logger.debug(f"[dataSync_load][D03]: <Successfully scheduled dataSync job for schedule ID dataSync on attempt {attempt + 1}.>")
				break  # Exit loop on success

			except Exception as e:
				logger.error(f"[dataSync_load][E01]: <Attempt {attempt + 1} to schedule dataSync for schedule ID dataSync failed: {e}>")
				if attempt < max_retries - 1:
					time.sleep(retry_delay)	 # Delay before retrying
				else:
					raise  # Re-raise exception if all attempts fail

	except Exception as e:
		logger.error(f"[dataSync_load][E02]: <Failed to add schedule ID dataSync to scheduler after {max_retries} attempts: {e}>")

	finally:
		logger.info("[dataSync_load][I02]: OUT;")



# Completed
def dataMart_load(max_retries=5, retry_delay=2):

	#  This function is used to create/load dataMart into APScheduler
	#  Return: None

	logger.info(f"[dataMart_load][I01]: IN;")
	logger.debug("[dataMart_load][D01]: max_retries:5; retry_delay:2")

	try:
		# Schedule the start job based on run_mode
	
		logger.debug(f"[dataMart_load][D02]: <Attempting to schedule dataMart for schedule ID dataMart>")

		#  Execution Details
		if ENVIRONMENT == 'Sandbox':
			venv = './Sandbox/smartProject/dataMart/venv/bin/python'
			program = './Sandbox/smartProject/dataMart/dataSync.py'
			params = []
		else:
			venv = './Production/smartProject/dataSync/venv/bin/python'
			program = './Production/smartProject/dataSync/dataSync.py'
			params = []
		
		logger.debug(f"[dataSync_load][D03]: venv:{venv}; program:{program}; params:{params}")


		#  Adding routine job into APScheduler
		for attempt in range(max_retries):
			try:
				scheduler.add_job(
					processRunner,
					args=[venv, program, params],
					trigger=CronTrigger(hour=17, minute=00, second=0),
					#trigger=CronTrigger(day=1, hour=0, minute=0, second=0),
					id='dataMart',
					jobstore='mariadb',
					replace_existing=True
				)
				logger.debug(f"[dataMart_load][D04]: <Successfully scheduled dataMart job for schedule ID dataMart on attempt {attempt + 1}>")
				break  # Exit loop on success

			except Exception as e:
				logger.error(f"[dataMart_load][E01]: Attempt {attempt + 1} to schedule dataMart for schedule ID dataMart failed: {e}")
				if attempt < max_retries - 1:
					time.sleep(retry_delay)	 # Delay before retrying
				else:
					raise  # Re-raise exception if all attempts fail

	except Exception as e:
		logger.error(f"[dataMart_load][E02]: Failed to add schedule ID dataMart to scheduler after {max_retries} attempts: {e}")
	finally:
		logger.info("[dataMart_load][I02]: OUT;")



# Completed
def getUsages_load(max_retries=5, retry_delay=2):

	#  This function is used to create/load getUsages into APScheduler
	#  Return: None

	logger.info("[getUsages_load][I01]: IN;")
	logger.debug("[getUsages_load][D01]: <Attempting to schedule getUsages for schedule ID getUsages>")

	try:

		#  Execution Details
		if ENVIRONMENT == 'Sandbox':
			venv = './Sandbox/smartProject/getUsages/venv/bin/python'
			program = './Sandbox/smartProject/getUsages/getUsages.py'
			params = []
		else:
			venv = './Production/smartProject/getUsages/venv/bin/python'
			program = './Production/smartProject/getUsages/getUsages.py'
			params = []

		logger.debug(f"[getUsages_load][D02]: venv:{venv}; program:{program}; params:{params}")


		# Adding Job to the APSchedule
		for attempt in range(max_retries):
			try:
				scheduler.add_job(
					processRunner,
					args=[venv, program, params],
					#trigger=CronTrigger(hour=17, minute=38, second=0),
					trigger=CronTrigger(hour=23, minute=00, second=0),
					id='getUsages',
					jobstore='mariadb',
					replace_existing=True
				)
				logger.debug(f"[getUsages_load][D03]: <Successfully scheduled getUsages job for schedule ID getUsages on attempt {attempt + 1}.>")
				break  # Exit loop on success

			except Exception as e:
				logger.error(f"[getUsages_load][E01]: <Attempt {attempt + 1} to schedule getUsages for schedule ID getUsages failed: {e}>")
				if attempt < max_retries - 1:
					time.sleep(retry_delay)	 # Delay before retrying
				else:
					raise  # Re-raise exception if all attempts fail

	except Exception as e:
		logger.error(f"[getUsages_load][E02]: <Failed to add schedule ID getUsages to scheduler after {max_retries} attempts: {e}>")

	finally:
		logger.info("[getUsages_load][I02]: OUT;")



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



# Completed
def fetch_schedules():

	#  This function is used to fetch all records from the database which are required to process
	#  Return: ARRAY

	logger.info("[fetch_schedules][I01]: IN");

	"""Fetch the schedules from the database."""
	try:
		conn = connect_with_retry()
		cursor = conn.cursor(pymysql.cursors.DictCursor)  # Use pymysql cursor for dictionary results
		cursor.execute("SELECT schedule_id, userid, ip, start_time, end_time, run_mode, status FROM schedules where status='Pending' or status='Deleting' or status='Disabling'or status='Forcing_On' or status='Forcing_Off' ")
		result = cursor.fetchall()

		logger.debug(f"[fetch_schedules][D01]: len(result):{len(result)}")

	finally:
		if conn.open:
			conn.close()
		logger.debug(f"[fetch_schedules][D02]: result:{result}")
		logger.info("[fetch_schedules][I02]: OUT")
		return result



# Completed
def processRunner(venv, program, params):

	# This function is a loader and runner of a module process.
	# Return: subprocess's object

	logger.info("[processRunner][I01]: IN;")
	logger.debug(f"[processRunner][D01]: venv:{venv}; program:{program}; params:{params};")

	#command = [venv, program] + params 
	
	command = [venv, program] + [str(param) for param in params]  # Ensure all params are strings
	result = None  # Initialize result to avoid UnboundLocalError
	logger.debug(f"Command: {' '.join(command)}")
	
	try:
		# Run the command
		

		result = subprocess.run(command, capture_output=True, text=True)

		logger.debug(f"[processRunner][D02]: command:{command};")
		logger.debug(f"[processRunner][D03]: type(result):{type(result)};")
		
		if result.returncode == 0:
			logger.debug(f"[processRunner][D04]: command:{' '.join(command)}; result.returncode:{result.returncode}")
		else:
			logger.error(f"[processRunner][E01]: <Script execution failed with return code {result.returncode}>")
			logger.error(f"[processRunner][E02]: Stdout: {result.stdout}")
			logger.error(f"[processRunner][E03]: Stderr: {result.stderr}")

	except FileNotFoundError:
		logger.error(f"[processRunner][E04]: File not found: {program}")

	except Exception as e:
		logger.error(f"[processRunner][E05]: Error executing {' '.join(command)}: {e}")

	finally:
		logger.info("[processRunner][I02]: OUT")
		return result if result else subprocess.CompletedProcess(args=command, returncode=-1)  # Return fallback



# Completed
def runScript(venv, program, params, operation, schedule_id, run_mode):
	
	#  This function is used to call a python script and update the status of the schedule
	#  Return: None
	
	logger.info("[runScript][I01]: IN")
	logger.debug(f"[runScript][D01]: venv:{venv}; program:{program}; params:{params}; operation:{operation}; schedule_id:{schedule_id}; run_mode:{run_mode}")

	try:

		logger.debug("[runScript][D02]: <processRunner called.>")
		result = processRunner(venv, program, params)
		
		if result.returncode == 0:
			logger.debug(f"[runScript][D03]: <processRunner:Success ({result.returncode})>")
		else:
			logger.debug(f"[runScript][D04]: <processRunner:Fail ({result.returncode})>")
		
		if operation == 'ON' or operation == 'AUTO':
			logging.debug(f"[runScript][D05]: Operation:{operation}; Run-mode:{run_mode}; <Status:Running;>")
			updateStatus(schedule_id, 'Running')

		elif operation == 'OFF':

			if run_mode == 'Repeat':
				logging.debug(f"[runScript][D06]: Operation:{operation}; Run-mode:{run_mode}; <Status:Scheduled;>")
				updateStatus(schedule_id, 'Scheduled')
			else:
				logging.debug(f"[runScript][D07]: Operation:{operation}; Run-mode:{run_mode}; <Status:Disabled;>")
				updateStatus(schedule_id, 'Disabled')

	except Exception as e:
		logger.error(f"[runScript][E01]: Error executing processRunner: {e}")
	finally:
		return result
		logger.info("[runScript][I02]: OUT")
		


# Completed
def updateStatus(schedule_id, status):

	#  This function is used to update the status of a schedule
	#  Return: None

	logger.info("[updateStatus][I01]: IN;")
	logger.debug(f"[updateStatus][D01]: schedule_id:{schedule_id}; status:{status}")

	try:
		conn = connect_with_retry()
		cursor = conn.cursor()
		cursor.execute("UPDATE schedules SET status = %s, updated_at = %s WHERE schedule_id = %s", (status, datetime.now(), schedule_id))
		conn.commit()
		logger.debug(f"[updateStatus][D02]: <Updated schedule ID {schedule_id} status to {status}>")
	finally:
		if conn.open:
			conn.close()
		logger.info("[updateStatus][I02]: OUT")



# Completed
def rtnExecutionSetting(ip):

	#  This function is used to return the brand of the smart devices
	#  Return: TAPO or YEELIGHT

	logger.info("[rtnExecutionSetting][I01]: IN")
	logger.debug(f"[rtnExecutionSetting][D01]: ip:{ip}")

	try:
		conn = connect_with_retry()
		cursor = conn.cursor(pymysql.cursors.DictCursor)  # Use pymysql cursor for dictionary results
		cursor.execute(f"SELECT type FROM userDevices where ip='{ip}'")
		result = cursor.fetchone()
		
		logger.debug(f"[rtnExecutionSetting][D02]: len(result):{len(result)}; result.get('type'):{result.get('type')}")

		if 'TAPO' in result.get('type'):

			logger.debug(f"[rtnExecutionSetting][D03]: RETURN:TAPO_Settings")
			return {
				"start_venv": './Production/smartProject/tapo/venv/bin/python',
				"start_script": './Production/smartProject/tapo/tapoControl.py',
				"end_venv": './Production/smartProject/tapo/venv/bin/python',
				"end_script": './Production/smartProject/tapo/tapoControl.py'
			}
		elif 'YEELIGHT' in result.get('type'):
			logger.debug(f"[rtnExecutionSetting][D04]: RETURN:YEELIGHT_Settings;")
			return {
				"start_venv": './Production/smartProject/yeelight/venv/bin/python',
				"start_script": './Production/smartProject/yeelight/yeelightControl.py',
				"end_venv": './Production/smartProject/yeelight/venv/bin/python',
				"end_script": './Production/smartProject/yeelight/yeelightControl.py',
			} 
		else:
			logger.debug(f"[rtnExecutionSetting][D05]: RETURN:UNKNOWN;")

			return {
				"start_venv": None,
				"start_script": None,
				"end_venv": None,
				"end_script": None
			}

	finally:
		if conn.open:
			conn.close()
		logger.info("[rtnExecutionSetting][I02]: OUT")



def processTaskTimes(start_time, end_time):
	
	logger.info("[processTaskTimes][I01]: IN")
	logger.debug(f"[processTaskTimes][D01]: start_time:{start_time}({type(start_time)}); end_time:{end_time}({type(end_time)})")
	
	
	# Use the current time as submission time
	submission_datetime = datetime.now()
	current_date = submission_datetime.date()
	
	logger.debug(f'[processTaskTimes][D02]: submission_datetime:{submission_datetime}; current_date:{current_date};')
	
	# Parse start and end times with current date
	start_datetime = datetime.strptime(f"{current_date} {start_time}", "%Y-%m-%d %H:%M:%S")
	end_datetime = datetime.strptime(f"{current_date} {end_time}", "%Y-%m-%d %H:%M:%S")
	
	# Handle end time crossing midnight
	if end_datetime <= start_datetime:
		end_datetime += timedelta(days=1)
	
	if submission_datetime > end_datetime:
		# If current time is after the period, schedule for tomorrow
		start_datetime += timedelta(days=1)
		end_datetime += timedelta(days=1)
	
	elif start_datetime <= submission_datetime <= end_datetime:
		# If current time is within the period, shift to tomorrow
		start_datetime += timedelta(days=1)
		end_datetime += timedelta(days=1)
	
	logger.debug(f'[processTaskTimes][D03]: submission_datetime:{submission_datetime}; start_time:{start_datetime.strftime("%Y-%m-%d %H:%M")}({type(end_datetime.strftime("%Y-%m-%d %H:%M"))}); end_time:{end_datetime.strftime("%Y-%m-%d %H:%M")}({type(end_datetime.strftime("%Y-%m-%d %H:%M"))});')
	logger.info("[processTaskTimes][I02]: OUT")
	return {"start_time": start_datetime.strftime("%Y-%m-%d %H:%M"), "end_time": end_datetime.strftime("%Y-%m-%d %H:%M")}



# Completed
def add_schedule_to_scheduler(schedule, max_retries=5, retry_delay=2):
	
	#  This Function is used to add a new schedule or amend an existing schedule
	#  Return: None
	
	logger.info("[add_schedule_to_scheduler][I01]: IN")
	logger.debug(f"[add_schedule_to_scheduler][D01]: schedule:{schedule}; max_retries:5; retry_delay:2")

	# Extract schedule details
	schedule_id = schedule.get('schedule_id')
	userid = schedule.get('userid')
	ip = schedule.get('ip')
	start_time = schedule.get('start_time')
	end_time = schedule.get('end_time')
	run_mode = schedule.get('run_mode')	 # 'Repeat' or 'Run-once'

	# Get Execution Settings
	settings = rtnExecutionSetting(ip)
	logger.debug(f"[add_schedule_to_scheduler][D02]: schedule_id:{schedule_id}; userid:{userid}; ip:{ip}; run_mode:{run_mode}; settings:{settings}")

	try:
		
		# Adjust times to datetime objects
		taskTimes = processTaskTimes(start_time, end_time)
		start_dt = datetime.strptime(taskTimes.get('start_time'), "%Y-%m-%d %H:%M")
		end_dt = datetime.strptime(taskTimes.get('end_time'), "%Y-%m-%d %H:%M")

		logger.debug(f"[add_schedule_to_scheduler][D03]: start_dt:{start_dt}:{type(start_dt)}; end_dt:{end_dt}:{type(end_dt)}")

		venv = settings.get('start_venv')
		program = settings.get('start_script')

		# Job 1: Start Job
		for attempt in range(max_retries):
			try:
				params = ['-userid', userid, '-ip', ip, '-operation', 'ON', '-schedule', schedule_id ]
				logger.debug(f"[add_schedule_to_scheduler][D04]: start_time:{start_dt};")
				
				start_trigger = DateTrigger(run_date=start_dt) if run_mode == 'Run-once' else CronTrigger(hour=start_dt.hour, minute=start_dt.minute)
				
				logger.debug(f"[add_schedule_to_scheduler][D11]: start_trigger:{start_trigger}")
				
				scheduler.add_job(
					runScript,
					args=[venv, program, params, 'ON', schedule_id, run_mode],
					trigger=start_trigger,
					id=f'start_job_{schedule_id}',
					jobstore='mariadb',
					replace_existing=True
				)
				logger.debug(f"[add_schedule_to_scheduler][D05]: <Successfully scheduled start job (start_job_{schedule_id}) for schedule ID {schedule_id} on attempt {attempt + 1}.>")
				break
			except Exception as e:
				logger.error(f"[add_schedule_to_scheduler][E01]: <Attempt {attempt + 1} to schedule start job (start_job_{schedule_id}) for schedule ID {schedule_id} failed: {e}>")
				if attempt < max_retries - 1:
					time.sleep(retry_delay)
				else:
					raise

		# Job 2: Interval Job
		# Adjust boundaries to exclude the first and last minutes
		
		taskTimes = processTaskTimes((start_time + timedelta(minutes=1)), (end_time - timedelta(minutes=1)))
		adjusted_start = datetime.strptime(taskTimes.get('start_time'), "%Y-%m-%d %H:%M")
		adjusted_end   = datetime.strptime(taskTimes.get('end_time'), "%Y-%m-%d %H:%M")
	
		logger.debug(f"[add_schedule_to_scheduler][D06]: adjusted_start:{adjusted_start}{type(adjusted_start)}; adjusted_end:{adjusted_end}{type(adjusted_end)}")

		# Only schedule if the adjusted boundaries allow for valid intervals
		if adjusted_start <= adjusted_end:
			for attempt in range(max_retries):
				try:
					params = ['-userid', userid, '-ip', ip, '-operation', 'AUTO', '-schedule', schedule_id ]
				
					# Use CronTrigger to handle intervals at 00 and 30 minutes
					interval_trigger = CronTrigger(
						minute='0,10,20,30,40,50',
						#minute='0,30',
						start_date=adjusted_start,
						end_date=adjusted_end
					)
					
					logger.debug(f"[add_schedule_to_scheduler][D12]: interval_trigger:{interval_trigger}")
				
					scheduler.add_job(
						runScript,
						args=[venv, program, params, 'AUTO', schedule_id, run_mode],
						trigger=interval_trigger,
						id=f'interval_job_{schedule_id}',  # Single ID for the interval job
						jobstore='mariadb',
						replace_existing=True
					)
					logger.debug(f"[add_schedule_to_scheduler][D07]: <Successfully scheduled interval job (interval_job_{schedule_id}) for schedule ID {schedule_id} from {adjusted_start} to {adjusted_end} on attempt {attempt + 1}.>")
					break  # Exit retry loop on success
				except Exception as e:
					logger.error(f"[add_schedule_to_scheduler][E02]: <Attempt {attempt + 1} to schedule interval job (interval_job_{schedule_id}) for schedule ID {schedule_id} failed: {e}>")
					if attempt < max_retries - 1:
						time.sleep(retry_delay)
					else:
						raise


		# Job 3: End Job
		for attempt in range(max_retries):
			try:
				
				logger.debug(f"[add_schedule_to_scheduler][D08]: end_time:{end_dt}")
				params = ['-userid', userid, '-ip', ip, '-operation', 'OFF', '-schedule', schedule_id ]
				
				end_trigger = DateTrigger(run_date=end_dt) if run_mode == 'Run-once' else CronTrigger(hour=end_dt.hour, minute=end_dt.minute)
				
				logger.debug(f"[add_schedule_to_scheduler][D13]: end_trigger:{end_trigger}")
				
				scheduler.add_job(
					runScript,
					args=[venv, program, params, 'OFF', schedule_id, run_mode],
					trigger=end_trigger,
					id=f'end_job_{schedule_id}',
					jobstore='mariadb',
					replace_existing=True
				)
				logger.debug(f"[add_schedule_to_scheduler][D09]: <Successfully scheduled end job (end_job_{schedule_id}) for schedule ID {schedule_id} on attempt {attempt + 1}.>")
				break
			except Exception as e:
				logger.error(f"[add_schedule_to_scheduler][E03]: <Attempt {attempt + 1} to schedule end job (end_job_{schedule_id}) for schedule ID {schedule_id} failed: {e}>")
				if attempt < max_retries - 1:
					time.sleep(retry_delay)
				else:
					raise

		# Update status to Scheduled
		updateStatus(schedule_id, 'Scheduled')
		logger.debug(f"[add_schedule_to_scheduler][D10]: <Schedule ID {schedule_id} status updated to 'Scheduled'.>")

	except Exception as e:
		logger.error(f"[add_schedule_to_scheduler][E04]: <Failed to add schedule ID {schedule_id} to scheduler after {max_retries} attempts: {e}>")

	finally:
		logger.info("[add_schedule_to_scheduler][I02]: OUT")



# Completed
def remove_schedule_from_scheduler(schedule_id, max_retries=3, retry_delay=2):

	# This function is used to remove all schedule's subtask with retry logic
	# RETURN: None

	logger.info(f"[remove_schedule_from_scheduler][I01]: IN")
	logger.debug(f"[remove_schedule_from_scheduler][D01]: schedule_id:{schedule_id};")

	"""Remove related start and end jobs from the APScheduler with retry logic."""
	job_ids = [f"start_job_{schedule_id}", f"interval_job_{schedule_id}", f"end_job_{schedule_id}"]	 # Job IDs to look for

	logging:debug(f"[remove_schedule_from_scheduler][D02]: job_ids:{job_ids};")

	for job_id in job_ids:
		for attempt in range(1, max_retries + 1):
			try:
				# Step 1: Check if the job exists using APScheduler's get_job()
				job = scheduler.get_job(job_id)

				if job:
					# Step 2: If the job exists, remove it
					scheduler.remove_job(job_id)
					logger.debug(f"[remove_schedule_from_scheduler][D03]: <Successfully removed job {job_id} for schedule ID {schedule_id}.>")
					break  # Exit retry loop on success
				else:
					logger.warning(f"[remove_schedule_from_scheduler][W01]: <Job {job_id} for schedule ID {schedule_id} not found.>")
					break  # No need to retry if job doesn't exist

			except Exception as e:
				logger.error(f"[remove_schedule_from_scheduler][E01]: Attempt {attempt} to remove job {job_id} failed: {e}>")
				if attempt < max_retries:
					logger.debug(f"[remove_schedule_from_scheduler][D04]: <Retrying in {retry_delay} seconds...>")
					time.sleep(retry_delay)
				else:
					logger.error(f"[remove_schedule_from_scheduler][ED02]: <Failed to remove job {job_id} after {max_retries} attempts.>")

	logger.debug(f"[remove_schedule_from_scheduler][D05]: <Job removal process completed for schedule ID {schedule_id}.>")
	logger.info("[remove_schedule_from_scheduler][I02]: OUT")



def deleteDevices():
	
	# This function is used to remove all schedule's subtask with the devices already removed
	# RETURN: None

	logger.info(f"[deleteDevices][I01]: IN")
	
	try:
		conn = connect_with_retry()
		cursor = conn.cursor(pymysql.cursors.DictCursor)  # Use pymysql cursor for dictionary results
		cursor.execute("SELECT schedule_id FROM deleteDevices")
		schedules = cursor.fetchall()
		
		logger.debug(f"[deleteDevices][D01]: schedules:{schedules}; len(schedules):{len(schedules)}")

		if schedules:
			for schedule in schedules:
				
				schedule_id = schedule.get('schedule_id')
				
				logger.debug(f"[deleteDevices][D02]: schedule_id:{schedule_id}")
				
				remove_schedule_from_scheduler(schedule_id)
				
				cursor.execute("DELETE FROM deleteDevices WHERE schedule_id = %s", (schedule_id,))
				conn.commit()
				logger.debug(f"[deleteDevices][D03]: <All schedule's sub-tasks removed [{schedule_id}]>")
				
		else:
			logger.debug(f"[main][D04]: <No deleted device schedule found>")
	finally:
		if conn.open:
			conn.close()
		logger.info(f"[deleteDevices][I02]: OUT")
		


##########################################################################

def main():

	logger.info(F"------>  ")
	logger.info(F"------>  Scheduler started  ---")
	logger.info(f"------>  {SYSTEM_NAME} . Version {SYSTEM_VER}	 <------")
	logger.info(f"------>  Last Updated: {datetime.fromtimestamp(os.path.getmtime(__file__))}  <------")
	logger.info(F"------>  ")

	logger.info("[main][I01]: IN")

	if DEVELOPER_MODE == 1:
		logger.info(f"------>  ")
		logger.info(f"------>  ~ ~ ~ ~ ~ ~	 D E V E L O P E R	 M O D E   ~ ~ ~ ~ ~ ~ ")
		logger.info(f"------>  ")
		
		dataSync_onLoad()
		
		logger.info(f"------>  ")
		logger.info(f"------>  ~ ~ ~ ~ ~ ~	 D E V E L O P E R	 M O D E   E n d e d   ~ ~ ~ ~ ~ ~ ")
		logger.info(f"------>  ")
		
		exit()
		
		

	#  Main Function
	#


	##############################
	##	Development Settings:
	##
	
	DEVELOPER_COUNT = 0
	
	##
	##	Development Settings End
	##############################

		
	if DEVELOPER_MODE == 0:
		#  Load the dataSync and dataMart Programs
		logger.debug("[main][D02]: <Loading dataSync and dataMart into scheduler>")
		dataSync_onLoad()
		dataSync_load()
		dataMart_load()
		getUsages_load()


	logger.debug("[main][D03]: <Starting infinite loop until receiving Keyboard Interrupt>")

	"""Main function to start the scheduler and polling loop."""
	while True:
		
		##########################################
		##	DEVELOPMENT MODE control mechanism	##
		##
		if DEVELOPER_MODE == 1:
			logger.debug(f"[main][D04]: DEVELOPER_COUNT:{DEVELOPER_COUNT}")
			if DEVELOPER_COUNT == 1:
				logger.debug("[main][D05]: <DEVELOPMENT QUIT>")
				break
		##########################################

		logger.info(f"[main][I02]: ------>")
		logger.info(f"[main][I03]: ------>")

		logger.debug("[main][D06]: <Fetching schedules>")
		# Fetch schedules and handle them
		# SELECT schedule_id, userid, ip, start_time, end_time, run_mode, status FROM schedules where status='Pending' or status='Deleting' or status='Disabling'or status='Forcing_On' or status='Forcing_Off'
		schedules = fetch_schedules()

		logger.debug(f"[main][D07]: Schedule:{schedules}; len(schedules):{len(schedules)}")

		
		########################################
		##	Trigger by Schedules
		##	
		for schedule in schedules:
			# Extract schedule details
			#schedule_id, userid, ip, start_time, end_time, start_script, start_venv, end_script, end_venv, run_mode, status
			schedule_id = schedule.get('schedule_id')
			userid = schedule.get('userid')
			ip = schedule.get('ip')
			start_time = schedule.get('start_time')
			end_time = schedule.get('end_time')
			start_script = schedule.get('start_script')
			start_venv = schedule.get('start_venv')
			end_script = schedule.get('end_script')
			end_venv = schedule.get('end_venv')
			run_mode = schedule.get('run_mode')
			status = schedule.get('status')

			logger.debug(f"[main][D08]: schedule_id:{schedule_id}; userid:{userid}; ip:{ip}; start_time:{start_time}; end_time:{end_time}; start_script:{start_script} start_venv:{start_venv}; end_script:{end_script}; end_venv:{end_venv}; run_mode:{run_mode}; status:{status}")

			if status == 'Pending':
				logger.debug(f"[main][D09]: <Adding schedule ID {schedule_id} to the scheduler.>")
				add_schedule_to_scheduler(schedule)

			elif status == 'Disabling':
				logger.debug(f"[main][D10]: <Disabling schedule ID {schedule_id}.>")
				remove_schedule_from_scheduler(schedule_id)
				updateStatus(schedule_id, 'Disabled')

			elif status == 'Deleting':
				logger.debug(f"[main][D11]: <Deleting schedule ID {schedule_id}.>")
				remove_schedule_from_scheduler(schedule_id)

				try:
					conn = connect_with_retry()
					cursor = conn.cursor()
					cursor.execute("DELETE FROM schedules WHERE schedule_id = %s", (schedule_id,))
					conn.commit()
					logger.debug(f"[main][D12]: <Deleted schedule ID {schedule_id} from the database.>")
				finally:
						if conn.open:
							conn.close()

			elif status == 'Forcing_On':

				logger.debug(f"[main][D13]: <Force to turn On Device>")

				# Run processRunner --> Trigger ON

				#  Get Execution Settings
				settings = rtnExecutionSetting(ip)
				params = ['-userid', userid, '-ip', ip, '-operation', 'F_ON']

				result = processRunner(settings.get('start_venv'), settings.get('start_script'), params)

				# delete schedule ID directly
				try:
					conn = connect_with_retry()
					cursor = conn.cursor()
					cursor.execute("DELETE FROM schedules WHERE schedule_id = %s", (schedule_id,))
					conn.commit()
					logger.debug(f"[main][D14]: <Deleted schedule ID {schedule_id} from the database.>")

				finally:
						if conn.open:
							conn.close()

			elif status == 'Forcing_Off':

				logger.debug(f"[main][D15]: <Force to turn OFF Device>")

				# Run processRunner --> Trigger OFF

				#  Get Execution Settings
				settings = rtnExecutionSetting(ip)
				params = ['-userid', userid, '-ip', ip, '-operation', 'F_OFF']

				result = processRunner(settings.get('start_venv'), settings.get('start_script'), params)

				# delete schedule ID directly
				try:
					conn = connect_with_retry()
					cursor = conn.cursor()
					cursor.execute("DELETE FROM schedules WHERE schedule_id = %s", (schedule_id,))
					conn.commit()
					logger.debug(f"[main][D16]: <Deleted schedule ID {schedule_id} from the database.>")

				finally:
						if conn.open:
							conn.close()


		########################################################
		##	Removing schedule's job because of device removal
		
		deleteDevices()
		
		logger.debug(f"[main][D17]: <Update all devices status and info.>")

		# Force to update all devices status in order to ensure proper status kept in database


		if DEVELOPER_MODE == 1:
			DEVELOPER_COUNT+=1
			logger.debug(f"[main][D18]: DEVELOPER_COUNT:{DEVELOPER_COUNT}")
		
		logger.info(f"[main][I04]: <Waiting for {SLEEP_DURATION} seconds for next polling.>")
		logger.info(f"[main][I05]: ------>")
		logger.info(f"[main][I06]: ------>")
		time.sleep(SLEEP_DURATION)	# Wait before checking again
	
	logger.info("[main][I07]: OUT")



if __name__ == "__main__":

	scheduler.start()
		
	try:
		main()
	except (KeyboardInterrupt, SystemExit):
		scheduler.shutdown()
		logger.info("---  Scheduler stopped	 ---")


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
'''

'''


