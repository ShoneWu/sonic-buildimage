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
# ------------------------------------------------------------------

try:
    import os
    import time
    import logging
    import glob
    import commands
    import re
    from collections import namedtuple
except ImportError as e:
    raise ImportError('%s - required module not found' % str(e))


def log_os_system(cmd, show):
    logging.info('Run :'+cmd)
    status = 1
    output = ""
    status, output = commands.getstatusoutput(cmd)
    if show:
        print "ACC: " + str(cmd) + " , result:"+ str(status)
   
    if status:
        logging.info('Failed :'+cmd)
        if show:
            print('Failed :'+cmd)
    return  status, output


class ThermalUtil(object):
    """Platform-specific ThermalUtil class"""

    THERMAL_NUM_MAX = 34
    THERMAL_NUM_1_IDX = 1 # Temp_LM75_Power
    THERMAL_NUM_2_IDX = 2 # Temp_LM75_LEFT
    THERMAL_NUM_3_IDX = 3 # Temp_LM75_HS
    THERMAL_NUM_4_IDX = 4 # Temp_LM75_CPU0
    THERMAL_NUM_5_IDX = 5 # Temp_LM75_CPU1
    THERMAL_NUM_6_IDX = 6 # Temp_LM75_PCH
    THERMAL_NUM_7_IDX = 7 # ADC_SB_P12V
    THERMAL_NUM_8_IDX = 8 # ADC_SB_P5V
    THERMAL_NUM_9_IDX = 9 # ADC_SB_P3V3
    THERMAL_NUM_10_IDX = 10 # ADC_SB_P1V2_AUX
    THERMAL_NUM_11_IDX = 11 # ADC_SB_P1V15_AUX
    THERMAL_NUM_12_IDX = 12 # ADC_SB_P1V05_PCH
    THERMAL_NUM_13_IDX = 13 # ADC_SB_PVNN_PCH
    THERMAL_NUM_14_IDX = 14 # ADC_SB_P1V8_PCH
    THERMAL_NUM_15_IDX = 15 # ADC_SB_P1V0_LOM
    THERMAL_NUM_16_IDX = 16 # PSU1_TEMP
    THERMAL_NUM_17_IDX = 17 # PSU2_TEMP
    THERMAL_NUM_18_IDX = 18 # Temp_PECI_CPU0
    THERMAL_NUM_19_IDX = 19 # Temp_PECI_CPU1
    THERMAL_NUM_20_IDX = 20 # Temp_TMP431
    THERMAL_NUM_21_IDX = 21 # IR3580_Vin
    THERMAL_NUM_22_IDX = 22 # IR3580_Vout
    THERMAL_NUM_23_IDX = 23 # IR3580_Iin
    THERMAL_NUM_24_IDX = 24 # IR3580_Iout
    THERMAL_NUM_25_IDX = 25 # IR3580_Pin
    THERMAL_NUM_26_IDX = 26 # IR3580_Pout
    THERMAL_NUM_27_IDX = 27 # IR3580_Temp
    THERMAL_NUM_28_IDX = 28 # IR3584_Vin
    THERMAL_NUM_29_IDX = 29 # IR3584_Vout
    THERMAL_NUM_30_IDX = 30 # IR3584_Iin
    THERMAL_NUM_31_IDX = 31 # IR3584_Iout
    THERMAL_NUM_32_IDX = 32 # IR3584_Pin
    THERMAL_NUM_33_IDX = 33 # IR3584_Pout
    THERMAL_NUM_34_IDX = 34 # IR3584_Temp
    
    IPMI_INTV = 10 # in seconds
    _ipmi_last_poll= 0

    """ Dictionary where
        key1 = thermal id index (integer) starting from 1 """
    DATA = {THERMAL_NUM_1_IDX: {'name':'Temp_LM75_Power', 'status':'na', 'value':0.0},
            THERMAL_NUM_2_IDX: {'name':'Temp_LM75_LEFT', 'status':'na', 'value':0.0},
            THERMAL_NUM_3_IDX: {'name':'Temp_LM75_HS', 'status':'na', 'value':0.0},
            THERMAL_NUM_4_IDX: {'name':'Temp_LM75_CPU0', 'status':'na', 'value':0.0},
            THERMAL_NUM_5_IDX: {'name':'Temp_LM75_CPU1', 'status':'na', 'value':0.0},
            THERMAL_NUM_6_IDX: {'name':'Temp_LM75_PCH', 'status':'na', 'value':0.0},
            THERMAL_NUM_7_IDX: {'name':'ADC_SB_P12V', 'status':'na', 'value':0.0},
            THERMAL_NUM_8_IDX: {'name':'ADC_SB_P5V', 'status':'na', 'value':0.0},
            THERMAL_NUM_9_IDX: {'name':'ADC_SB_P3V3', 'status':'na', 'value':0.0},
            THERMAL_NUM_10_IDX: {'name':'ADC_SB_P1V2_AUX', 'status':'na', 'value':0.0},
            THERMAL_NUM_11_IDX: {'name':'ADC_SB_P1V15_AUX', 'status':'na', 'value':0.0},
            THERMAL_NUM_12_IDX: {'name':'ADC_SB_P1V05_PCH', 'status':'na', 'value':0.0},
            THERMAL_NUM_13_IDX: {'name':'ADC_SB_PVNN_PCH', 'status':'na', 'value':0.0},
            THERMAL_NUM_14_IDX: {'name':'ADC_SB_P1V8_PCH', 'status':'na', 'value':0.0},
            THERMAL_NUM_15_IDX: {'name':'ADC_SB_P1V0_LOM', 'status':'na', 'value':0.0},
            THERMAL_NUM_16_IDX: {'name':'PSU1_TEMP', 'status':'na', 'value':0.0},
            THERMAL_NUM_17_IDX: {'name':'PSU2_TEMP', 'status':'na', 'value':0.0},
            THERMAL_NUM_18_IDX: {'name':'Temp_PECI_CPU0', 'status':'na', 'value':0.0},
            THERMAL_NUM_19_IDX: {'name':'Temp_PECI_CPU1', 'status':'na', 'value':0.0},
            THERMAL_NUM_20_IDX: {'name':'Temp_TMP431', 'status':'na', 'value':0.0},
            THERMAL_NUM_21_IDX: {'name':'IR3580_Vin', 'status':'na', 'value':0.0},
            THERMAL_NUM_22_IDX: {'name':'IR3580_Vout', 'status':'na', 'value':0.0},
            THERMAL_NUM_23_IDX: {'name':'IR3580_Iin', 'status':'na', 'value':0.0},
            THERMAL_NUM_24_IDX: {'name':'IR3580_Iout', 'status':'na', 'value':0.0},
            THERMAL_NUM_25_IDX: {'name':'IR3580_Pin', 'status':'na', 'value':0.0},
            THERMAL_NUM_26_IDX: {'name':'IR3580_Pout', 'status':'na', 'value':0.0},
            THERMAL_NUM_27_IDX: {'name':'IR3580_Temp', 'status':'na', 'value':0.0},
            THERMAL_NUM_28_IDX: {'name':'IR3584_Vin', 'status':'na', 'value':0.0},
            THERMAL_NUM_29_IDX: {'name':'IR3584_Vout', 'status':'na', 'value':0.0},
            THERMAL_NUM_30_IDX: {'name':'IR3584_Iin', 'status':'na', 'value':0.0},
            THERMAL_NUM_31_IDX: {'name':'IR3584_Iout', 'status':'na', 'value':0.0},
            THERMAL_NUM_32_IDX: {'name':'IR3584_Pin', 'status':'na', 'value':0.0},
            THERMAL_NUM_33_IDX: {'name':'IR3584_Pout', 'status':'na', 'value':0.0},
            THERMAL_NUM_34_IDX: {'name':'IR3584_Temp', 'status':'na', 'value':0.0},
           }
           
    ipmi_cmd = "ipmitool sensor" 
    subcmd = "grep 'TEMP\|ADC\|Temp\|IR3580\|IR3584'"

    def get_num_thermals(self):
        return self.THERMAL_NUM_MAX

    def get_idx_thermal_start(self):
        return self.THERMAL_NUM_1_IDX

    def _syscmd(self, cmd):
        status, output = commands.getstatusoutput(cmd)
        return status, output

    def ipmi_poll_thermal(self):
        now = time.time()
        if now < (self._ipmi_last_poll + self.IPMI_INTV):
            return True    
        else:
            self._ipmi_last_poll = now
        cmd = self.ipmi_cmd + "|" + self.subcmd
        st, log = self._syscmd(cmd)
        if st != 0:
            raise 'error on syscmd'
        log = re.sub(r' ', "", log)

        for line in log.split("\n"):
            for d in self.DATA:
                if self.DATA[d]['name'] in line:
                    try:
                        float(line.split('|')[1])
                        self.DATA[d]['value'] = float(line.split('|')[1])
                    except ValueError:
                        self.DATA[d]['value'] = 0
                    self.DATA[d]['status'] = line.split('|')[3]
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
    thermal = ThermalUtil()
    #for x in range(1,35):
    #    print "termal=%f" % thermal._get_thermal_val(x)
    #print "get_al1=%s" %thermal.get_all()

if __name__ == '__main__':
    main()
