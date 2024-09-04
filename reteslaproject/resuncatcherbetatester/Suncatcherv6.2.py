import sys
import requests
import ast
import datetime
import time
import teslapy
import json

def tesla_plugged_in():
    global cardata
    global vehicles
    success = 0
    while (success == 0):
        with teslapy.Tesla('<<< Email Used For Tesla Account >>>') as tesla:
            try:
                vehicles = tesla.vehicle_list()
            except:
                print("Get vehicle-list failed.")
                time.sleep(3)
                continue
            try:
                vehicles[0].sync_wake_up()
            except:
                print("Vehicle wake_up failed.")
                time.sleep(3)
                continue
            try:
                cardata = vehicles[0].get_vehicle_data()
            except:
                print("Get Vehicle Data Failed.")
                time.sleep(3)
                continue
            try:
                lat_raw = cardata['drive_state']['latitude']
                success = 1
            except:
                time.sleep(3)
                continue
    longitude_raw = cardata['drive_state']['longitude']
    plug_status = cardata['charge_state']['charge_port_door_open']
    odometer = cardata['vehicle_state']['odometer']
    odometer_short = round(odometer, 1)
    
    if (lat_home - .0006) <= lat_raw <= (lat_home + .0006) and (long_home - .0006) <= longitude_raw <= (long_home + .0006):
        at_home = "At Home"
    else:
        at_home = "Not At Home"
    if plug_status:
        tpi = "Plugged In"
    else:
        tpi = "Not Plugged In"
    return at_home, tpi, odometer_short

def get_meter_reading():
    success = 0
    while success == 0:
        x = open('commands.xml', 'r').read()  # Commands to be processed by the Eagle-200
        url = "http://<<< Local IP Address For Eagle-200 >>>/cgi-bin/post_manager"  # Location of the Eagle-200
        HEADERS = {'Content-type': 'multi-part/form-data',
                    'Authorization': 'Basic MDA2NmIwOjEwY2IxN2M0NmQyNmM2ZDU='}
        try:
            r = requests.post(url, data=x, headers=HEADERS)
        except:
            print("Couldn't get meter data. Sleeping & retrying.....")
            time.sleep(3)
        try:
            structure = ast.literal_eval(r.text)
        except:
            print("Meter read error.")
            time.sleep(3)
        try:
            meter_now = float(structure['Device']['Components']['Component']['Variables']['Variable']['Value'])
            success = 1
        except:
            print("Can't read meter json data.")
            time.sleep(3)
    return meter_now

def offpeak():
    now = datetime.datetime.now()
    now_hour = now.hour
    today = now.weekday()
    if (peak_start <= now_hour < peak_end) and (0 <= today <= 4):
        offpeak = "Peak"
    else:
        offpeak = "Off-Peak"
    return offpeak

def charging_status():
    success = 0
    while (success == 0):
        if cardata['charge_state']['charging_state'] == "Charging":
            currently_charging = "Charging"
            current_amps = int(cardata['charge_state']['charge_amps'])
        else:
            currently_charging = "Not Charging"
            current_amps = 0
        charge_level = cardata['charge_state']['battery_level']
        charge_limit = cardata['charge_state']['charge_limit_soc']
        success = 1
    return currently_charging, current_amps, charge_level, charge_limit

def start_charging():
    success = 0
    while (success == 0):
        with teslapy.Tesla('<<< Email Used For Tesla Account >>>') as tesla:
            try:
                vehicles = tesla.vehicle_list()
                vehicles[0].sync_wake_up()
                vehicles[0].command('START_CHARGE')
                success = 1
            except:
                time.sleep(3)
                continue
    return

def stop_charging():
    success = 0
    while (success == 0):
        with teslapy.Tesla('<<< Email Used For Tesla Account >>>') as tesla:
            try:
                vehicles = tesla.vehicle_list()
                vehicles[0].sync_wake_up()
                vehicles[0].command('STOP_CHARGE')
                success = 1
            except:
                time.sleep(3)
                continue
    return

def set_charging_rate(amps):
    success = 0
    while (success == 0):
        with teslapy.Tesla('<<< Email Used For Tesla Account >>>') as tesla:
            try:
                vehicles = tesla.vehicle_list()
                vehicles[0].sync_wake_up()
                vehicles[0].command('CHARGING_AMPS', charging_amps=amps)
                success = 1
            except:
                time.sleep(3)
                continue     
    return


def solar():
    api_key = '<<< SolarEdge API Key >>>'
    site_id = '<<< SolarEdge Site ID>>>'
    solaredge = 'https://monitoringapi.solaredge.com/%20site/' + site_id + '/overview.json?api_key=' + api_key
    success = 0
    while success == 0:
        try:
            json_data = requests.get(solaredge).json()
            success = 1
        except:
            time.sleep(3)
            continue
    global resultK_short

    class solaredge():
        @staticmethod
        def solardata():
            lastupdatetime = json_data['overview']['lastUpdateTime']
            totalenergythisyear = json_data['overview']['lifeTimeData']['energy'] / 1000
            lastyearenergy = json_data['overview']['lastYearData']['energy'] / 1000
            lastmonthenergy = json_data['overview']['lastMonthData']['energy'] / 1000
            lastdayenergy = json_data['overview']['lastDayData']['energy'] / 1000
            currentpower = json_data['overview']['currentPower']['power']
            productiontoday = json_data['overview']
            return {'lastupdatetime': lastupdatetime, 'totalenergythisyear': totalenergythisyear,
                    'lastyearenergy': lastyearenergy, 'lastmonthenergy': lastmonthenergy,
                    'lastdayenergy': lastdayenergy, 'currentpower': currentpower, 'productiontoday': productiontoday}

    result = solaredge.solardata()
    resultK = result['currentpower'] / 1000
    resultK_short = round(resultK, 2)
    powertoday = result['lastdayenergy']
    power_so_far = result['productiontoday']
    return powertoday, power_so_far


def write_log(meter, namps, rate, status, odo, soc, solar_added, total_solar_today):
    today = time.strftime("%m/%d/%Y")
    thisinstant = datetime.datetime.now()
    tod = thisinstant.strftime("%H:%M")
    with open(("/home/pi/Desktop/Tesla/SuncatcherLog.csv"), "a") as f:
        f.write("%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n" % (today, tod, rate, status, meter, namps, odo, soc, solar_added, total_solar_today))
    return

def write_teslastatus(loc,cable,batt,stat,amps):
    with open(("/home/pi/Desktop/Tesla/teslastatus.json"),"w") as f:
        f.write("{\n   \"Location\": \"%s\",\n   \"Charging Cable\": \"%s\",\n   \"Battery Level\": %s,\n   \"Status\": \"%s\",\n   \"Amps\": %s\n}" % (loc,cable,batt,stat,amps))
    return

def get_sccontrol():
    f = open('/home/pi/Desktop/Tesla/sccontrol.json')
    data = json.load(f)
    minnight = data["MinNight"]
    maxday = data["MaxDay"]
    pausesc = data["PauseSC"]
    return minnight,maxday,pausesc

# <<< The next section contains a number of parameters that should be reviewed.  lat_home and long_home must be set
# <<< Also note if sunrise_hour, sunset_hour, peak_start and peak_end are set appropriately
#   Adjustable Program Settings
min_night_charge = 50       # Battery % car is to be charged to at night - using energy from grid.
max_day_battery_level = 70  # Maximum battery % to be charged to using solar during the day.
#lat_home = ##.####          # Car's latitude when parked at user's home
#long_home = ##.####         # Car's longitude when parked at user's home
peak_start = 17             # Hour peak electric pricing begins (24 hour clock)
peak_end = 21               # Hour peak electric pricing ends (24 hour clock)
meter_threshold = .240      # Meter Instantaneous Deman needs to be larger than this value - in either direction - to warrant a change in car charging rate.  Value of .240 represents 1 Amp change on 240V circuit
sunrise_hour = 6
sunset_hour = 17
seconds_to_wait = 180
counter = 0
prev_meter_reading = 0
last_meter_action = 0
fn = time.strftime("%b%d%G")
print("\n")
charge_start = 0
charge_end = 0
odometer_start = 0
odometer_end = 0
today = time.strftime("%b %d, %G")
at_home, tpi, odometer_short = tesla_plugged_in()
currently_charging, current_amps, charge_level, charge_limit = charging_status()


while(1):
    now = datetime.datetime.now()
    now_hour = now.hour
    current_rate = offpeak()

    day_offpeak_count = 0
    kwh_hours_added = 0
    #
    # Loop for daytime; Off-Peak
    #
    while (sunrise_hour <= now_hour < sunset_hour) and current_rate == "Off-Peak":
        min_night_charge, max_day_battery_level, pause_sc = get_sccontrol()
        day_offpeak_count = day_offpeak_count + 1
        at_home, tpi, odometer_short = tesla_plugged_in()
        currently_charging, current_amps, charge_level, charge_limit = charging_status()
        current_meter = get_meter_reading()
        incremental_amps = round(current_meter * -1000 / 245)
        new_amps = current_amps + incremental_amps
        powertoday, power_so_far = solar()
        wait_seconds = 600
        if (at_home == "At Home") and (tpi == "Plugged In"):
            if charge_level < charge_limit:
                wait_seconds = 600
                if charge_level < max_day_battery_level:
                    if currently_charging == "Charging":
                        if new_amps > 0:
                            ## Change amperage setting
                            inc_kwh = round(((current_amps * 240 * 1.1) / 1000 * wait_seconds / 3600), 2)
                            print("%s Charging @ %s amps. Meter: %s Battery level: %s Max daytime battery: %s Changing amps to %s" % (time.ctime(), current_amps, current_meter, charge_level, max_day_battery_level, new_amps))
                            set_charging_rate(new_amps)
                            write_log(current_meter,new_amps,current_rate,currently_charging,odometer_short,charge_level,inc_kwh,powertoday)
                            write_teslastatus(at_home,tpi,charge_level,currently_charging,new_amps)
                        else:
                            ## Stop Charging
                            stop_charging()
                            inc_kwh = round(((current_amps * 240 * 1.1) / 1000 * wait_seconds / 3600), 2)
                            print("%s Charging. Current Amps: %s Meter: %s  Pulling from grid. Pulling from grid. Stopping charing." % (time.ctime(),current_amps,current_meter))
                            write_log(current_meter, 0, current_rate,"Stopping Charging",odometer_short,charge_level,inc_kwh,powertoday)
                            write_teslastatus(at_home,tpi,charge_level,"Not Charging",0)
                    else:
                        if new_amps > 3:
                            ## Start charging; set amperage to nww amps
                            print("%s Not charging. Meter: %s Battery level: %s Max daytime battery: %s Starting charging @ %s amps." % (time.ctime(), current_meter, charge_level, max_day_battery_level, new_amps))
                            start_charging()
                            set_charging_rate(new_amps)
                            write_log(current_meter, new_amps, current_rate,"Starting Charging",odometer_short,charge_level,0,powertoday)
                            write_teslastatus(at_home,tpi,charge_level,"Charging",new_amps)

                        else:
                            print("%s Not charging. Meter: %s  Making no changes." % (time.ctime(),current_meter))
                            write_log(current_meter, 0, current_rate,"Not Charging",odometer_short,charge_level,0,powertoday)
                            write_teslastatus(at_home,tpi,charge_level,currently_charging,0)
                else:
                    if currently_charging == "Charging":
                        ## Stop charging
                        inc_kwh = round(((current_amps * 240 * 1.1) / 1000 * wait_seconds / 3600), 2)
                        print("%s Charging @ %s amps. Meter: %s Battery level: %s Max daytime battery: %s Stopping charging. Total kWh today = %s" % (time.ctime(), current_amps, current_meter, charge_level, max_day_battery_level, kwh_hours_added))
                        stop_charging()
                        write_log(current_meter, 0, current_rate,"Stopping Charging",odometer_short,charge_level,inc_kwh,powertoday)
                        write_teslastatus(at_home,tpi,charge_level,"Not Charging",0)
                    else:
                        ## Do nothing.  Max daytime charge level reached.
                        print("%s Not charging. Charge level: %s Max Day Charge: %s At or above daytime limit." % (time.ctime(),charge_level,max_day_battery_level))
                        write_log(current_meter, 0, current_rate,"Not Charging",odometer_short,charge_level,0,powertoday)
                        write_teslastatus(at_home,tpi,charge_level,"Not Charging",0) 
            else:
                if currently_charging == "Charging":
                    inc_kwh = round(((current_amps * 240 * 1.1) / 1000 * wait_seconds / 3600), 2)
                    stop_charging()
                    print("%s Charging. At or above charge limit. Stopping charging." % time.ctime())
                    write_log(current_meter, 0, current_rate, "Stopping Charging", odometer_short, charge_level, inc_kwh, powertoday)
                    write_teslastatus(at_home,tpi,charge_level,"Not Charging",0)
                else:
                    print("%s Not charging. At or above charge limit. Making no changes." % (time.ctime()))
                    write_log(current_meter, 0, current_rate, "Not Charging", odometer_short, charge_level, 0, powertoday)
                    write_teslastatus(at_home,tpi,charge_level,"Not Charging",0)
        else:
            ## Car not at home
            print("%s Car is: %s Charging cable is: %s  Car not chargeable" % (time.ctime(), at_home, tpi))
            write_log(current_meter, 0, current_rate, "Not Chargeable", odometer_short, charge_level, 0, powertoday)
            write_teslastatus(at_home,tpi,charge_level,"Not Charging",0)
        time.sleep(wait_seconds)
        now = datetime.datetime.now()
        now_hour = now.hour
        current_rate = offpeak()
    #
    # Loop for being in Peak Pricing
    #
    now = datetime.datetime.now()
    now_hour = now.hour
    current_rate = offpeak()
    current_meter = 0
    while current_rate == "Peak":
        last_meter = current_meter
        current_meter = get_meter_reading()
        powertoday, power_so_far = solar()
        if abs(current_meter - last_meter) > .5:
            at_home, tpi, odometer_short = tesla_plugged_in()
            currently_charging, current_amps, charge_level, charge_limit = charging_status()
            if at_home == "At Home" and tpi == "Plugged In":
                if currently_charging == "Charging":
                    ## Stop charging
                    print("%s Charging @ %s amps.In peak pricing. Stopping charging." % (time.ctime(), current_amps))
                    stop_charging()
                    write_log(current_meter, 0, current_rate, "Stopping Charging", odometer_short, charge_level, 0,powertoday)

                else:
                    ## In peak.  Not charging.  Don't change anything.
                    print("%s In peak pricing. Not charging. Making no changes." % time.ctime())
                    write_log(current_meter, 0, current_rate, "Not Charging", odometer_short, charge_level, 0,powertoday)
            else:
                ##  During Peak.  Car not at home or not plugged in.
                print("%s In peak pricing. Car not home or not plugged in." % time.ctime())
                write_log(current_meter, 0, current_rate, "Not Chargeable", odometer_short, charge_level, 0, powertoday)

        else:
            print("%s No major change in consumption." % time.ctime())
            powertoday, power_so_far = solar()
            write_log(current_meter,0,current_rate,"Not Charging","9999999","9999999",0,powertoday)
        write_teslastatus(at_home,tpi,charge_level,"Not Charging",0)
        time.sleep(60)
        now = datetime.datetime.now()
        now_hour = now.hour
        current_rate = offpeak()

    #
    # Loop for late night / overnight
    #
    now = datetime.datetime.now()
    now_hour = now.hour
    current_rate = offpeak()
    home_for_the_night = 0

    while (now_hour >= sunset_hour or now_hour < sunrise_hour) and current_rate == "Off-Peak":
        at_home, tpi,odometer_short = tesla_plugged_in()
        min_night_charge, max_day_battery_level, pause_sc = get_sccontrol()
        currently_charging, current_amps, charge_level, charge_limit = charging_status()
        current_meter = get_meter_reading()
        powertoday, power_so_far = solar()
        if at_home == "At Home" and tpi == "Plugged In" and charge_level < min_night_charge:
            current_meter = get_meter_reading()
            if currently_charging == "Not Charging":
                ## Start charging at 32 amps
                print("%s Nighttime. Car is: %s Charging cable is: %s  Battery level: %s. Min night charge level: %s Starting charging." % (time.ctime(), at_home, tpi, charge_level, min_night_charge))
                start_charging()
                new_amps = 32
                set_charging_rate(new_amps)
                delta_percent = min_night_charge - charge_level
                kwh_needed = delta_percent * .75
                wait_seconds = (kwh_needed/8)*60*60
                write_log(current_meter, 0, current_rate, "Starting Charging", odometer_short, charge_level, 0, powertoday)
                write_teslastatus(at_home,tpi,charge_level,"Charging",32)
            else:
                ## Charging.  Make sure charge rate is maxed.
                if current_amps < 32:
                    new_amps = 32
                    set_charging_rate(new_amps)
                print("%s Nighttime. Charging @ %s amps. Battery level: %s Min night charge: %s. Changing amps to 32." % (time.ctime(), current_amps, charge_level, min_night_charge))
                wait_seconds = 300
                write_log(current_meter, 0, current_rate, "Charging", odometer_short, charge_level, 0,powertoday)
                write_teslastatus(at_home,tpi,charge_level,"Charging",32)
        else:
            if currently_charging == "Charging":
                print("%s Nighttime. Charging. Battery: %s Min Night Charge: %s Stopping charging." % (time.ctime(),charge_level,min_night_charge))
                stop_charging()
                write_log(current_meter, 0, current_rate, "Stopping Charging", odometer_short, charge_level, 0, powertoday)
                write_teslastatus(at_home,tpi,charge_level,"Not Charging",0)
            wait_seconds = 1200
            print("%s Nighttime. %s. %s." % (time.ctime(),at_home,tpi))
            write_log(current_meter, 0, current_rate, "Not Chargeable", odometer_short, charge_level, 0, powertoday)
        time.sleep(wait_seconds)
        now = datetime.datetime.now()
        now_hour = now.hour






