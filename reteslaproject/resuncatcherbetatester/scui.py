import PySimpleGUI as sg
import time
import datetime
import json

def get_tesla_status():
    f = open('/home/pi/Desktop/Tesla/teslastatus.json')
    data = json.load(f)
    location = data["Location"]
    charging_cable = data["Charging Cable"]
    battery_level = data["Battery Level"]
    status = data["Status"]
    amps = data["Amps"]
    return location, charging_cable, battery_level, status, amps

def get_sccontrol():
    f = open('/home/pi/Desktop/Tesla/sccontrol.json')
    data = json.load(f)
    min_night = data['MinNight']
    max_day = data['MaxDay']
    return min_night, max_day


myfont = '("FreeSerif",24)'
mybold = '("FreeSerif",24,"bold")'

frame1 = [[sg.Frame('SunCatcher Control',
         [[sg.Text("Min Nighttime Battery",font=('Arial',24,'bold'))],
         [sg.Slider((0,100),orientation='horizontal', font=('Arial',18,'bold'))],
         [sg.Text("",font=myfont)],
         [sg.Text("Max Daytime Battery",font=('Arial',24,'bold'))],
         [sg.Slider((0,100),orientation='horizontal', font=('Arial',18,'bold'))],
         #[sg.Checkbox("Pause SunCatcher",default=False,font=('Arial',24,'bold'))],
         [sg.Text("")],
         [sg.Button("Apply",font=('Arial',14,'bold'))]])]]


frame2 = [[sg.Frame("Tesla Status",
         [[sg.vtop(sg.Text("Location: ",font=('Arial',20,'bold'))), sg.Text("", key='-LOC-',font=('Arial',18))],
         #[sg.Text("")],
         [sg.Text("Cable: ",font=('Arial',20,'bold')), sg.Text("", key='-CAB-',font=('Arial',18))],
         #[sg.Text("")],
         [sg.Text("Battery: ",font=('Arial',20,'bold')), sg.Text("", key='-BAT-',font=('Arial',18)), sg.Text("%",font=myfont)],
         #[sg.Text("")],
         [sg.Text("Status: ",font=('Arial',20,'bold')), sg.Text("",key='-STA-',font=('Arial',18))],
         #[sg.Text("")],
         [sg.Text("Amps: ",font=('Arial',20,'bold')), sg.Text("",key='-AMP-',font=('Arial',18))],
         [sg.Text("Max Night Battery: ",font=('Arial',20,'bold')), sg.Text("", key='-SL1-', font=('Arial',18)), sg.Text("%",font=myfont)],
         [sg.Text("Max Day Battery: ",font=('Arial',20,'bold')), sg.Text("", key='-SL2-', font=('Arial',18)), sg.Text("%",font=myfont)]])]]
        

#sg.theme('Dark2')

layout = [[sg.Column(frame1,pad=5), sg.Column(frame2,pad=10)]]

# Create the window
window = sg.Window("SunCatcher", layout,size=(800,450),resizable=True, background_color="#020202")

# Create an event loop
while True:
    event, values = window.read(timeout=100)
    # End program if user closes window or
    # presses the OK button
    now = datetime.datetime.now()
    now_second = now.second
    now_minute = now.minute
    number = 20
    if now_second == 0 or now_second == 15 or now_second == 30 or now_second == 45:
        loc,ccable,batlevel,cstatus,camps = get_tesla_status()
        MinNight, MaxDay = get_sccontrol()
        window.Element('-LOC-').update(loc)
        window.Element('-CAB-').update(ccable)
        window.Element('-BAT-').update(batlevel)
        window.Element('-STA-').update(cstatus)
        window.Element('-AMP-').update(camps)
        window.Element('-SL1-').update(MinNight)
        window.Element('-SL2-').update(MaxDay)
    if event == "Apply" or event == sg.WIN_CLOSED:
        max_night = values[0]
        max_day = values[1]
        pause_sc = 'False'
        with open(("/home/pi/Desktop/Tesla/sccontrol.json"), "w") as f:
            f.write("{\n   \"MinNight\":  %s,\n   \"MaxDay\":  %s,\n   \"PauseSC\": \"%s\"\n}\n" % (max_night, max_day, pause_sc))
    
        
window.close()

