from ciphercommon.config import CipherConfig
import socket
import datetime    
import processinsights.ExecutionSchedule as ExecutionSchedule
import processinsights.HTMLFormat as HTMLFormat

def main():
    config = CipherConfig.load('parameters.yaml')
    websettings = config['WebServer']
    # Retrieve records
    Emails, PList, df = ExecutionSchedule.GetLastHourProcessData()

    #Output data in HTML format
    currenthr = datetime.datetime.now().hour
    dt = datetime.datetime.now().strftime("%m-%d-%Y")

    dt1 = dt + '@'+ str(currenthr) + ':00:00'
    #dt2 = 'Status' + '_' + dt + '_' + str(currenthr) + '00.html'
    if currenthr < 10:
        dt1 = dt + '@'+ '0'+ str(currenthr) + ':00:00'
        #dt2 = 'Status' + '_' + dt + '_' + '0' + str(currenthr) + '00.html'

    dt2 = 'ProcessRunStatus.html'
    s, AList = HTMLFormat.GenerateHTML(df, dt1)
    
    with open('.\\processinsights\\static\\'+dt2, "w") as file:
        file.write(s)
        file.close()
        
    if len(Emails) > 0:
        siteurl = 'http://' + socket.gethostbyname(socket.gethostname()) + ':' + str(websettings['Port'])
        if websettings['Site'] != None:
            siteurl = 'http://' + str(websettings['Site']) + ':' + str(websettings['Port'])

        strlink = '\nUse link for latest updates\n' + siteurl + '/ProcessStatus' + '\n'          
        strlink+= '\nUse link to view planned and actual process scheduling summary\n' + siteurl
            
        for i in range(len(Emails)):        
            if len(PList) > 0:
                Applist = ''
                for s in PList[i]:
                    Applist+=s + '\n'
                ExecutionSchedule.SendNotification(Emails[i], Applist, dt1, strlink)

    return
       
if __name__ == '__main__':
    # execute only if run as the entry point into the program
    main()    
    
        
        

                                    
                                                
    
