from flask import Flask, current_app
import os
from ciphercommon.config import CipherConfig
from ciphercommon.data import CipherData
import processinsights.ExecutionSchedule as ExecutionSchedule

app = Flask(__name__)

@app.route('/')
def RunMain():
    return current_app.send_static_file('MainPage.html')

@app.route('/Schedule/<sDate>')
def RunSchedule(sDate):
    ExecutionSchedule.YstExecutionSchedule(When=sDate)
    return current_app.send_static_file('ExecutionSchedule.html')

@app.route('/Summary/<sDate>')
def RunSummary(sDate):
    ExecutionSchedule.YstExecutionSchedule(When=sDate)
    return current_app.send_static_file('ExecutionSummary.html')

@app.route('/ProcessStatus')
def GetProcessStatus():
    return current_app.send_static_file('ProcessRunStatus.html')

if __name__ == '__main__':
    config = CipherConfig.load('parameters.yaml')
    websettings = config['WebServer']
    app.run(host='0.0.0.0', port=websettings['Port'])



