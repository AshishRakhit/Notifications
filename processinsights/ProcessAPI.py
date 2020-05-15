from flask import Flask, Blueprint, send_from_directory
from processinsights.ExecutionSchedule import YstExecutionSchedule

process_api = Blueprint('process_api', __name__)

def createapp():

    app = Flask(__name__)

    @process_api.route('/')
    def RunMain():
        return send_from_directory('./static','MainPage.html')
        

    @process_api.route('/Schedule/<sDate>')
    def RunSchedule(sDate):
        YstExecutionSchedule(When=sDate)
        return send_from_directory('./static','ExecutionSchedule.html')

    @process_api.route('/Summary/<sDate>')
    def RunSummary(sDate):
        YstExecutionSchedule(When=sDate)
        return send_from_directory('./static','ExecutionSummary.html')

    @process_api.route('/ProcessStatus')
    def GetProcessStatus():
        return send_from_directory('./static','ProcessRunStatus.html')

    app.register_blueprint(process_api)
    return app