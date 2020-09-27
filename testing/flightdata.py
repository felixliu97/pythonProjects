from revoscalepy import RxComputeContext, RxInSqlServer, RxSqlServerData
from revoscalepy import rx_lin_mod, rx_predict, rx_summary
from revoscalepy import RxOptions, rx_import

import os

def test_linmod_sql():
	sql_server = os.getenv('PYTEST_SQL_SERVER', '.')

	sql_connection_string = 'Driver=SQL Server;Server=' + sqlServer + ';Database=sqlpy;Trusted_Connection=True;'
	print("connectionString={0!s}".format(sql_connection_string))

	data_source = RxSqlServerData(
		sql_query = "select top 10 * from airlinedemosmall",
		connection_string = sql_connection_string,

		column_info = {
			"ArrDelay" : { "type" : "integer" },
			"DayOfWeek" : {
				"type" : "factor",
				"levels" : [ "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday" ]
			}
		})

	sql_compute_context = RxInSqlServer(
		connection_string = sql_connection_string,
		num_tasks = 4,
		auto_cleanup = False
		)

	#
	# Run linmod locally
	#
	linmod_local = rx_lin_mod("ArrDelay ~ DayOfWeek", data = data_source)
	#
	# Run linmod remotely
	#
	linmod = rx_lin_mod("ArrDelay ~ DayOfWeek", data = data_source, compute_context = sql_compute_context)

	# Predict results
	# 
	predict = rx_predict(linmod, data = rx_import(input_data = data_source))
	summary = rx_summary("ArrDelay ~ DayOfWeek", data = data_source, compute_context = sql_compute_context)