from flask import Flask, current_app, Blueprint, send_from_directory
from processinsights.ExecutionSchedule import YstExecutionSchedule

process_api = Blueprint('process_api', __name__)

def createapp():
	
	app = Flask(__name__)

	@process_api.route('/')
	def RunMain():
		#return current_app.send_static_file('MainPage.html')
		#return 'Hello_World'
		return send_from_directory('./static','MainPage.html')
		
	@process_api.route('/Schedule/<sDate>')
	def RunSchedule(sDate):
		#return 'Hello_World'
		YstExecutionSchedule(When=sDate)
		#return current_app.send_static_file('ExecutionSchedule.html')
		return send_from_directory('./static','ExecutionSchedule.html')
		

	@process_api.route('/Summary/<sDate>')
	def RunSummary(sDate):
		#return 'Hello_World'
		YstExecutionSchedule(When=sDate)
		#return current_app.send_static_file('ExecutionSummary.html')
		return send_from_directory('./static','ExecutionSummary.html')
		
	@process_api.route('/ProcessStatus')
	def GetProcessStatus():
		#return current_app.send_static_file('./ProcessRunStatus.html')
		return send_from_directory('./static','ProcessRunStatus.html')
		
	app.register_blueprint(process_api)
	return app