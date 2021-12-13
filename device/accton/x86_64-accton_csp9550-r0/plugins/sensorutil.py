#!/usr/bin/env python
#
# Copyright (C) 2017 Accton Technology Corporation
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

# ------------------------------------------------------------------
# HISTORY:
#    mm/dd/yyyy (A.D.)
#    3/23/2018: Roy Lee modify for as7326_56x
#    6/26/2018: Jostar implement by new thermal policy from HW RD
#    7/2/2020(1.1): (1)Read CPLD register to judge whether PSU is present
#                   (2)Get PSU information(eg: Voltage/current/temperature etc) to give self.DATA directly,
#                      not give x[0-9]/y[0-9] -> x[0-9]/y[0-9] give self.DATA again
# ------------------------------------------------------------------

import commands
import os.path
import re
import json
import subprocess

VERSION = '1.0'


class SensorUtil(object):
    """Platform-specific SensorUtil class"""

    """ Dictionary where
        key1 = thermal id index (integer) starting from 1 """
    DATA = {'FAN1':{'fan1_front':{'Type':'RPM', 'Value':0.0, 'LowThd':0.0, 'HighThd':0.0},
                    'fan1_rear':{'Type':'RPM', 'Value':0.0, 'LowThd':0.0, 'HighThd':0.0},
                   },
            'FAN2':{'fan2_front':{'Type':'RPM', 'Value':0.0, 'LowThd':0.0, 'HighThd':0.0},
                    'fan2_rear':{'Type':'RPM', 'Value':0.0, 'LowThd':0.0, 'HighThd':0.0}
                   },
            'FAN3':{'fan3_front':{'Type':'RPM', 'Value':0.0, 'LowThd':0.0, 'HighThd':0.0},
                    'fan3_rear':{'Type':'RPM', 'Value':0.0, 'LowThd':0.0, 'HighThd':0.0}
                   },
            'FAN4':{'fan4_front':{'Type':'RPM', 'Value':0.0, 'LowThd':0.0, 'HighThd':0.0},
                    'fan4_rear':{'Type':'RPM', 'Value':0.0, 'LowThd':0.0, 'HighThd':0.0}
                   },
            'FAN5':{'fan5_front':{'Type':'RPM', 'Value':0.0, 'LowThd':0.0, 'HighThd':0.0},
                    'fan5_rear':{'Type':'RPM', 'Value':0.0, 'LowThd':0.0, 'HighThd':0.0}
                   },
            'TEMP':{'MAC_hot_temp':{'Type':'temperature', 'Value':0.0, 'LowThd':0.0, 'HighThd':0.0},
                    'MAC_cool_temp':{'Type':'temperature', 'Value':0.0, 'LowThd':0.0, 'HighThd':0.0},
                    'pch_temp':{'Type':'temperature', 'Value':0.0, 'LowThd':0.0, 'HighThd':0.0},
                    'cpu0_temp':{'Type':'temperature', 'Value':0.0, 'LowThd':0.0, 'HighThd':0.0},
                    'cpu1_temp':{'Type':'temperature', 'Value':0.0, 'LowThd':0.0, 'HighThd':0.0},
                    'CPU_TEMP':{'Type':'temperature', 'Value':0.0, 'LowThd':0.0, 'HighThd':0.0}
                   },
            'PSU1':{'vin':{'Type':'voltage', 'Value':0.0, 'LowThd':0.0, 'HighThd':0.0},
                    'iin':{'Type':'amp', 'Value':0.0, 'LowThd':0.0, 'HighThd':0.0},
                    'pin':{'Type':'power', 'Value':0.0, 'LowThd':0.0, 'HighThd':0.0},
                    'vout':{'Type':'voltage', 'Value':0.0, 'LowThd':0.0, 'HighThd':0.0},
                    'iout':{'Type':'amp', 'Value':0.0, 'LowThd':0.0, 'HighThd':0.0},
                    'pout':{'Type':'power', 'Value':0.0, 'LowThd':0.0, 'HighThd':0.0},
                    'fan':{'Type':'RPM', 'Value':0.0, 'LowThd':0.0, 'HighThd':0.0},
                    'Ambient_Temperature':{'Type':'temperature', 'Value':0.0, 'LowThd':0.0, 'HighThd':0.0},
                    'Primary_Temperature':{'Type':'temperature', 'Value':0.0, 'LowThd':0.0, 'HighThd':0.0},
                    'Secondary_Temperature':{'Type':'temperature', 'Value':0.0, 'LowThd':0.0, 'HighThd':0.0}
                   },
            'PSU2':{'vin':{'Type':'voltage', 'Value':0.0, 'LowThd':0.0, 'HighThd':0.0},
                    'iin':{'Type':'amp', 'Value':0.0, 'LowThd':0.0, 'HighThd':0.0},
                    'pin':{'Type':'power', 'Value':0.0, 'LowThd':0.0, 'HighThd':0.0},
                    'vout':{'Type':'voltage', 'Value':0.0, 'LowThd':0.0, 'HighThd':0.0},
                    'iout':{'Type':'amp', 'Value':0.0, 'LowThd':0.0, 'HighThd':0.0},
                    'pout':{'Type':'power', 'Value':0.0, 'LowThd':0.0, 'HighThd':0.0},
                    'fan':{'Type':'RPM', 'Value':0.0, 'LowThd':0.0, 'HighThd':0.0},
                    'Ambient_Temperature':{'Type':'temperature', 'Value':0.0, 'LowThd':0.0, 'HighThd':0.0},
                    'Primary_Temperature':{'Type':'temperature', 'Value':0.0, 'LowThd':0.0, 'HighThd':0.0},
                    'Secondary_Temperature':{'Type':'temperature', 'Value':0.0, 'LowThd':0.0, 'HighThd':0.0}
                   },
            'SWITCH':{'ir3580_vin':{'Type':'voltage', 'Value':0.0, 'LowThd':0.0, 'HighThd':0.0},
                      'ir3580_iin':{'Type':'amp', 'Value':0.0, 'LowThd':0.0, 'HighThd':0.0},
                      'ir3580_pin':{'Type':'power', 'Value':0.0, 'LowThd':0.0, 'HighThd':0.0},
                      'ir3580_vout':{'Type':'voltage', 'Value':0.0, 'LowThd':0.0, 'HighThd':0.0},
                      'ir3580_iout':{'Type':'amp', 'Value':0.0, 'LowThd':0.0, 'HighThd':0.0},
                      'ir3580_pout':{'Type':'power', 'Value':0.0, 'LowThd':0.0, 'HighThd':0.0},
                      'ir3584_vin':{'Type':'voltage', 'Value':0.0, 'LowThd':0.0, 'HighThd':0.0},
                      'ir3584_iin':{'Type':'amp', 'Value':0.0, 'LowThd':0.0, 'HighThd':0.0},
                      'ir3584_pin':{'Type':'power', 'Value':0.0, 'LowThd':0.0, 'HighThd':0.0},
                      'ir3584_vout':{'Type':'voltage', 'Value':0.0, 'LowThd':0.0, 'HighThd':0.0},
                      'ir3584_iout':{'Type':'amp', 'Value':0.0, 'LowThd':0.0, 'HighThd':0.0},
                      'ir3584_pout':{'Type':'power', 'Value':0.0, 'LowThd':0.0, 'HighThd':0.0}
                     },
            'SYS':{'Sys_AirFlow': 'BTOF'}
           }

    DATA_RDONLY = DATA.copy()

    curl_cmd1 = "curl -s http://240.1.1.1:8080/api/sys/sensors"
    curl_cmd2 = "curl -s http://240.1.1.1:8080/api/sys/fanpower_threshold"

    def get_num_thermals(self):
        return self.THERMAL_NUM_MAX

    def get_idx_thermal_start(self):
        return self.THERMAL_NUM_1_IDX

    def _syscmd(self, cmd):
        status, output = commands.getstatusoutput(cmd)
        return status, output

    def _validate_sensor(self, sensor_dict):
        fld_list = ["LowThd", "HighThd", "Value"]
        for fld in fld_list:
            if fld not in sensor_dict:
                return False

        try:
            low = float(sensor_dict["LowThd"])
            high = float(sensor_dict["HighThd"])
            val = float(sensor_dict["Value"])

            if val > high or val < low:
                return False

            return True
        except:
            return Fales

    def ipmi_poll_thermal(self):
        # Reset DATA for reentrant
        self.DATA = self.DATA_RDONLY.copy()

        st1, log1 = self._syscmd(self.curl_cmd1)
        st2, log2 = self._syscmd(self.curl_cmd2)
        if st1 != 0 or st2 != 0:
            print 'error on syscmd'
        d = json.loads(log1)
        g = json.loads(log2)


        #ast_pwm-isa-0000
        #FAN1
        self.DATA['FAN1']['fan1_front']['Value'] = d["Information"][0]["fan1"].split(" ")[0]
        self.DATA['FAN1']['fan1_rear']['Value'] = d["Information"][0]["fan2"].split(" ")[0]
        self.DATA['FAN1']['fan1_front']['LowThd'] = g["Information"]["fan1_1_L"]
        self.DATA['FAN1']['fan1_front']['HighThd'] = g["Information"]["fan1_1_H"]
        self.DATA['FAN1']['fan1_rear']['LowThd'] = g["Information"]["fan1_2_L"]
        self.DATA['FAN1']['fan1_rear']['HighThd'] = g["Information"]["fan1_2_H"]

        #FAN2
        self.DATA['FAN2']['fan2_front']['Value'] = d["Information"][0]["fan3"].split(" ")[0]
        self.DATA['FAN2']['fan2_rear']['Value'] = d["Information"][0]["fan4"].split(" ")[0]
        self.DATA['FAN2']['fan2_front']['LowThd'] = g["Information"]["fan2_1_L"]
        self.DATA['FAN2']['fan2_front']['HighThd'] = g["Information"]["fan2_1_H"]
        self.DATA['FAN2']['fan2_rear']['LowThd'] = g["Information"]["fan2_2_L"]
        self.DATA['FAN2']['fan2_rear']['HighThd'] = g["Information"]["fan2_2_H"]

        #FAN3
        self.DATA['FAN3']['fan3_front']['Value'] = d["Information"][0]["fan5"].split(" ")[0]
        self.DATA['FAN3']['fan3_rear']['Value'] = d["Information"][0]["fan6"].split(" ")[0]
        self.DATA['FAN3']['fan3_front']['LowThd'] =g["Information"]["fan3_1_L"]
        self.DATA['FAN3']['fan3_front']['HighThd'] =g["Information"]["fan3_1_H"]
        self.DATA['FAN3']['fan3_rear']['LowThd'] = g["Information"]["fan3_2_L"]
        self.DATA['FAN3']['fan3_rear']['HighThd'] = g["Information"]["fan3_2_H"]

        #FAN4
        self.DATA['FAN4']['fan4_front']['Value'] = d["Information"][0]["fan7"].split(" ")[0]
        self.DATA['FAN4']['fan4_rear']['Value'] = d["Information"][0]["fan8"].split(" ")[0]
        self.DATA['FAN4']['fan4_front']['LowThd'] = g["Information"]["fan4_1_L"]
        self.DATA['FAN4']['fan4_front']['HighThd'] = g["Information"]["fan4_1_H"]
        self.DATA['FAN4']['fan4_rear']['LowThd'] = g["Information"]["fan4_2_L"]
        self.DATA['FAN4']['fan4_rear']['HighThd'] = g["Information"]["fan4_2_H"]

        #FAN5
        self.DATA['FAN5']['fan5_front']['Value'] = d["Information"][0]["fan9"].split(" ")[0]
        self.DATA['FAN5']['fan5_rear']['Value'] = d["Information"][0]["fan10"].split(" ")[0]
        self.DATA['FAN5']['fan5_front']['LowThd'] = g["Information"]["fan5_1_L"]
        self.DATA['FAN5']['fan5_front']['HighThd'] = g["Information"]["fan5_1_H"]
        self.DATA['FAN5']['fan5_rear']['LowThd'] = g["Information"]["fan5_2_L"]
        self.DATA['FAN5']['fan5_rear']['HighThd'] = g["Information"]["fan5_2_H"]


        #SWITCH
        #ir3580-i2c-0-08
        self.DATA['SWITCH']['ir3580_vin']['Value'] = d["Information"][1]["in0"].split(" ")[0]
        self.DATA['SWITCH']['ir3580_iin']['Value'] = d["Information"][1]["curr1"].split(" ")[0]
        if d["Information"][1]["power1"].split(" ")[1] == 'mW':
            power1=float(d["Information"][1]["power1"].split(" ")[0]) / 1000
            self.DATA['SWITCH']['ir3580_pin']['Value'] = power1
        elif d["Information"][1]["power1"].split(" ")[1] == 'kW':
            power1=float(d["Information"][1]["power1"].split(" ")[0]) * 1000
            self.DATA['SWITCH']['ir3580_pin']['Value'] = power1
        else:
            self.DATA['SWITCH']['ir3580_pin']['Value'] = d["Information"][1]["power1"].split(" ")[0]
        self.DATA['SWITCH']['ir3580_vout']['Value'] = d["Information"][1]["in1"].split(" ")[0]
        self.DATA['SWITCH']['ir3580_iout']['Value'] = d["Information"][1]["curr2"].split(" ")[0]
        if d["Information"][1]["power2"].split(" ")[1] == 'mW':
            power2=float(d["Information"][1]["power2"].split(" ")[0]) / 1000
            self.DATA['SWITCH']['ir3580_pout']['Value'] = power2
        elif d["Information"][1]["power2"].split(" ")[1] == 'kW':
            power2=float(d["Information"][1]["power2"].split(" ")[0]) * 1000
            self.DATA['SWITCH']['ir3580_pout']['Value'] = power2
        else:
            self.DATA['SWITCH']['ir3580_pout']['Value'] = d["Information"][1]["power2"].split(" ")[0]

        self.DATA['SWITCH']['ir3580_vin']['LowThd'] = g["Information"]["ir3580_vin_L"]
        self.DATA['SWITCH']['ir3580_vin']['HighThd'] = g["Information"]["ir3580_vin_H"]
        self.DATA['SWITCH']['ir3580_iin']['LowThd'] = g["Information"]["ir3580_iin_L"]
        self.DATA['SWITCH']['ir3580_iin']['HighThd'] = g["Information"]["ir3580_iin_H"]
        self.DATA['SWITCH']['ir3580_pin']['LowThd'] = g["Information"]["ir3580_pin_L"]
        self.DATA['SWITCH']['ir3580_pin']['HighThd'] = g["Information"]["ir3580_pin_H"]
        self.DATA['SWITCH']['ir3580_vout']['LowThd'] = g["Information"]["ir3580_vout_L"]
        self.DATA['SWITCH']['ir3580_vout']['HighThd'] = g["Information"]["ir3580_vout_H"]
        self.DATA['SWITCH']['ir3580_iout']['LowThd'] = g["Information"]["ir3580_iout_L"]
        self.DATA['SWITCH']['ir3580_iout']['HighThd'] = g["Information"]["ir3580_iout_H"]
        self.DATA['SWITCH']['ir3580_pout']['LowThd'] = g["Information"]["ir3580_pout_L"]
        self.DATA['SWITCH']['ir3580_pout']['HighThd'] = g["Information"]["ir3580_pout_H"]

        #ir3584-i2c-0-0a
        self.DATA['SWITCH']['ir3584_vin']['Value'] = d["Information"][2]["in0"].split(" ")[0]
        self.DATA['SWITCH']['ir3584_iin']['Value'] = d["Information"][2]["curr1"].split(" ")[0]
        if d["Information"][2]["power1"].split(" ")[1] == 'mW':
            power1=float(d["Information"][2]["power1"].split(" ")[0]) / 1000
            self.DATA['SWITCH']['ir3584_pin']['Value'] = power1
        elif d["Information"][2]["power1"].split(" ")[1] == 'kW':
            power1=float(d["Information"][2]["power1"].split(" ")[0]) * 1000
            self.DATA['SWITCH']['ir3584_pin']['Value'] = power1
        else:
            self.DATA['SWITCH']['ir3584_pin']['Value'] = d["Information"][2]["power1"].split(" ")[0]
        self.DATA['SWITCH']['ir3584_vout']['Value'] = d["Information"][2]["in1"].split(" ")[0]
        self.DATA['SWITCH']['ir3584_iout']['Value'] = d["Information"][2]["curr2"].split(" ")[0]
        if d["Information"][2]["power2"].split(" ")[1] == 'mW':
            power2=float(d["Information"][2]["power2"].split(" ")[0]) / 1000
            self.DATA['SWITCH']['ir3584_pout']['Value'] = power2
        elif d["Information"][2]["power2"].split(" ")[1] == 'kW':
            power2=float(d["Information"][2]["power2"].split(" ")[0]) * 1000
            self.DATA['SWITCH']['ir3584_pout']['Value'] = power2
        else:
            self.DATA['SWITCH']['ir3584_pout']['Value'] = d["Information"][2]["power2"].split(" ")[0]

        self.DATA['SWITCH']['ir3584_vin']['LowThd'] = g["Information"]["ir3584_vin_L"]
        self.DATA['SWITCH']['ir3584_vin']['HighThd'] = g["Information"]["ir3584_vin_H"]
        self.DATA['SWITCH']['ir3584_iin']['LowThd'] = g["Information"]["ir3584_iin_L"]
        self.DATA['SWITCH']['ir3584_iin']['HighThd'] = g["Information"]["ir3584_iin_H"]
        self.DATA['SWITCH']['ir3584_pin']['LowThd'] = g["Information"]["ir3584_pin_L"]
        self.DATA['SWITCH']['ir3584_pin']['HighThd'] = g["Information"]["ir3584_pin_H"]
        self.DATA['SWITCH']['ir3584_vout']['LowThd'] = g["Information"]["ir3584_vout_L"]
        self.DATA['SWITCH']['ir3584_vout']['HighThd'] = g["Information"]["ir3584_vout_H"]
        self.DATA['SWITCH']['ir3584_iout']['LowThd'] = g["Information"]["ir3584_iout_L"]
        self.DATA['SWITCH']['ir3584_iout']['HighThd'] = g["Information"]["ir3584_iout_H"]
        self.DATA['SWITCH']['ir3584_pout']['LowThd'] = g["Information"]["ir3584_pout_L"]
        self.DATA['SWITCH']['ir3584_pout']['HighThd'] = g["Information"]["ir3584_pout_H"]     
        
        
        #TEMP
        #lm75b-i2c-6-48
        self.DATA['TEMP']['MAC_hot_temp']['Value'] = d["Information"][3]["temp1"].split(" ")[0]
        self.DATA['TEMP']['MAC_hot_temp']['LowThd'] = g["Information"]["MAC_hot_temp_L"]
        self.DATA['TEMP']['MAC_hot_temp']['HighThd'] = g["Information"]["MAC_hot_temp_H"]

        #lm75b-i2c-6-4a
        self.DATA['TEMP']['MAC_cool_temp']['Value'] = d["Information"][5]["temp1"].split(" ")[0]
        self.DATA['TEMP']['MAC_cool_temp']['LowThd'] = g["Information"]["MAC_cool_temp_L"]
        self.DATA['TEMP']['MAC_cool_temp']['HighThd'] = g["Information"]["MAC_cool_temp_H"]

        #lm75b-i2c-6-4c: CPU0(0x98 over 0x75, >> 1, is 0x4c), CPU0 must be present
        self.DATA['TEMP']['cpu0_temp']['Value'] = d["Information"][6]["temp1"].split(" ")[0]
        self.DATA['TEMP']['cpu0_temp']['LowThd'] = g["Information"]["cpu0_temp_L"]
        self.DATA['TEMP']['cpu0_temp']['HighThd'] = g["Information"]["cpu0_temp_H"]

        #lm75b-i2c-6-4d: PCH(0x9A over 0x75, >> 1, is 0x4d)
        self.DATA['TEMP']['pch_temp']['Value'] = d["Information"][7]["temp1"].split(" ")[0]
        self.DATA['TEMP']['pch_temp']['LowThd'] = g["Information"]["pch_temp_L"]
        self.DATA['TEMP']['pch_temp']['HighThd'] = g["Information"]["pch_temp_H"]

        #lm75b-i2c-6-4e: CPU1(0x9C over 0x75, >> 1, is 0x4e)
        #judge CPU1 present or not, and get CPU_TEMP
        cmd1 = subprocess.Popen('dmidecode -t processor | grep "Status:"', shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        cinfo, err = cmd1.communicate()
        if len(err) != 0:
            print("failed to get CPU present infomation")
            return -1
        cinfo = cinfo.decode(errors="ignore")
        cinfo1=re.sub('\t', '', cinfo)
        cinfo2=cinfo1.splitlines()  #CPU0: cinfo2[0], CPU1: cinfo2[1]
        
        if "Populated, Enabled" != cinfo2[1].split(": ")[1]: 
            del self.DATA['TEMP']['cpu1_temp'] 
            self.DATA['TEMP']['CPU_TEMP']['Value'] = self.DATA['TEMP']['cpu0_temp']['Value']
        else:
            self.DATA['TEMP']['cpu1_temp']['Value'] = d["Information"][8]["temp1"].split(" ")[0]
            self.DATA['TEMP']['cpu1_temp']['LowThd'] = g["Information"]["cpu1_temp_L"]
            self.DATA['TEMP']['cpu1_temp']['HighThd'] = g["Information"]["cpu1_temp_H"]

            cpu0_temp = self.DATA['TEMP']['cpu0_temp']
            cpu1_temp = self.DATA['TEMP']['cpu1_temp']
            if self._validate_sensor(cpu0_temp):
                if self._validate_sensor(cpu1_temp):
                    val = (float(cpu0_temp["Value"]) + float(cpu1_temp["Value"])) / 2
                else:
                    val = float(cpu0_temp["Value"])
            else:
                if self._validate_sensor(cpu1_temp):
                    val = float(cpu1_temp["Value"])
                else:
                    val = (float(cpu0_temp["Value"]) + float(cpu1_temp["Value"])) / 2
            self.DATA['TEMP']['CPU_TEMP']['Value'] = val
        self.DATA['TEMP']['CPU_TEMP']['LowThd'] = g["Information"]["cpu0_temp_L"]
        self.DATA['TEMP']['CPU_TEMP']['HighThd'] = g["Information"]["cpu0_temp_H"]
        

        #PSU: PSU1/PSU2
        #judge PSU1/PSU2 present or not
        cmd = subprocess.Popen("psuutil status", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        info, err = cmd.communicate()
        if len(err) != 0:
            print("failed to get PSU present infomation")
            return -1
        info = info.decode(errors="ignore")
        info1=info.splitlines() #PSU1: info1[2], PSU2: info1[3]

        #PSU1: psu_driver-i2c-7-58
        if "PSU 1  OK" != info1[2]:
            del self.DATA['PSU1']
        else:
            self.DATA['PSU1']['vin']['Value'] = d["Information"][9]["in0"].split(" ")[0]
            self.DATA['PSU1']['iin']['Value'] = d["Information"][9]["curr1"].split(" ")[0]
            if d["Information"][9]["power1"].split(" ")[1] == 'mW':
                power1=float(d["Information"][9]["power1"].split(" ")[0]) / 900
                self.DATA['PSU1']['pin']['Value'] = power1
            elif d["Information"][9]["power1"].split(" ")[1] == 'kW':
                power1=float(d["Information"][9]["power1"].split(" ")[0]) * 900
                self.DATA['PSU1']['pin']['Value'] = power1
            else:
                self.DATA['PSU1']['pin']['Value'] = d["Information"][9]["power1"].split(" ")[0]
            self.DATA['PSU1']['vout']['Value'] = d["Information"][9]["in1"].split(" ")[0]
            self.DATA['PSU1']['iout']['Value'] = d["Information"][9]["curr2"].split(" ")[0]
            if d["Information"][9]["power2"].split(" ")[1] == 'mW':
                power2=float(d["Information"][9]["power2"].split(" ")[0]) / 900
                self.DATA['PSU1']['pout']['Value'] = power2
            elif d["Information"][9]["power2"].split(" ")[1] == 'kW':
                power2=float(d["Information"][9]["power2"].split(" ")[0]) * 900
                self.DATA['PSU1']['pout']['Value'] = power2
            else:
                self.DATA['PSU1']['pout']['Value'] = d["Information"][9]["power2"].split(" ")[0]
            self.DATA['PSU1']['fan']['Value'] = d["Information"][9]["fan1"].split(" ")[0]
            self.DATA['PSU1']['Ambient_Temperature']['Value'] = d["Information"][9]["temp1"].split(" ")[0]
            self.DATA['PSU1']['Primary_Temperature']['Value'] = d["Information"][9]["temp2"].split(" ")[0]
            self.DATA['PSU1']['Secondary_Temperature']['Value'] = d["Information"][9]["temp3"].split(" ")[0]

            self.DATA['PSU1']['vin']['LowThd'] = g["Information"]["psu1_vin_L"]
            self.DATA['PSU1']['vin']['HighThd'] = g["Information"]["psu1_vin_H"]
            self.DATA['PSU1']['iin']['LowThd'] = g["Information"]["psu1_iin_L"]
            self.DATA['PSU1']['iin']['HighThd'] = g["Information"]["psu1_iin_H"]
            self.DATA['PSU1']['pin']['LowThd'] = g["Information"]["psu1_pin_L"]
            self.DATA['PSU1']['pin']['HighThd'] = g["Information"]["psu1_pin_H"]
            self.DATA['PSU1']['vout']['LowThd'] = g["Information"]["psu1_vout_L"]
            self.DATA['PSU1']['vout']['HighThd'] = g["Information"]["psu1_vout_H"]
            self.DATA['PSU1']['iout']['LowThd'] = g["Information"]["psu1_iout_L"]
            self.DATA['PSU1']['iout']['HighThd'] = g["Information"]["psu1_iout_H"]
            self.DATA['PSU1']['pout']['LowThd'] = g["Information"]["psu1_pout_L"]
            self.DATA['PSU1']['pout']['HighThd'] = g["Information"]["psu1_pout_H"]
            self.DATA['PSU1']['fan']['LowThd'] = g["Information"]["psu1_fan_L"]
            self.DATA['PSU1']['fan']['HighThd'] = g["Information"]["psu1_fan_H"]
            self.DATA['PSU1']['Ambient_Temperature']['LowThd'] = g["Information"]["psu1_temp1_L"]
            self.DATA['PSU1']['Ambient_Temperature']['HighThd'] = g["Information"]["psu1_temp1_H"]
            self.DATA['PSU1']['Primary_Temperature']['LowThd'] = g["Information"]["psu1_temp2_L"]
            self.DATA['PSU1']['Primary_Temperature']['HighThd'] = g["Information"]["psu1_temp2_H"]
            self.DATA['PSU1']['Secondary_Temperature']['LowThd'] = g["Information"]["psu1_temp3_L"]
            self.DATA['PSU1']['Secondary_Temperature']['HighThd'] = g["Information"]["psu1_temp3_H"]

        #PSU2: psu_driver-i2c-7-59
        if "PSU 2  OK" != info1[3]:
            del self.DATA['PSU2']
        else:
            self.DATA['PSU2']['vin']['Value'] = d["Information"][10]["in0"].split(" ")[0]
            self.DATA['PSU2']['iin']['Value'] = d["Information"][10]["curr1"].split(" ")[0]
            if d["Information"][10]["power1"].split(" ")[1] == 'mW':
                power1=float(d["Information"][10]["power1"].split(" ")[0]) / 1000
                self.DATA['PSU2']['pin']['Value'] = power1
            elif d["Information"][10]["power1"].split(" ")[1] == 'kW':
                power1=float(d["Information"][10]["power1"].split(" ")[0]) * 1000
                self.DATA['PSU2']['pin']['Value'] = power1
            else:
                self.DATA['PSU2']['pin']['Value'] = d["Information"][10]["power1"].split(" ")[0]
            self.DATA['PSU2']['vout']['Value'] = d["Information"][10]["in1"].split(" ")[0]
            self.DATA['PSU2']['iout']['Value'] = d["Information"][10]["curr2"].split(" ")[0]
            if d["Information"][10]["power2"].split(" ")[1] == 'mW':
                power2=float(d["Information"][10]["power2"].split(" ")[0]) / 1000
                self.DATA['PSU2']['pout']['Value'] = power2
            elif d["Information"][10]["power2"].split(" ")[1] == 'kW':
                power2=float(d["Information"][10]["power2"].split(" ")[0]) * 1000
                self.DATA['PSU2']['pout']['Value'] = power2
            else:
                self.DATA['PSU2']['pout']['Value'] = d["Information"][10]["power2"].split(" ")[0]
            self.DATA['PSU2']['fan']['Value'] = d["Information"][10]["fan1"].split(" ")[0]
            self.DATA['PSU2']['Ambient_Temperature']['Value'] = d["Information"][10]["temp1"].split(" ")[0]
            self.DATA['PSU2']['Primary_Temperature']['Value'] = d["Information"][10]["temp2"].split(" ")[0]
            self.DATA['PSU2']['Secondary_Temperature']['Value'] = d["Information"][10]["temp3"].split(" ")[0]

            self.DATA['PSU2']['vin']['LowThd'] = g["Information"]["psu2_vin_L"]
            self.DATA['PSU2']['vin']['HighThd'] = g["Information"]["psu2_vin_H"]
            self.DATA['PSU2']['iin']['LowThd'] = g["Information"]["psu2_iin_L"]
            self.DATA['PSU2']['iin']['HighThd'] = g["Information"]["psu2_iin_H"]
            self.DATA['PSU2']['pin']['LowThd'] = g["Information"]["psu2_pin_L"]
            self.DATA['PSU2']['pin']['HighThd'] = g["Information"]["psu2_pin_H"]
            self.DATA['PSU2']['vout']['LowThd'] = g["Information"]["psu2_vout_L"]
            self.DATA['PSU2']['vout']['HighThd'] = g["Information"]["psu2_vout_H"]
            self.DATA['PSU2']['iout']['LowThd'] = g["Information"]["psu2_iout_L"]
            self.DATA['PSU2']['iout']['HighThd'] = g["Information"]["psu2_iout_H"]
            self.DATA['PSU2']['pout']['LowThd'] = g["Information"]["psu2_pout_L"]
            self.DATA['PSU2']['pout']['HighThd'] = g["Information"]["psu2_pout_H"]
            self.DATA['PSU2']['fan']['LowThd'] = g["Information"]["psu2_fan_L"]
            self.DATA['PSU2']['fan']['HighThd'] = g["Information"]["psu2_fan_H"]
            self.DATA['PSU2']['Ambient_Temperature']['LowThd'] = g["Information"]["psu2_temp1_L"]
            self.DATA['PSU2']['Ambient_Temperature']['HighThd'] = g["Information"]["psu2_temp1_H"]
            self.DATA['PSU2']['Primary_Temperature']['LowThd'] = g["Information"]["psu2_temp2_L"]
            self.DATA['PSU2']['Primary_Temperature']['HighThd'] = g["Information"]["psu2_temp2_H"]
            self.DATA['PSU2']['Secondary_Temperature']['LowThd'] = g["Information"]["psu2_temp3_L"]
            self.DATA['PSU2']['Secondary_Temperature']['HighThd'] = g["Information"]["psu2_temp3_H"]


        #char of Value/LowThd/HighThd to float
        for index1 in self.DATA:
            if index1 != 'SYS':
                for index2 in self.DATA[index1]:
                    if self.DATA[index1][index2]['Value'] != 'N/A':
                        self.DATA[index1][index2]['Value'] = float(self.DATA[index1][index2]['Value'])
                    if self.DATA[index1][index2]['LowThd'] != 'N/A':
                        self.DATA[index1][index2]['LowThd'] = float(self.DATA[index1][index2]['LowThd'])
                    if self.DATA[index1][index2]['HighThd'] != 'N/A':
                        self.DATA[index1][index2]['HighThd'] = float(self.DATA[index1][index2]['HighThd'])

        return True

    def get_all(self):
        self.ipmi_poll_thermal()
        return self.DATA

    def _get_thermal_val(self, thermal_num):
        if thermal_num < self.get_idx_thermal_start() or thermal_num > self.get_num_thermals() :
            logging.debug('GET. Parameter error. thermal_num:%d', thermal_num)
            return None
        self.ipmi_poll_thermal()
        return self.DATA[thermal_num]['value']

def main():
    sensor = SensorUtil()
    print "get_all=%s" %sensor.get_all()

if __name__ == '__main__':
    main()
