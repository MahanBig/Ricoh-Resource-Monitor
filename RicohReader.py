import pprint
import webbrowser
import os
import emoji
import tkinter as tk
from tkinter import ttk
from puresnmp import walk, get

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller. Found on stackoverflow """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def  myWalk(IP, OID):
    """ Creates a list of StringVar from walk result """
    results=[]
    for row in walk(IP, 'public', OID):
        newResult=tk.StringVar()
        if type(row[1])==bytes:
            value=row[1].decode('utf=8')
        else:
            value=row[1]
        newResult.set(value)
        results.append(newResult)
    if len(results)==0:
        newResult=tk.StringVar()
        newResult.set('')
        results.append(newResult)
    return results

def mySet(varList, walkResults, index):
    """ Updates a list of StringVars with new values, accounting for possible change in list length """
    if len(varList[index])>len(walkResults):
        for i in range(len(varList[index])-len(walkResults)):
            newEntry=tk.StringVar()
            newEntry.set('')
            walkResults.append(newEntry)
    elif len(varList[index])<len(walkResults):
        for i in range(len(walkResults)-len(varList[index])):
            newEntry=tk.StringVar()
            newEntry.set('')
            varList[index].append(newEntry)
    if type(varList[index])==list:
        for q,item in enumerate(varList[index]):
            varList[index][q].set(walkResults[q].get())
    elif type(varList[index])==dict:
        for q,item in enumerate(varList[index]):
            varList[index][item].set(walkResults[q].get())
    return varList

def imgGet(string, printers, index):
    """ Returns proper image name from Model OID and presence of LCT """
    check=0
    if string == 'MP C6004ex':
        return c6004ex
    elif string == 'MP C3504ex':
        return c3504ex
    elif string == 'MP C6503':
        for i,tray in enumerate(printers[index]['Trays']):
            if list(tray.keys())[0] == 'LCT':
                check=1
                return  c6503f
        if check!=1:
            return c6503
            
printers=[
          {'IP':'172.18.181.227','Name':'CI-121'},
          {'IP':'172.18.166.19','Name':'CI202-L'},
          {'IP':'172.18.166.92','Name':'CI202-R'},
          #{'IP':'172.18.181.232','Name':'CI-214'},
          #{'IP':'172.18.181.244','Name':'CI-301'},
          {'IP':'172.18.181.231','Name':'CI-335'},
          #{'IP':'172.18.181.230','Name':'CI-DO'},
          {'IP':'172.18.178.120','Name':'SDW-FL2'},
          {'IP':'172.18.177.204','Name':'ANX-A'},
          {'IP':'172.19.55.10','Name':'ANX-B'},
          #{'IP':'172.18.186.18','Name':'RH-204'},
          ]

ModelOID = '.1.3.6.1.2.1.43.5.1.1.16.1'
SerialOID = '.1.3.6.1.2.1.43.5.1.1.17.1'
InkNames_baseOID = '.1.3.6.1.2.1.43.11.1.1.6'
InkLevels_baseOID = '.1.3.6.1.2.1.43.11.1.1.9.1'
TrayNames_baseOID = '.1.3.6.1.2.1.43.8.2.1.13'
TrayMaxCap_baseOID = '.1.3.6.1.2.1.43.8.2.1.9.1'
TrayCurrCap_baseOID = '.1.3.6.1.2.1.43.8.2.1.10.1'
Err_baseOID = '.1.3.6.1.2.1.43.18.1.1.8.1'

root=tk.Tk()
root.title('Ricoh Resource Monitor')
root.iconbitmap(resource_path('icon.ico'))

s=ttk.Style()
s.theme_use('alt')
s.configure('black.Horizontal.TProgressbar', background='black')
s.configure('cyan.Horizontal.TProgressbar', background='cyan')
s.configure('magenta.Horizontal.TProgressbar', background='magenta')
s.configure('yellow.Horizontal.TProgressbar', background='yellow')

#Create a list of styles to iterate through later
styles=['black.Horizontal.TProgressbar',
        'cyan.Horizontal.TProgressbar',
        'magenta.Horizontal.TProgressbar',
        'yellow.Horizontal.TProgressbar',]

c3504ex = tk.PhotoImage(file=resource_path('c3504ex.png')).subsample(4, 4)
c6004ex = tk.PhotoImage(file=resource_path('c6004ex.png')).subsample(4, 4)
c6503 = tk.PhotoImage(file=resource_path('c6503.png')).subsample(4, 4)
c6503f = tk.PhotoImage(file=resource_path('c6503f.png')).subsample(4, 4)

#Define the main index value early so I can define localReload outside of the loop
i=0

#Create the master lists of StringVars. These are the value that will be updated upon a reload
alertVarsList=[]
inkVarsList=[]
currTrayVarsList=[]

localReload=lambda i=i:(mySet(alertVarsList, myWalk(printers[i]['IP'], Err_baseOID),i ),
                          mySet(inkVarsList, myWalk(printers[i]['IP'], InkLevels_baseOID),i ),
                          mySet(currTrayVarsList, myWalk(printers[i]['IP'], TrayCurrCap_baseOID),i ))

for i,item in enumerate(printers):
    #Begin gathering information
    printers[i]['Model']=get(printers[i]['IP'], 'public', ModelOID).decode('utf-8')
    
    inkNames=[]
    for row in walk(printers[i]['IP'], 'public', InkNames_baseOID):
        inkNames.append(row[1].decode('utf-8'))  
    Inks=[] #Will hold ink names and current level
    tempInkVarList={}
    for inkIndex in range(len(inkNames)):
        inkLevel=get(printers[i]['IP'], 'public', InkLevels_baseOID+'.'+str(inkIndex+1))
        newInk=tk.StringVar()
        newInk.set(inkLevel)
        tempInkVarList[inkNames[inkIndex]]=newInk
        Inks.append({inkNames[inkIndex]:inkLevel})
    inkVarsList.append(tempInkVarList)
    printers[i]['Inks']=Inks
    
    trayNames=[]
    for row in walk(printers[i]['IP'], 'public', TrayNames_baseOID):
        trayNames.append(row[1].decode('utf-8'))
    Trays=[] #Will hold tray names and current/max paper levels
    tempTrayVarList={}
    for trayIndex in range(len(trayNames)):
        currLevel=get(printers[i]['IP'], 'public', TrayCurrCap_baseOID+'.'+str(trayIndex+1))
        maxLevel=get(printers[i]['IP'], 'public', TrayMaxCap_baseOID+'.'+str(trayIndex+1))
        newTray=tk.StringVar()
        newTray.set(currLevel)
        tempTrayVarList[trayNames[trayIndex]]=newTray
        Trays.append({trayNames[trayIndex]:{'maxLevel':maxLevel,'currLevel':currLevel}})
    currTrayVarsList.append(tempTrayVarList)
    printers[i]['Trays']=Trays
    
    Alerts=[]
    for row in walk(printers[i]['IP'], 'public', Err_baseOID):
        Alerts.append(row[1].decode('utf-8'))
    printers[i]['Alerts']=Alerts
    alertVarsList.append(myWalk(printers[i]['IP'], Err_baseOID))
    
    #Begin drawing frames
    printerFrame = tk.Frame(root, padx=17)
    #printerFrame.grid(row=1, column=i)
    printerFrame.pack(side=tk.LEFT, fill=tk.Y)
    
    Name=tk.Label(printerFrame, text=printers[i]['Name'], font=(None, 14))
    Name.grid(row=0, column=i)
    IP=tk.Label(printerFrame, text=printers[i]['IP'], font=(None, 8))
    IP.grid(row=2, column=i)
    Model=tk.Label(printerFrame, text=printers[i]['Model'], font=(None, 9))
    Model.grid(row=1, column=i)
    
    buttonFrame  = tk.Frame(printerFrame)
    url='http://' + printers[i]['IP'] + '/web/guest/en/websys/webArch/getStatus.cgi'
    linkButton = tk.Button(buttonFrame, text="Link", command=lambda aurl=url:webbrowser.open(aurl))
    linkButton.pack(side=tk.LEFT)
    reloadButton = tk.Button(buttonFrame, text="Reload", command=localReload)
    reloadButton.pack(side=tk.RIGHT)
    buttonFrame.grid(row=3, column=i)

    alertFrame = tk.Frame(printerFrame)
    for item, alert in enumerate(alertVarsList[i]):
        alert = tk.Label(alertFrame, textvariable=alertVarsList[i][item], fg='red')
        alert.pack()
    alertFrame.grid(row=4, column=i)

    printerImageCanvas = tk.Canvas(printerFrame, width=135, height=140)
    printerImageCanvas.grid(row=5, column=i)
    printerImageCanvas.create_image(135, 140, image=imgGet(printers[i]['Model'], printers, i), anchor='se')
    
    inkFrame=tk.Frame(printerFrame)
    counter=0
    for t, ink in enumerate(inkVarsList[i]):
        if t==1:
            #Skip the waste toner 
            continue
        
        Frame=tk.Frame(inkFrame)
        
        Bar=ttk.Progressbar(Frame, variable=inkVarsList[i][ink], style=styles[counter])
        Bar.pack(side=tk.LEFT)
        
        Label=tk.Label(Frame, textvariable=inkVarsList[i][ink], bd=0, width=3)
        percent=tk.Label(Frame, text='%', bd=0)
        percent.pack(side=tk.RIGHT)
        Label.pack(side=tk.RIGHT)
        
        Frame.pack()
        counter+=1
    inkFrame.grid(row=6, column=i)

    trayFrame=tk.Frame(printerFrame)
    for u, tray in enumerate(currTrayVarsList[i]):
        Frame=tk.Frame(trayFrame)

        trayName=tk.Label(Frame, text=list(printers[i]['Trays'][u].keys())[0]+':', anchor='w', width=9)
        trayName.pack(side=tk.LEFT)
        
        trayCurrLevel=tk.Label(Frame, textvariable=currTrayVarsList[i][tray], width=5, anchor='e')
        trayMaxLevel=tk.Label(Frame, text='/ '+str(printers[i]['Trays'][u][tray]['maxLevel']), width=5, anchor='e')
        trayMaxLevel.pack(side=tk.RIGHT)
        trayCurrLevel.pack(side=tk.RIGHT)
        
        Frame.pack()
    trayFrame.grid(row=7, column=i, pady=20)
    
    print("Done: " + printers[i]['Name'])

def masterReload():
    for masterReloadIndex in range(len(printers)):
        mySet(alertVarsList, myWalk(printers[masterReloadIndex]['IP'], Err_baseOID),masterReloadIndex )
        mySet(inkVarsList, myWalk(printers[masterReloadIndex]['IP'], InkLevels_baseOID),masterReloadIndex )
        mySet(currTrayVarsList, myWalk(printers[masterReloadIndex]['IP'], TrayCurrCap_baseOID),masterReloadIndex )

tk.Button(root, text='R\ne\nl\no\na\nd\n\nA\nl\nl', command=masterReload, bg='deep sky blue', activebackground='DeepSkyBlue4').pack(side=tk.RIGHT)
root.mainloop()
