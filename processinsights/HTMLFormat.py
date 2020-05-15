

def addheader(hstr):
    hstr+='<head>\r\n'
    return hstr
    
def addstyle(hstr):
    hstr+='<style>\r\n' + \
        'table, th, td { border-collapse: separate; border-spacing: 2px;}\r\n' + \
        'th, td {text-align: left;}\r\n' + \
        '</style>\r\n'
    return hstr

def closeheader(hstr):
    hstr+='</head>\r\n'
    return hstr

def addbody(hstr):
    hstr+='<Body>\r\n'
    return hstr

def addTitle(hstr, datetime):
    hstr+='<br><br><h2>Status on {datetime}</h2><br><br>'.format(datetime=datetime)
    return hstr

def addtableheader(hstr):
    hstr+= '<table>\n' + \
        '<tr>\n' + \
        '<th>ID</th>\n' + \
        '<th>Process</th>\n' + \
        '<th>Start Time</th>\n' + \
        '<th>End Time</th>\n' + \
        '<th>Actual Exec Time(min)</th>\n' + \
        '<th>Avg Exec Time(min)</th>\n' + \
        '<th>Records Affected</th>\n' + \
        '<th>Avg Exec Count</th>\n' + \
        '<th>Run Status</th>\n' + \
        '<th>Time Status</th>\n' + \
        '<th>Count Status</th>\n' + \
        '<th>Exec Status</th>\n' + \
        '<th>Alert</th>\n' + \
        '</tr>\n'
    return hstr

def addtablerow(hstr, vlist, Alert=False):
    s=''
    for v in vlist:
        s+='<td>' + str(v) + '</td>\n'
    if Alert is True:
        hstr+='<tr style="background-color:LightCoral">\n' + s + '</tr>\n'
    else:
        hstr+='<tr>\n' + s + '</tr>\n'
    return hstr
        
def closetable(hstr):
    hstr+='</table>\n'
    return hstr

def closebody(hstr):
    hstr+='</body>\n'
    return hstr


def GenerateHTML(df, datetime:str): 
    hstr='<html>\n'
    hstr = addheader(hstr)
    hstr = addstyle(hstr)
    hstr = closeheader(hstr)
    hstr = addbody(hstr)
    hstr = addTitle(hstr,datetime)
    hstr = addtableheader(hstr)
    Alist=''
    for row in df.itertuples():
        if row[12] is True:
            hstr = addtablerow(hstr, row, True)
            Alist+=row[1] + '\n'
        else:
            hstr = addtablerow(hstr, row, False)
    hstr = closetable(hstr)
    hstr = closebody(hstr)
    hstr+='</html>'
    return hstr, Alist
