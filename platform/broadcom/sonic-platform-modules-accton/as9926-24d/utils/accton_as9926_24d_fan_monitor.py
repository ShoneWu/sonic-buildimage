#!/usr/bin/env python

try:
    import os
    import sys
    import syslog
    import signal
    import time
    import glob

except ImportError as e:
    raise ImportError('%s - required module not found' % str(e))

SLEEP_TIME = 10 # Loop interval in second.
DEVICE_SHUTDOWN_PATH = "/sys/bus/i2c/devices/19-0068/shutdown"
DEBUG_MODE = False

FAN_NUM_MAX = 6
FAN_REAR_BASE_OFFSET = 10
FAN_PREFIX_PATH    = "/sys/bus/i2c/devices/17-0066/fan%d_%s"
FAN_PRESENT_NODE   = "present"
FAN_FRONT_RPM_NODE = "front_speed_rpm"
FAN_REAR_RPM_NODE  = "rear_speed_rpm"
FAN_DIRECTION_NODE = "direction"
FAN_FAULT_NODE     = "fault"

FAN_DUTY_CYCLE_PERCENTAGE_PATH = "/sys/bus/i2c/devices/17-0066/fan_duty_cycle_percentage"
FAN_PERCENTAGE_MIN = 50
FAN_PERCENTAGE_MID = 75
FAN_PERCENTAGE_MAX = 100

THERMAL_NUM_MAX = 10
THERMAL_SENSOR_PATH =["/sys/devices/platform/coretemp.0/hwmon/hwmon*/temp*_input",
                        "/sys/bus/i2c/devices/18-0048/hwmon/hwmon*/temp1_input",
                        "/sys/bus/i2c/devices/18-0049/hwmon/hwmon*/temp1_input",
                        "/sys/bus/i2c/devices/18-004a/hwmon/hwmon*/temp1_input",
                        "/sys/bus/i2c/devices/18-004b/hwmon/hwmon*/temp1_input",
                        "/sys/bus/i2c/devices/18-004c/hwmon/hwmon*/temp1_input",
                        "/sys/bus/i2c/devices/18-004c/hwmon/hwmon*/temp2_input",
                        "/sys/bus/i2c/devices/18-004d/hwmon/hwmon*/temp1_input",
                        "/sys/bus/i2c/devices/18-004e/hwmon/hwmon*/temp1_input",
                        "/sys/bus/i2c/devices/18-004f/hwmon/hwmon*/temp1_input"]

tid = 0
tA  = 1
tB  = 2
tC  = 3
tD  = 4
tSd = 5

temp_sensor_threshold = {tid: 2, tA: 57000, tB: 52000, tC: 62000, tD: 79000, tSd: 84000}, {tid: 3, tA: 57000, tB: 52000, tC: 63000, tD: 83000, tSd: 88000}

FUNCTION_NAME = 'fan-control'
PRODUCT_NAME  = 'AS9926-24D'

LOG_EMERG     = 0       #  system is unusable
LOG_ALERT     = 1       #  action must be taken immediately
LOG_CRIT      = 2       #  critical conditions
LOG_ERR       = 3       #  error conditions
LOG_WARNING   = 4       #  warning conditions
LOG_NOTICE    = 5       #  normal but significant condition
LOG_INFO      = 6       #  informational
LOG_DEBUG     = 7       #  debug-level messages

priority_name = {
    LOG_CRIT    : "critical",
    LOG_DEBUG   : "debug",
    LOG_WARNING : "warning",
    LOG_INFO    : "info",
}

def SYS_LOG(level, msg):
    syslog.syslog(level, msg)

def DBG_LOG(msg):
    if DEBUG_MODE:
        level = syslog.LOG_DEBUG
        x = PRODUCT_NAME + ' ' + priority_name[level].upper() + ' : ' + msg
        SYS_LOG(level, x)

def SYS_LOG_INFO(msg):
    level = syslog.LOG_INFO
    x = PRODUCT_NAME + ' ' + priority_name[level].upper() + ' : ' + msg
    SYS_LOG(level, x)

def SYS_LOG_WARN(msg):
    level = syslog.LOG_WARNING
    x = PRODUCT_NAME + ' ' + priority_name[level].upper() + ' : ' + msg
    SYS_LOG(level, x)

def SYS_LOG_CRITICAL(msg):
    level = syslog.LOG_CRIT
    x = PRODUCT_NAME + ' ' + priority_name[level].upper() + ' : ' + msg
    SYS_LOG(level, x)

def getstatusoutput(cmd):
    if sys.version_info.major == 2:
        # python2
        import commands
        return commands.getstatusoutput( cmd )
    else:
        # python3
        import subprocess
        return subprocess.getstatusoutput( cmd )

def shutdown_device():
    ret, output = getstatusoutput("echo 1 > %s" % DEVICE_SHUTDOWN_PATH)
    try:
        if ret != 0:
            # Fail to shutdown device
            SYS_LOG_CRITICAL('fail to shutdown the device')
            return False
    except Exception as e:
        DBG_LOG(repr(e))
        return False

    return True

def set_fan_duty(duty):
    # Valid the target duty
    duty = min(duty, FAN_PERCENTAGE_MAX)
    duty = max(duty, FAN_PERCENTAGE_MIN)

    ret, output = getstatusoutput("echo %d > %s" % (duty, FAN_DUTY_CYCLE_PERCENTAGE_PATH))
    try:
        if ret != 0:
            # Fail to set fan duty
            SYS_LOG_CRITICAL('fail to set fan duty cycle percentage')
            return False
    except Exception as e:
        DBG_LOG(repr(e))
        return False

    return True

def get_fan_duty():
    ret, output = getstatusoutput("cat "+FAN_DUTY_CYCLE_PERCENTAGE_PATH)
    try:
        fanduty = int(output)
        if ret != 0 or len(output) == 0:
            # Fail to get fan duty
            SYS_LOG_WARN('fail to get fan duty cycle percentage')
            return False
    except Exception as e:
        DBG_LOG(repr(e))
        return False

    return fanduty

def get_temperature(tid):
    ret, output = getstatusoutput("cat "+THERMAL_SENSOR_PATH[tid])
    try:
        temperature = int(output)
        if ret != 0 or len(output) == 0:
            # Fail to get thermal sensor temperature
            SYS_LOG_WARN('thermal index %d fail to get sensor temperature' % tid)
            return False
    except Exception as e:
        DBG_LOG(repr(e))
        return False

    return temperature

def check_fan_status():
    for fan_index in range(1, FAN_NUM_MAX+1):
        ret, output = getstatusoutput("cat "+FAN_PREFIX_PATH % (fan_index, FAN_PRESENT_NODE))
        try:
            if ret != 0 or len(output) == 0:
                # Fail to get fan present status
                SYS_LOG_WARN('fan index %d fail to get present status' % fan_index)
                return False
        except Exception as e:
            DBG_LOG(repr(e))
            return False

    return True

def check_thermal_sensor_status():
    for thermal_index in range(len(THERMAL_SENSOR_PATH)):
        ret, output = getstatusoutput("cat "+THERMAL_SENSOR_PATH[thermal_index]+" | sort -ur | head -n 1")
        try:
            if ret != 0:
                # Fail to get thermal sensor status
                SYS_LOG_WARN('thermal index %d fail to get sensor status' % thermal_index)
                return False
        except Exception as e:
            DBG_LOG(repr(e))
            return False
    return True

def fan_status_policy():
    # Bring fan speed to FAN_PERCENTAGE_MAX if any fan is not operational
    for fan_index in range(1, FAN_NUM_MAX+1):
        # Check fan fault status
        ret, output = getstatusoutput("cat "+FAN_PREFIX_PATH % (fan_index, FAN_FAULT_NODE))
        try:
            if ret != 0 or len(output) == 0:
                # Fail to get fan fault status
                SYS_LOG_WARN('fan index %d fail to get fault status' % fan_index)
                return False
            elif output == "1":
                # Fan fault detected
                SYS_LOG_WARN('fan index %d fault detected' % fan_index)
                return False
        except Exception as e:
            DBG_LOG(repr(e))
            return False

    # Bring fan speed to FAN_PERCENTAGE_MAX if fan is not present
    for fan_index in range(1, FAN_NUM_MAX+1):
        # Check fan present status
        ret, output = getstatusoutput("cat "+FAN_PREFIX_PATH % (fan_index, FAN_PRESENT_NODE))
        try:
            if ret != 0 or len(output) == 0:
                # Fail to get fan present status
                SYS_LOG_WARN('fan index %d fail to get present status' % fan_index)
                return False
            elif output == "0":
                # Fan absent detected
                SYS_LOG_WARN('fan index %d absent detected' % fan_index)
                return False
        except Exception as e:
            DBG_LOG(repr(e))
            return False

    return True

def thermal_sensor_policy():
    # Get current fan duty
    fanduty = get_fan_duty()
    if(fanduty is False):
        return False

    DBG_LOG('fanduty:%d' % fanduty)

    aboveTa = 0
    aboveTb = 0
    aboveTc = 0
    aboveTd = 0
    aboveSd = 0
    
    # Get temperature from each thermal sensor 
    for sensor in temp_sensor_threshold:
        try:
            temp = get_temperature(sensor[tid])
            aboveTa += (temp > sensor[tA])
            aboveTb += (temp > sensor[tB])
            aboveTc += (temp > sensor[tC])
            aboveTd += (temp > sensor[tD])
            aboveSd += (temp > sensor[tSd])
            DBG_LOG('tid:%d, temp:%d, aboveTa:%d, aboveTb:%d, aboveTc:%d, aboveTd:%d, aboveSd:%d ' % (sensor[tid], temp, aboveTa, aboveTb, aboveTc, aboveTd, aboveSd))
        except Exception as e:
            DBG_LOG(repr(e))
            return False

    # Determine if temperature above the shutdown threshold 
    if(aboveSd):
        SYS_LOG_CRITICAL('temperature above the shutdown threshold')
        if(shutdown_device() is False):
            return False

    # Adjust fan speed based on current temperature if fan speed changed
    newPercentage = 0
    if(fanduty == FAN_PERCENTAGE_MIN):
        newPercentage = FAN_PERCENTAGE_MID if (aboveTc != 0) else 0
    elif(fanduty == FAN_PERCENTAGE_MID):
        if aboveTd != 0:
            newPercentage = FAN_PERCENTAGE_MAX;
        elif aboveTb == 0:
            newPercentage = FAN_PERCENTAGE_MIN;
    elif(fanduty == FAN_PERCENTAGE_MAX):
        newPercentage = FAN_PERCENTAGE_MID if (aboveTa == 0) else 0
    else:
        newPercentage = FAN_PERCENTAGE_MAX

    DBG_LOG('newPercentage:%d' % newPercentage)
    if(newPercentage != 0):
        if(set_fan_duty(newPercentage)is False):
            return False

    return True

def main(argv):
    # Wait 60 seconds for system to finish the initialization.
    time.sleep(60)

    # Main loop.
    while True:
        # Sleep
        time.sleep(SLEEP_TIME)
        
        if(check_fan_status() is False):
            SYS_LOG_WARN('check fan status failed, set fan speed to max')
            set_fan_duty(FAN_PERCENTAGE_MAX)
            continue

        if(check_thermal_sensor_status() is False):
            SYS_LOG_WARN('check thermal sensor status failed, set fan speed to max')
            set_fan_duty(FAN_PERCENTAGE_MAX)
            continue

        if(fan_status_policy() is False):
            SYS_LOG_WARN('fan status policy failed, set fan speed to max')
            set_fan_duty(FAN_PERCENTAGE_MAX)
            continue

        if(thermal_sensor_policy() is False):
            SYS_LOG_WARN('thermal sensor policy failed, set fan speed to max')
            set_fan_duty(FAN_PERCENTAGE_MAX)
            continue

if __name__ == '__main__':
    main(sys.argv)


