import numpy
import math
import os
import json
import datetime
import time
import plotly
import plotly.figure_factory as ff
import plotly.graph_objects as go
from ciphercommon.config import CipherConfig
from ciphercommon.data import CipherData
from azure.servicebus.control_client import ServiceBusService
from azure.servicebus.control_client import Message


def ComputeSummaryStatistics(AppName: str=None,PeriodinMonths: int=1):
    CipherConfig.load('parameters.yaml')

    dbconn = CipherData.byConfig('NexusODS', 'oxyread')
    
    #Get average and maximum execution time over a user specified period   
    SqlOptions = ['(CAST(AVG(CAST(DATEDIFF(SECOND, StartTime, EndTime) as decimal(12,2))/60) as decimal(12,2))) AS Avg_Exec_Time', \
                  '(CAST(MAX(CAST(DATEDIFF(SECOND, StartTime, EndTime) as decimal(12,2))/60) as decimal(12,2))) AS Max_Exec_Time']

    Sqlstr3 = 'select A.ApplicationName,'
    Sqlstr5 = ' from dbo.ExecutionSummary A \
        where A.StartTime > DATEADD(month, -1, GETUTCDATE())'

    SqlstrAvg = Sqlstr3 + str(SqlOptions[0]) + Sqlstr5
    SqlstrMax = Sqlstr3 + str(SqlOptions[1]) + Sqlstr5   

    if AppName is not None:
        Sqlstrx = ' AND A.ApplicationName = ? GROUP BY A.ApplicationName'
        SqlstrAvg+=Sqlstrx
        dfAvg = dbconn.load(SqlstrAvg, params=[AppName])
        SqlstrMax+=Sqlstrx
        dfMax = dbconn.load(SqlstrMax, params=[AppName])
    else:
        Sqlstrx = ' GROUP BY A.ApplicationName ORDER BY A.ApplicationName'
        SqlstrAvg+=Sqlstrx
        dfAvg = dbconn.load(SqlstrAvg)
        SqlstrMax+=Sqlstrx
        dfMax = dbconn.load(SqlstrMax)

    dfAvg['Max_Exec_Time'] = dfMax['Max_Exec_Time'] 
          
    return dfAvg

def YstExecutionSchedule(AppName: str=None, OutPath: str='./output', PlotData: bool=False, When:str=''):

    CipherConfig.load('parameters.yaml')

    dbconn = CipherData.byConfig('NexusODS', 'oxyread')
    
    dfAvg = ComputeSummaryStatistics(AppName=AppName)

    StartDate = datetime.datetime.now().strftime("%Y-%m-%d")

    #TIME_DIFFERENCE = -5
    is_dst = time.localtime().tm_isdst
    TIME_DIFFERENCE = -1.0*time.timezone
    if is_dst > 0:
        TIME_DIFFERENCE+=3600

    lower_limit=-86400 - TIME_DIFFERENCE
    upper_limit = -TIME_DIFFERENCE
   
    if (len(When) != 0):
        StartDate = When
        When = '\'' + When + ' 00:00:00' + '\''
        Sqlstrlimits='WHERE A.StartTime BETWEEN dateadd(ss,{lower_limit} , datediff(dd,0,{When})) AND \
            dateadd(ss, {upper_limit}, datediff(dd,0,{When}))'.format(lower_limit=lower_limit, upper_limit=upper_limit,When=When)
    else:
        StartDate = datetime.datetime.now().strftime("%Y-%m-%d")
        Sqlstrlimits='WHERE A.StartTime BETWEEN dateadd(ss,{lower_limit} ,datediff(dd,0,GETUTCDATE())) AND \
            dateadd(ss, {upper_limit}, datediff(dd,0,GETUTCDATE()))'.format(lower_limit=lower_limit, upper_limit=upper_limit)

    Sqlstr1 = 'SELECT * FROM ( SELECT A.ApplicationName \
    , \'HR\' + CAST(DATEPART(HOUR,A.StartTime) AS NVARCHAR)        StartHr \
    , A.RunStatus + \' : \' + CAST(A.RecordsAffected AS NVARCHAR)  RunStatus \
    FROM dbo.ExecutionSummary A '
    Sqlstr1+=Sqlstrlimits
    
    SqlParameter = ' AND A.ApplicationName = ?' 

    Sqlstr2 = ') SRC\
    PIVOT ( \
    MAX(RunStatus) FOR StartHr IN (HR0,HR1,HR2,HR3,HR4,HR5,HR6,HR7,HR8,HR9,HR10,HR11,HR12,HR13,HR14,HR15,HR16,HR17,HR18,HR19,HR20,HR21,HR22,HR23) \
    ) PVT \
    ORDER BY 1;' 

    if AppName is not None: 
        Sqlstr3 = Sqlstr1 + SqlParameter + Sqlstr2
        df2 = dbconn.load(Sqlstr3, params=[AppName])
    else:    
        Sqlstr3 = Sqlstr1 + Sqlstr2
        df2 = dbconn.load(Sqlstr3)

    actual_ecount = [0]*len(dfAvg.index)
    for rowA in dfAvg.itertuples():
        bFound = False
        for row in df2.itertuples():
            #Check if the Application exists in dfAvg 
            if row[1] == rowA[1]:
                bFound = True
                for i in range(24):
                    if row[i+2] is not None:
                        actual_ecount[rowA[0]]+=1
            else:
                continue
            if bFound is True:
                break 
       
    planned_time = [0]*len(dfAvg.index)
    planned_ecount = [0]*len(dfAvg.index)

    #Read planned tasks from JSON
    with open('./ScheduledTasks.json') as json_data:   
        tasks_dict = json.load(json_data)

    for x in tasks_dict:
        if x['Environment'] == CipherConfig.Environment:
            for row in dfAvg.itertuples():
                if x['ApplicationName'].lower() == row[1].lower():
                    planned_time[row[0]] = 60 * float(x['Interval'])
                    planned_ecount[row[0]] = 24 / int(x['Interval'])
                    break
                else:
                    continue    
    
    dfAvg['Planned_Exec_Time'] = planned_time         #Col 4
    dfAvg['Actual_Exec_Count'] = actual_ecount        #Col 5
    dfAvg['Planned_Exec_Count'] = planned_ecount      #Col 6

    #Detect if the actual count is less than planned cpunt
    bActual = ['False']*len(dfAvg.index)
    for row in dfAvg.itertuples():
        if row[5] < row[6]:
            bActual[row[0]] = 'True'

    dfAvg['Actual Count < Planned Count'] = bActual

    #Write data to CSV file
    if not os.path.exists(OutPath):
        os.mkdir(OutPath)
    FileName = OutPath + '/ExecSummary-' + CipherConfig.Environment + ' ' + StartDate + '.csv'
    CipherData.toCsv(os.path.abspath(FileName), dfAvg)

    fig1 = go.Figure(data=[
    go.Bar(name='Actual', x=dfAvg.ApplicationName, y=dfAvg.Actual_Exec_Count),
    go.Bar(name='Planned', x=dfAvg.ApplicationName, y=dfAvg.Planned_Exec_Count)
    ])

    fig1.update_layout(title = CipherConfig.Environment + ' ' + StartDate, barmode='group')
    if PlotData is True:
        fig1.show()
    fname = './processinsights/static/ExecutionSummary'
    plotly.offline.plot(fig1, filename=fname, auto_open=False)

    TIME_DIFFERENCE = -1.0*time.timezone
    if time.localtime().tm_isdst > 0:
        TIME_DIFFERENCE+=3600

    #Adjust time relative to UTC
    SqlAdjustTime = ' dateadd(ss,{TIME_DIFFERENCE}, A.StartTime) Start , \
    dateadd(ss, {TIME_DIFFERENCE}, A.EndTime) Finish '.format(TIME_DIFFERENCE=TIME_DIFFERENCE)

    Sqlstr6 = 'SELECT A.ApplicationName Task\
    , A.RunStatus + \' : \' + CAST(A.RecordsAffected AS NVARCHAR)  RunStatus,'
    Sqlstr6+=SqlAdjustTime
    Sqlstr6+=', CAST(CAST(DATEDIFF(SECOND, StartTime, EndTime) as decimal(12,2))/60 as decimal(12,2)) ExecTime \
    FROM NexusODS.dbo.ExecutionSummary A '

    Sqlstr6+=Sqlstrlimits
    #Sort the processes 
    SqlstrSort = ' ORDER BY A.ApplicationName'
    Sqlstr6+=SqlstrSort
 
    if AppName is not None:
        Sqlstrx = ' AND A.ApplicationName = ?'
        Sqlstr6+=Sqlstrx
        dfExecSch = dbconn.load(Sqlstr6, params=[AppName])
    else:
        dfExecSch = dbconn.load(Sqlstr6)

    dfExecSch_Save = dfExecSch.copy()
    dfExecSch['Start_Time'] = dfExecSch['Start'].apply(lambda x: x.strftime("%m/%d/%Y, %H:%M:%S"))
    dfExecSch['Finish_Time'] = dfExecSch['Finish'].apply(lambda x: x.strftime("%m/%d/%Y, %H:%M:%S"))
    dfExecSch.drop('Start', axis=1, inplace=True)
    dfExecSch.drop('Finish', axis=1, inplace=True)
    
    if not os.path.exists(OutPath):
        os.mkdir(OutPath)
    FileName = OutPath + '/YstExecSchedule-' + CipherConfig.Environment + ' ' + StartDate + '.csv'
    CipherData.toCsv(os.path.abspath(os.path.abspath(FileName)), dfExecSch)

    hover = ['Exec Time/Max Time(min)=']*len(dfExecSch_Save.index)
    for row in dfExecSch_Save.itertuples():
        hover[row[0]]+=str(row[5]) + '/NA'
        for row1 in dfAvg.itertuples():
            if row[1].lower() == row1[1].lower():
                hover[row[0]]=hover[row[0]][:-2]
                hover[row[0]]+=str(row1[3])
                break
            else:
                continue
    
    dfExecSch_Save['Description'] = hover
        
    #Create dictionary for Gantt chart
    dfExecSch_Save.drop('RunStatus', axis=1, inplace=True)
    dfExecSch_Save.drop('ExecTime', axis=1, inplace=True)

        
    fig1 = ff.create_gantt(dfExecSch_Save, height = 1000, width = 2000, bar_width=0.2, showgrid_x=True, showgrid_y=True, group_tasks=True)

    fig1.update_layout(title = CipherConfig.Environment + ' ' + StartDate)
    if PlotData is True:
        fig1.show()
    fname = './processinsights/static/ExecutionSchedule'
    plotly.offline.plot(fig1, filename=fname, auto_open=False)

    return

def GetLastHourProcessData():

    CipherConfig.load('parameters.yaml')

    dbconn = CipherData.byConfig('NexusODS', 'oxyread')
    
    TIME_DIFFERENCE = -1.0*time.timezone
    if time.localtime().tm_isdst > 0:
        TIME_DIFFERENCE+=3600
    
    Sqlstr1 = 'SELECT A.ApplicationName, \
    convert(varchar, DATEADD(HOUR, -5, A.StartTime), 108) AS StartTime, \
    convert(varchar, DATEADD(HOUR, -5, A.EndTime), 108) AS EndTime,   \
    CAST((CAST(DATEDIFF(SECOND, A.StartTime, A.EndTime) as decimal(12,2))/60) as decimal(12,2)) AS ActualExecTime, \
    B.AvgExecTime, \
    B.ExecTimeTolerPct, \
    B.MinAllowableTime, \
    A.RecordsAffected, \
    B.AvgExecCount, \
    B.ExecCountTolerPct, \
    B.MinAllowableCount, \
    A.RunStatus, \
    B.ReportBadStatus, \
    B.SendMailTo'   
    
    Sqlstr2 = ' FROM dbo.ExecutionSummary A, dbo.ExecutionSummaryConfig B \
        WHERE A.ApplicationName = B.ApplicationName AND \
        A.EndTime BETWEEN DATEADD(hour, (DATEDIFF(hour, 0, GETUTCDATE())-1), 0) AND DATEADD(hour, DATEDIFF(hour, 0, GETUTCDATE()), 0) \
        ORDER BY A.ApplicationName'

    Sqlstr3 = Sqlstr1 + Sqlstr2

    dfExecSch = dbconn.load(Sqlstr3)
    #Detect Alerts in the dataset
    #index=0,ApplicationName=1,StartTime=2,EndTime=3,ActualExecTime=4,AvgExecTime=5,ExecTimeTolerPct=6,MinAllowableTime=7,RecordsAffected=8,AvgExecCount=9,
    #ExecCountTolerPct=10,MinAllowableCount=11,RunStatus=12,ReportBadStatus=13, SendMailTo=14,TimeStatus=15,CountStatus=16,ExecStatus=17,Alert=18
    TimeStatus = ['']*len(dfExecSch.index)
    CountStatus = ['']*len(dfExecSch.index)
    ExecStatus = ['']*len(dfExecSch.index)
    RaiseAlert=[False]*len(dfExecSch.index)

    for row in dfExecSch.itertuples():
        if row.ActualExecTime > row.MinAllowableTime:
            val = 100*(row.ActualExecTime-row.AvgExecTime)/row.AvgExecTime
            if val > row.ExecTimeTolerPct:
                TimeStatus[row[0]] = 'HI'
                RaiseAlert[row[0]] = True
            elif val < -row.ExecTimeTolerPct:
                TimeStatus[row[0]] = 'LO'
                RaiseAlert[row[0]] = True
        if row.RecordsAffected > row.MinAllowableCount:
            val = 100*(row.RecordsAffected-row.AvgExecCount)/row.AvgExecCount
            if val > row.ExecCountTolerPct:
                CountStatus[row[0]] = 'HI'
                RaiseAlert[row[0]] = True
            elif val < -row.ExecCountTolerPct:
                CountStatus[row[0]] = 'LO' 
                RaiseAlert[row[0]] = True
        if row.RunStatus.lower() != 'Good'.lower() and row.ReportBadStatus == 1:
            ExecStatus[row[0]]='ERROR'
            RaiseAlert[row[0]] = True
                    
    dfExecSch['TimeStatus']=TimeStatus
    dfExecSch['CountStatus']=CountStatus
    dfExecSch['ExecStatus']=ExecStatus
    dfExecSch['Alert']=RaiseAlert
    
    'Create list of mail addresses'   
    EMails = []
    for row in dfExecSch.itertuples():
        if row.SendMailTo is not None:
            lst = row.SendMailTo.split(';')
            for s in lst:
                bFound = False
                for sm in EMails:
                    if s.lower() == sm.lower():
                        bFound = True
                        break
                if(bFound is False):
                    EMails.append(s)

    PList = []
    for sm in EMails:
        lst = []
        for row in dfExecSch.itertuples():
            if row.SendMailTo is not None:
                if sm in row.SendMailTo and row.Alert is True:
                    lst.append(row[1]) 
        if len(lst) > 0:               
            PList.append(lst)
   
    #Sort the rows
    new_order = list(range(len(dfExecSch.index)))
    ix=0
    for row in dfExecSch.itertuples():
        if row.Alert is True:
            tmp = new_order[row[0]]
            new_order[row[0]] = ix
            new_order[new_order.index(ix)]=tmp
            ix = ix + 1
    dfExecSch['new']=new_order   
    dfExecSch_sorted = dfExecSch.sort_values('new').drop('new', axis=1)
    dfExecSch_sorted.drop(['ExecTimeTolerPct','MinAllowableTime','ExecCountTolerPct', \
    'MinAllowableCount','ReportBadStatus','SendMailTo'], axis=1,inplace=True)
    dfExecSch_sorted.reset_index(drop=True, inplace = True)

    return EMails, PList, dfExecSch_sorted

def GetProcessRunStatus(dfExecStatus): 

    CipherConfig.load('parameters.yaml')

    dbconn = CipherData.byConfig('NexusODS', 'oxyread')

    Sqlstr1 = 'SELECT DATEADD(hour, (DATEDIFF(hour, 0, GETUTCDATE())-1), 0) AS StartTime'
    df = dbconn.load(Sqlstr1)
    start_secs = (df['StartTime'].dt.hour*60 + df['StartTime'].dt.minute)*60 + df['StartTime'].dt.second

    Sqlstr1 = 'SELECT DATEADD(hour, DATEDIFF(hour, 0, GETUTCDATE()), 0) AS EndTime'
    df = dbconn.load(Sqlstr1)
    end_secs = (df['EndTime'].dt.hour*60 + df['EndTime'].dt.minute)*60 + df['EndTime'].dt.second
   
    Sqlstr1 = 'SELECT ApplicationName, TaskStartTime, TaskInterval from dbo.ExecutionSummaryConfig'
    df = dbconn.load(Sqlstr1)
    
    Execlist = dfExecStatus['ApplicationName'].tolist()
    Applist=[]
    for row in df.itertuples():
        secs = (row[2].hour*60 + row[2].minute)*60 + row[2].second
        while(True):
            if(secs < int(end_secs)):
                if(secs >= int(start_secs)):
                    for app in Execlist:
                        if(app.lower() == row[1].lower()):
                            Exists = True
                            break
                    if(Exists is False):
                        Applist.append(row[1])  
                    break
                secs+=row[3]*3600
            else:
                break
    return Applist                
                                
def SendNotification(EMail, PList, dt1, strlink):
    config = CipherConfig.load('parameters.yaml')
    Bus_settings = config['Notification']['AzureMessageBus']
    MessageBody_settings = config['Notification']['MessageBody']
    if Bus_settings['SharedAccessKeyValue'] != None and \
    Bus_settings['ServiceNamespace'] != None:
        Address_list = [EMail]
        ServiceNameSpace = Bus_settings['ServiceNamespace']
        sbs = ServiceBusService(ServiceNameSpace,
                                shared_access_key_name = Bus_settings['SharedAccessKeyName'],
                                shared_access_key_value = Bus_settings['SharedAccessKeyValue'] ) 
        message = {
            'EmailType' : 0,
            'Subject' : 'Status on ' + dt1,
            'FromAddress' : MessageBody_settings['FromAddress'],
            'ReplyTo' : '',
            'FromName' : MessageBody_settings['FromName'] + ' ' + CipherConfig.Country + '-' + CipherConfig.Environment,
            'ToAddresses' : Address_list,
            'Message' : 'Processes completed with Alert(s) in the last hour\n\n' + PList + strlink,
            'CcAddresses': [],
            'BccAddresses': [],
            'Metadata': {
                "TaskName": "This is a test message"}
            }

        json = CipherData.toJson(message)
        msg = Message(json)
        sbs.send_queue_message(Bus_settings['QueueName'], msg)    
    return





