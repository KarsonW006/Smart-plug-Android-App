'''
	Program: dataMart.py  [aka dataMart_v8.py] [Old Name: forecast.py]
	
	Objective: 
		- Feed data into forecasting model for processing
		- Save the forecast data into table


	usage:	dataMart.py


	Dependency: 
		- pip install pandas
		- pip install prophet
		- pip install SQLAlchemy
		- pip install pymysql


	Version: 20241225_v001 [Released]
	
	
	Changelog:
		- 20241107_v000		--> Initial Version. Using Python-prophet
		- 20241115_v000		--> [Change] Fixing unstable database server issue (Connection V2)
		- 20241215_v000		--> [Change] Adding Debug Info
		- 20241225_v001		--> Initial Version 2.  Project directory structural revamp

	
	Functions List:
		def create_db_connection():
		def fetch_data(view_name):
		def forecast_data(df, periods, freq):
		def convert_to_datetime(df, date_col, freq):
		def delete_all_records(table_name):
		def insert_forecast_data(forecast_df, forecast_type):
		def main():
		
		
	Remark:
		For Deployment:
			1. Update Version number
			2. Set the Indicator from '[Developing]'/'[Pre-Released]' to '[Released]'
			3. Ensure ChangeLog is correct
			4. Copy from Sandbox to Production by eliminating '_vX' suffix
			
'''	   

import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy import text
from sqlalchemy import inspect
from prophet import Prophet
from datetime import datetime
from datetime import datetime
import logging
from logging.handlers import TimedRotatingFileHandler
import time
import os

# Database connection parameters
user = 'YOUR_DATABASE_USER'
password = 'YOUR_DB_PASSWORD'
host = 'YOUR_DATABASE_HOST'
database = 'YOUR_DATABASE_NAME'

# Constants
MAX_RETRIES = 5	 # Maximum number of retries for database connection
RETRY_DELAY = 5	 # Delay in seconds between retries
SLEEP_DURATION = 60		# Time to sleep in seconds
BACKOFF_TIME = 60		# Seconds to wait between retries after an error
MAX_BACKUP_FILES = 7	# Number of backups to retain


SYSTEM_NAME = 'dataMart [Series.2]'
SYSTEM_VER = '20241225_v001'
DEVELOPER_MODE = 0			#  Developer mode: ON (1) | OFF (0)
ENVIRONMENT = "Sandbox" if "Sandbox" in os.path.abspath(os.path.dirname(__file__)) else "Production"


# Set log level: use logging.INFO for production and logging.DEBUG for development
LOG_LEVEL = logging.DEBUG  if "Sandbox" in os.path.abspath(os.path.dirname(__file__)) else logging.INFO 

# Configure logging
log_handler = TimedRotatingFileHandler(
	"./Sandbox/smartProject/.logs/dataMart.log" if ENVIRONMENT == 'Sandbox' else "./Production/smartProject/.logs/dataMart.log",
	when="midnight",		  # Rotate at midnight every day
	interval=1,				   # Every 1 day
	backupCount=MAX_BACKUP_FILES			   # Keep logs for the last 7 days
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

# Create logger instance
logger = logging.getLogger(__name__)




# Step 1: Set up the database connection
def create_db_connection():
	
	#  This function is used to make database connection
	#  Return: None
	
	logger.info("[create_db_connection][I01]: IN")
	
	#  Creates a SQLAlchemy engine with retry logic for database connection readiness."""
	connection_string = f'mysql+pymysql://{user}:{password}@{host}/{database}'
	retries = 0
	engine = None
	
	while retries < MAX_RETRIES:
		try:
			# Try to create the SQLAlchemy engine and connect
			engine = create_engine(connection_string)
			# Attempt to execute a simple query to confirm connection
			with engine.connect() as connection:
				connection.execute(text("SELECT 1"))
			print("Database connection established.")
			logger.debug("[create_db_connection][D01]: <Database connection established>")
			logger.info("[create_db_connection][I02]: OUT")
			return engine
		except Exception as e:
			logger.error(f"[create_db_connection][E01]: <Database connection failed: {e}. Retrying in {RETRY_DELAY} seconds>")
			retries += 1
			time.sleep(RETRY_DELAY)
	logger.critical("[create_db_connection][C01]: <Failed to establish database connection after multiple attempts>")
	raise ConnectionError("Failed to establish database connection after multiple attempts.")
	logger.debug("[create_db_connection][I03]: OUT]")



# Step 2: Fetch data from the database
def fetch_data(view_name):
	
	#  This function is used to fetch data from the database 
	#  Return: df (data object)
	
	logger.info(f"[fetch_data][I01]: IN")
	logger.debug(f"[fetch_data][D01]: view_name:{view_name}>")
	
	engine = create_db_connection() 
	query = f"SELECT * FROM {view_name}"
	
	logger.debug(f"[fetch_data][D02]: <SELECT * FROM {view_name}>")
	
	df = pd.read_sql(query, con=engine)
	engine.dispose()
	logger.debug(f"[fetch_data][D03]: <Fetched {len(df)} rows from {view_name}>")
	logger.debug(f"[fetch_data][D04]: df:{df};")
	logger.info(f"[fetch_data][I02]: OUT")
	return df
	


# Step 3: Forecast data using Prophet
def forecast_data(df, periods, freq):
	
	#  This function is used to make forecast by using the data model 'Prophet'
	#  Return: forecast (data object)
	
	logger.info(f"[forecast_data][I01]: IN")
	logger.debug(f"[forecast_data][D01]: df:{df}; periods:{periods}; freq:{freq};")
	logger.debug(f"[forecast_data][D02]: <Forecasting data with {periods} periods, frequency: {freq}>")
	
	model = Prophet()  # Initialize the Prophet model
	model.fit(df[['ds', 'y']])	# Fit the model to the data
	
	future = model.make_future_dataframe(periods=periods, freq=freq)  # Create a future dataframe
	forecast = model.predict(future)  # Generate forecast
	
	logger.debug(f"[forecast_data][D03]: <Forecasting complete. {len(forecast)} data points predicted>")
	logger.debug(f"[forecast_data][D04]: forecast:{forecast}")
	logger.info(f"[forecast_data][I02]: OUT;")
	
	return forecast 
	


# Function to convert to datetime
def convert_to_datetime(df, date_col, freq):
	
	#  This function is used to convert data to datetime 
	#  Return: df (data object)
	
	logger.info(f"[convert_to_datetime][I01]: IN")
	logger.debug(f"[convert_to_datetime][D01]: df:{df}; date_col:{date_col}; freq:{freq}")
	
	if freq == 'M':
		df['ds'] = pd.to_datetime(df[date_col])
		
	elif freq == 'Q':
		# Extract the year and quarter from the format YYYY-Qn
		df['ds'] = df[date_col].apply(
			lambda x: pd.Timestamp(year=int(x.split('-')[0]), month=int(x.split('-')[1][1]) * 3 - 2, day=1)
		)
	
	logger.debug(f'[convert_to_datetime[D02]: {df.rename(columns={"avg_inc_vat": "y"})}')
	logger.info("[convert_to_datetime][I02]: OUT")

	return df.rename(columns={"avg_inc_vat": "y"})



# Delete all old records in table 'forecasted_prices'
def delete_all_records(table_name):

	#  This function is used to delete all existing records in the table 'forecast_prices'
	#  Return: None
	
	logger.info(f"[delete_all_records][I01]: IN")
	logger.debug(f"[delete_all_records][D01]: table_name:{table_name}>")
	logger.debug(f"[delete_all_records][D02]: <Deleting all records from table {table_name}>")
	
	engine = create_db_connection()
	with engine.connect() as connection:
		connection.execute(text(f"DELETE FROM {table_name}"))
		connection.commit()	 # Ensure changes are committed if using a transactional database
	engine.dispose()
	
	logger.debug(f"[delete_all_records][D03]: <All records from {table_name} deleted>")
	logger.info(f"[delete_all_records][I02]: OUT")



# Step 6: Insert forecast results into the database
def insert_forecast_data(forecast_df, forecast_type):
	
	#  This function is used to insert processed forecast results into the database
	#  Return: None
	
	logger.info(f"[insert_forecast_data][I01]: IN")
	logger.debug(f"[insert_forecast_data][D01]: forecast_df:{forecast_df}; forecast_type:{forecast_type}")
	logger.debug(f"[insert_forecast_data][D02]: <Inserting forecast data of type '{forecast_type}' into database>")
	
	engine = create_db_connection()
	
	# Prepare the data for insertion
	forecast_df = forecast_df[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].copy()
	forecast_df['forecast_type'] = forecast_type
	forecast_df['created_at'] = datetime.now()	# Record insertion time

	# Rename columns to match the target table
	forecast_df.rename(columns={
		'ds': 'forecast_date',
		'yhat': 'forecast_price',
		'yhat_lower': 'forecast_price_lower',
		'yhat_upper': 'forecast_price_upper'
	}, inplace=True)

	# Insert into the `forecasted_prices` table
	forecast_df.to_sql('forecasted_prices', con=engine, if_exists='append', index=False)

	engine.dispose()
	logger.info(f"[insert_forecast_data][D03]: <Forecast data of type '{forecast_type}' inserted into the database>")
	logger.debug("[insert_forecast_data][I02]: OUT")



# Step 5: Main function to execute the program
def main():
	
	logger.info(f"------>  ")
	logger.info("------>  dataMart Started  <------")
	logger.info(f"------>  {SYSTEM_NAME} . Version {SYSTEM_VER}  <------")
	logger.info(f"------>  Last Updated: {datetime.fromtimestamp(os.path.getmtime(__file__))}  <------")
	logger.info(f"------>  ")

	logger.info("[main][I01]: IN")


	if DEVELOPER_MODE == 1:
		logger.info(f"------>  ")
		logger.info(f"------>  ~ ~ ~ ~ ~ ~   D E V E L O P E R   M O D E   ~ ~ ~ ~ ~ ~ ")
		logger.info(f"------>  ")
		
		
		print(f"ENVIRONMENT:{ENVIRONMENT}")
		
		logger.info(f"------>  ")
		logger.info(f"------>  ~ ~ ~ ~ ~ ~   D E V E L O P E R   M O D E   E n d e d   ~ ~ ~ ~ ~ ~ ")
		logger.info(f"------>  ")
		
		exit()
		

	try:
		# Fetch data from views (ensure you have created these views in your database)
			monthly_df = fetch_data('_dm_monthly_price_series')
			quarterly_df = fetch_data('_dm_quarterly_price_series')
			
			# Ensure 'ds' column is in datetime format
			monthly_df['ds'] = pd.to_datetime(monthly_df['month_start'])
			quarterly_df['ds'] = pd.to_datetime(quarterly_df['quarter_start'])
			
			# Convert data for Prophet
			monthly_df = convert_to_datetime(monthly_df, 'month_start', 'ME')
			quarterly_df = convert_to_datetime(quarterly_df, 'quarter_start', 'QE')
			
			# Rename the average price column to 'y'
			monthly_df.rename(columns={'avg_inc_vat': 'y'}, inplace=True)
			quarterly_df.rename(columns={'avg_inc_vat': 'y'}, inplace=True)
			
			# Forecast next 12 months, 4 quarters, and 5 years
			monthly_forecast = forecast_data(monthly_df, periods=36, freq='ME')
			quarterly_forecast = forecast_data(quarterly_df, periods=12, freq='QE')
			
			# Insert forecast data into the database
			delete_all_records('forecasted_prices')
			insert_forecast_data(monthly_forecast, 'monthly')
			insert_forecast_data(quarterly_forecast, 'quarterly')

	except Exception as e:
		logger.error(f"[main][E01]: <An error occurred: {e}>")
	finally:
		logger.info("[main][I02]: IN")
		logger.info("---  dataMart Ended  ---")

if __name__ == "__main__":
	main()
