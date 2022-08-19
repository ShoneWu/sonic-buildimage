#!/usr/bin/env python
#
# Copyright (C) 2021 Accton Networks, Inc.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
Usage: %(scriptName)s [options] command object

options:
    -h | --help     : this help message
    -d | --debug    : run with debug mode
    -f | --force    : ignore error during installation or clean
command:
    install     : install drivers and generate related sysfs nodes
    clean       : uninstall drivers and remove related sysfs nodes
    show        : show all systen status
    sff         : dump SFP eeprom
    set         : change board setting with fan|led|sfp
"""

import os
try:
    import commands
except Exception as ex:
    import subprocess
import sys, getopt
import logging
import re
import time


PROJECT_NAME = 'csp7551'
version = '0.1.0'
verbose = False
DEBUG = False
args = []
ALL_DEVICE = {}
#DEVICE_NO = {'led':5, 'fan':6,'thermal':4, 'psu':2, 'sfp':32}
DEVICE_NO = {'sfp':32}
FORCE = 0
#logging.basicConfig(filename= PROJECT_NAME+'.log', filemode='w',level=logging.DEBUG)
#logging.basicConfig(level=logging.INFO)

if DEBUG == True:
    print (sys.argv[0])
    print ('ARGV      :', sys.argv[1:])


def main():
    global DEBUG
    global args
    global FORCE
    status = 0

    if len(sys.argv)<2:
        show_help()

    options, args = getopt.getopt(sys.argv[1:], 'hdf', ['help',
                                                       'debug',
                                                       'force',
                                                          ])
    if DEBUG == True:
        print (options)
        print (args)
        print (len(sys.argv))

    for opt, arg in options:
        if opt in ('-h', '--help'):
            show_help()
        elif opt in ('-d', '--debug'):
            DEBUG = True
            logging.basicConfig(level=logging.INFO)
        elif opt in ('-f', '--force'): 
            FORCE = 1
        else:
            logging.info('no option')
    for arg in args:
        if arg == 'install':
           status = do_install()
        elif arg == 'clean':
           status = do_uninstall()
        elif arg == 'api':
           do_sonic_platform_install()
        elif arg == 'api_clean':
           do_sonic_platform_clean()
        elif arg == 'show':
           status = device_traversal()
        elif arg == 'sff':
            if len(args)!=2:
                show_eeprom_help()
            elif int(args[1]) ==0 or int(args[1]) > DEVICE_NO['sfp']:
                show_eeprom_help()
            else:
                show_eeprom(args[1])
            return
        elif arg == 'set':
            if len(args)<3:
                show_set_help()
            else:
                set_device(args[1:])
            return
        else:
            show_help()

    if status:
        sys.exit(1)
    else:
        sys.exit(0)

def show_help():
    print (__doc__ % {'scriptName' : sys.argv[0].split("/")[-1]})
    sys.exit(0)

def show_set_help():
    cmd =  sys.argv[0].split("/")[-1]+ " "  + args[0]
    print  (cmd +" [led|sfp|fan]")
    print  ("    use \""+ cmd + " led 0-4 \"  to set led color")
    print  ("    use \""+ cmd + " fan 0-100\" to set fan duty percetage")
    print  ("    use \""+ cmd + " sfp 1-32 {0|1}\" to set sfp# tx_disable")
    sys.exit(0)

def show_eeprom_help():
    cmd =  sys.argv[0].split("/")[-1]+ " "  + args[0]
    print  ("    use \""+ cmd + " 1-32 \" to dump sfp# eeprom")
    sys.exit(0)

def my_log(txt):
    if DEBUG == True:
        print ("[ROY]"+txt)
    return

def log_os_system(cmd, show):
    logging.info('Run :'+cmd)
    try:
        status, output = commands.getstatusoutput(cmd)
    except Exception as ex:
        status, output = subprocess.getstatusoutput(cmd)
    my_log (cmd +"with result:" + str(status))
    my_log ("      output:"+output)
    if status:
        logging.info('Failed :'+cmd)
        if show:
            print('Failed :'+cmd)
    return  status, output

def driver_check():
    ret, lsmod = log_os_system("lsmod| grep accton", 0)
    logging.info('mods:'+lsmod)
    if len(lsmod) ==0:
        return False   
    return True


kos = [
'modprobe i2c_dev',
'modprobe i2c_mux_pca954x force_deselect_on_exit=1',
'modprobe ipmi_devintf',
'modprobe libcomposite',
'modprobe usb_f_acm',
'modprobe g_serial',
'modprobe g_ether',
'insmod /lib/modules/"$(uname -r)"/extra/fpga_driver.ko',
'insmod /lib/modules/"$(uname -r)"/extra/accton_i2c_cpld.ko',
'insmod /lib/modules/"$(uname -r)"/extra/x86-64-accton-csp7551-sfp.ko',
'insmod /lib/modules/"$(uname -r)"/extra/at24_csp7551.ko',
'modprobe devlink',
'modprobe ice',
'insmod /lib/modules/"$(uname -r)"/extra/bf_kdrv.ko',
'insmod /lib/modules/"$(uname -r)"/extra/bf_tun.ko'
]

rm_kos = [
'modprobe -r i2c_dev',
'modprobe -r i2c_mux_pca954x',
'modprobe -r ipmi_devintf',
'rmmod fpga_driver',
'rmmod x86-64-accton-csp7551-sfp',
'rmmod accton_i2c_cpld',
'rmmod bf_kdrv',
'rmmod bf_tun'
]

def driver_install():
    global FORCE
    status = os.system("lsmod | grep ast")
    if status == 0:
        log_os_system("rmmod -f ast", 1)
    
    status, kervel_version = log_os_system("uname -r",0)
    
    #os.system("modprobe -r ice")
    if os.path.isfile("/usr/lib/modules/{}/kernel/drivers/gpu/drm/ast/ast.ko".format(kervel_version)):
        os.rename("/usr/lib/modules/{}/kernel/drivers/gpu/drm/ast/ast.ko".format(kervel_version),"/usr/lib/modules/{}/kernel/drivers/gpu/drm/ast/ast.ko.bak".format(kervel_version))
        os.system("rmmod ast")
    status,output=log_os_system("modinfo ice| grep version | head -n 1 | cut -d ':'  -f 2", 1)
    if output.strip() == "0.7.1-k":
        os.system("modprobe -r ice")
        os.system("cp /usr/lib/modules/{}/updates/drivers/net/ethernet/intel/ice/ice.ko /usr/lib/modules/{}/kernel/drivers/net/ethernet/intel/ice/ice.ko".format(kervel_version,kervel_version))
        os.system("update-initramfs -u")
    for i in range(0,len(kos)):
        log_os_system(kos[i], 1)

    os.system("depmod")

    return 0

def driver_uninstall():
    global FORCE
    for i in range(0,len(rm_kos)):
        log_os_system(rm_kos[i], 1)
    return 0

led_prefix ='/sys/class/leds/'+PROJECT_NAME+'_led::'
hwmon_types = {'led': ['diag','fan','loc','psu1','psu2']}
hwmon_nodes = {'led': ['brightness'] }
hwmon_prefix ={'led': led_prefix}

i2c_prefix = '/sys/bus/i2c/devices/'
i2c_bus = {}
i2c_nodes = {}

#i2c-0 is i801 SMBUS
#i2c-1~i2c-32 are smbus 1-32 that map into port 1-32
sfp_map =  [1, 2, 3, 4, 5, 6, 7, 8, 9,10,
           11,12,13,14,15,16,17,18,19,20,
		   21,22,23,24,25,26,27,28,29,30,
		   31,32
		   ]

#TLV EEPROM is at bus0 0x57, i2c-33 and i2c-34 are port_cpld1 and port_cpld2
mknod =[
'echo cpld_csp7551 0x62 > /sys/bus/i2c/devices/i2c-33/new_device',
'echo cpld_csp7551 0x64 > /sys/bus/i2c/devices/i2c-34/new_device'
]

def device_install():
    global FORCE
    status, kervel_version = log_os_system("uname -r",0)
    if kervel_version == "4.19.0-12-2-amd64":
        mknod.append('echo 24cxb04 0x57 > /sys/bus/i2c/devices/i2c-0/new_device')
    else:
        mknod.append('echo 24c64 0x57 > /sys/bus/i2c/devices/i2c-0/new_device')

    for i in range(0,len(mknod)):
        #for pca954x need times to built new i2c buses
        if mknod[i].find('pca954') != -1:
           time.sleep(1)

        status, output = log_os_system(mknod[i], 1)
        if status:
            print (output)
            if FORCE == 0:
                return status

    for i in range(0,len(sfp_map)):
        status, output =log_os_system("echo csp7551_port"+str(i+1)+" 0x50 > /sys/bus/i2c/devices/i2c-"+str(sfp_map[i])+"/new_device", 1)
        if status:
            print (output)
            if FORCE == 0:
                return status
    return
    
def device_uninstall():
    global FORCE
    
    for i in range(0,len(sfp_map)):
        if os.path.isfile("/tmp/device_init_first_time"):
            target = "/sys/bus/i2c/devices/i2c-"+str(sfp_map[i])+"/delete_device"
        else:
            target = "/sys/bus/i2c/devices/i2c-"+str(sfp_map[i])+"/delete_device > /dev/null 2>&1"
        status, output =log_os_system("echo 0x50 > "+ target, 1)
        if status:
            print (output)
            if FORCE == 0:
                return status

    nodelist = mknod

    for i in range(len(nodelist)):
        target = nodelist[-(i+1)]
        temp = target.split()
        del temp[1]
        temp[-1] = temp[-1].replace('new_device', 'delete_device')
        if os.path.isfile("/tmp/device_init_first_time"):
            status, output = log_os_system(" ".join(temp), 1)
        else:
            status, output = log_os_system(" ".join(temp)+" > /dev/null 2>&1", 1)
        if status:
            print (output)
            if FORCE == 0:
                return status

    log_os_system("echo 1 > /tmp/device_init_first_time", 1)

    return

def system_ready():
    if driver_check() == False:
        return False
    if not device_exist(): 
        return False
    return True

PLATFORM_ROOT_PATH = '/usr/share/sonic/device'
PLATFORM_API2_WHL_FILE_PY3 ='sonic_platform-1.0-py3-none-any.whl'
def do_sonic_platform_install():
    device_path = "{}{}{}{}".format(PLATFORM_ROOT_PATH, '/x86_64-accton_', PROJECT_NAME, '-r0')
    SONIC_PLATFORM_BSP_WHL_PKG_PY3 = "/".join([device_path, PLATFORM_API2_WHL_FILE_PY3])

    #Check API2.0 on py whl file
    status, output = log_os_system("pip3 show sonic-platform > /dev/null 2>&1", 0)
    if status:
        if os.path.exists(SONIC_PLATFORM_BSP_WHL_PKG_PY3):
            status, output = log_os_system("pip3 install "+ SONIC_PLATFORM_BSP_WHL_PKG_PY3, 1)
            if status:
                print ("Error: Failed to install {}".format(PLATFORM_API2_WHL_FILE_PY3))
                return status
            else:
                print ("Successfully installed {} package".format(PLATFORM_API2_WHL_FILE_PY3))
        else:
            print('{} is not found'.format(PLATFORM_API2_WHL_FILE_PY3))
    else:
        print('{} has installed'.format(PLATFORM_API2_WHL_FILE_PY3))

    return

def do_sonic_platform_clean():
    status, output = log_os_system("pip3 show sonic-platform > /dev/null 2>&1", 0)
    if status:
        print('{} does not install, not need to uninstall'.format(PLATFORM_API2_WHL_FILE_PY3))
    else:
        status, output = log_os_system("pip3 uninstall sonic-platform -y", 0)
        if status:
            print('Error: Failed to uninstall {}'.format(PLATFORM_API2_WHL_FILE_PY3))
            return status
        else:
            print('{} is uninstalled'.format(PLATFORM_API2_WHL_FILE_PY3))

    return

def do_install():
    status = 0
    print ("Checking system....")
    if driver_check() == False:
        print ("No driver, installing....")
        status = driver_install()
        if status:
            if FORCE == 0:
                return status
    else:
        print (PROJECT_NAME.upper()+" drivers detected....")
    if not device_exist():
        print ("No device, installing....")
        status = device_install() 
        if status:
            if FORCE == 0:
                return status
    else:
        print (PROJECT_NAME.upper()+" devices detected....")

    #do_sonic_platform_install()

    return status

def do_uninstall():
    print ("Checking system....")
    if (not device_exist()) and (FORCE == 0):
        print (PROJECT_NAME.upper() +" has no device installed....")
    else:
        print ("Removing device....")
        status = device_uninstall()
        if status:
            if FORCE == 0:
                return status

    if (driver_check()== False) and (FORCE == 0):
        print (PROJECT_NAME.upper() +" has no driver installed....")
    else:
        print ("Removing installed driver....")
        status = driver_uninstall()
        if status:
            if FORCE == 0:
                return  status

    #do_sonic_platform_clean()

    return 0

def devices_info():
    global DEVICE_NO
    global ALL_DEVICE
    global i2c_bus, hwmon_types
    for key in DEVICE_NO:
        ALL_DEVICE[key]= {}
        for i in range(0,DEVICE_NO[key]):
            ALL_DEVICE[key][key+str(i+1)] = []

    for key in i2c_bus:
        buses = i2c_bus[key]
        nodes = i2c_nodes[key]
        for i in range(0,len(buses)):
            for j in range(0,len(nodes)):
                if  'fan' == key:
                    for k in range(0,DEVICE_NO[key]):
                        node = key+str(k+1)
                        path = i2c_prefix+ buses[i]+"/fan"+str(k+1)+"_"+ nodes[j]
                        my_log(node+": "+ path)
                        ALL_DEVICE[key][node].append(path)
                elif  'sfp' == key:
                    for k in range(0,DEVICE_NO[key]):
                        node = key+str(k+1)
                        path = i2c_prefix+ str(sfp_map[k])+ buses[i]+"/"+ nodes[j]
                        my_log(node+": "+ path)
                        ALL_DEVICE[key][node].append(path)
                else:
                    node = key+str(i+1)
                    path = i2c_prefix+ buses[i]+"/"+ nodes[j]
                    my_log(node+": "+ path)
                    ALL_DEVICE[key][node].append(path)

    for key in hwmon_types:
        itypes = hwmon_types[key]
        nodes = hwmon_nodes[key]
        for i in range(0,len(itypes)):
            for j in range(0,len(nodes)):
                node = key+"_"+itypes[i]
                path = hwmon_prefix[key]+ itypes[i]+"/"+ nodes[j]
                my_log(node+": "+ path)
                ALL_DEVICE[key][ key+str(i+1)].append(path)

    #show dict all in the order
    if DEBUG == True:
        for i in sorted(ALL_DEVICE.keys()):
            print(i+": ")
            for j in sorted(ALL_DEVICE[i].keys()):
                print("   "+j)
                for k in (ALL_DEVICE[i][j]):
                    print("   "+"   "+k)
    return

def show_eeprom(index):
    if system_ready()==False:
        print("System's not ready.")
        print("Please install first!")
        return

    if len(ALL_DEVICE)==0:
        devices_info()
    node = ALL_DEVICE['sfp'] ['sfp'+str(index)][0]
    node = node.replace(node.split("/")[-1], 'sfp_eeprom')
    # check if got hexdump command in current environment
    ret, log = log_os_system("which hexdump", 0)
    ret, log2 = log_os_system("which busybox hexdump", 0)
    if len(log):
        hex_cmd = 'hexdump'
    elif len(log2):
        hex_cmd = ' busybox hexdump'
    else:
        log = 'Failed : no hexdump cmd!!'
        logging.info(log)
        print (log)
        return 1

    print (node + ":")
    ret, log = log_os_system("cat "+node+"| "+hex_cmd+" -C", 1)
    if ret==0:
        print  (log)
    else:
        print ("**********device no found**********")
    return

def set_device(args):
    global DEVICE_NO
    global ALL_DEVICE
    if system_ready()==False:
        print("System's not ready.")
        print("Please install first!")
        return

    if len(ALL_DEVICE)==0:
        devices_info()

    if args[0]=='led':
        if int(args[1])>4:
            show_set_help()
            return
        #print  ALL_DEVICE['led']
        for i in range(0,len(ALL_DEVICE['led'])):
            for k in (ALL_DEVICE['led']['led'+str(i+1)]):
                ret, log = log_os_system("echo "+args[1]+" >"+k, 1)
                if ret:
                    return ret
    elif args[0]=='fan':
        if int(args[1])>100:
            show_set_help()
            return
        #print  ALL_DEVICE['fan']
        #fan1~6 is all fine, all fan share same setting
        node = ALL_DEVICE['fan'] ['fan1'][0]
        node = node.replace(node.split("/")[-1], 'fan_duty_cycle_percentage')
        ret, log = log_os_system("cat "+ node, 1)
        if ret==0:
            print ("Previous fan duty: " + log.strip() +"%")
        ret, log = log_os_system("echo "+args[1]+" >"+node, 1)
        if ret==0:
            print ("Current fan duty: " + args[1] +"%")
        return ret
    elif args[0]=='sfp':
        if int(args[1])> DEVICE_NO[args[0]] or int(args[1])==0:
            show_set_help()
            return
        if len(args)<2:
            show_set_help()
            return

        if int(args[2])>1:
            show_set_help()
            return

        #print  ALL_DEVICE[args[0]]
        for i in range(0,len(ALL_DEVICE[args[0]])):
            for j in ALL_DEVICE[args[0]][args[0]+str(args[1])]:
                if j.find('tx_disable')!= -1:
                    ret, log = log_os_system("echo "+args[2]+" >"+ j, 1)
                    if ret:
                        return ret

    return

#get digits inside a string.
#Ex: 31 for "sfp31"
def get_value(input):
    digit = re.findall('\d+', input)
    return int(digit[0])

def device_traversal():
    if system_ready()==False:
        print("System's not ready.")
        print("Please install first!")
        return

    if len(ALL_DEVICE)==0:
        devices_info()
    for i in sorted(ALL_DEVICE.keys()):
        print("============================================")
        print(i.upper()+": ")
        print("============================================")

        for j in sorted(ALL_DEVICE[i].keys(), key=get_value):
            print ("   "+j+":",)
            for k in (ALL_DEVICE[i][j]):
                ret, log = log_os_system("cat "+k, 0)
                func = k.split("/")[-1].strip()
                func = re.sub(j+'_','',func,1)
                func = re.sub(i.lower()+'_','',func,1)
                if ret==0:
                    print (func+"="+log+" ",)
                else:
                    print (func+"="+"X"+" ",)
            print
            print("----------------------------------------------------------------")

        print
    return

def device_exist():
    ret1, log = log_os_system("ls "+i2c_prefix+"0-0057", 0)
    ret2, log = log_os_system("ls "+i2c_prefix+"*0050", 0)
    return not(ret1 or ret2)

if __name__ == "__main__":
    main()
