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
# ------------------------------------------------------------------

try:
    import time
    import logging
    import commands
    import re
    from collections import namedtuple
except ImportError as e:
    raise ImportError('%s - required module not found' % str(e))


class FanUtil(object):
    """Platform-specific FanUtil class"""

    """CSP9550 has 5 set of fans, each set has 2 fans.
       FAN_NUM_*_1_IDX is outer fan, RPM is higher.
       FAN_NUM_*_2_IDX is inner fan, RPM is lower."""
    FAN_NUM_ON_MAIN_BROAD = 10
    FAN_NUM_1_1_IDX = 1
    FAN_NUM_1_2_IDX = 2
    FAN_NUM_2_1_IDX = 3
    FAN_NUM_2_2_IDX = 4
    FAN_NUM_3_1_IDX = 5
    FAN_NUM_3_2_IDX = 6
    FAN_NUM_4_1_IDX = 7
    FAN_NUM_4_2_IDX = 8
    FAN_NUM_5_1_IDX = 9
    FAN_NUM_5_2_IDX = 10

    IPMI_INTV = 10 # in seconds
    _ipmi_last_poll= 0
    """ Dictionary where
        key1 = fan id index (integer) starting from 1 """
    DATA = {FAN_NUM_1_1_IDX: {'name':'Fan1_1', 'status':'nr', 'rpm':0},
            FAN_NUM_1_2_IDX: {'name':'Fan1_2', 'status':'nr', 'rpm':0},
            FAN_NUM_2_1_IDX: {'name':'Fan2_1', 'status':'nr', 'rpm':0},
            FAN_NUM_2_2_IDX: {'name':'Fan2_2', 'status':'nr', 'rpm':0},
            FAN_NUM_3_1_IDX: {'name':'Fan3_1', 'status':'nr', 'rpm':0},
            FAN_NUM_3_2_IDX: {'name':'Fan3_2', 'status':'nr', 'rpm':0},
            FAN_NUM_4_1_IDX: {'name':'Fan4_1', 'status':'nr', 'rpm':0},
            FAN_NUM_4_2_IDX: {'name':'Fan4_2', 'status':'nr', 'rpm':0},
            FAN_NUM_5_1_IDX: {'name':'Fan5_1', 'status':'nr', 'rpm':0},
            FAN_NUM_5_2_IDX: {'name':'Fan5_2', 'status':'nr', 'rpm':0}
           }

    ipmi_cmd = "ipmitool sensor"
    subcmd = "grep Fan"
    max_rpm_1 = 29000 # max RPM of outer fan
    max_rpm_2 = 23680 # max RPM of inner fan

    def get_num_fans(self):
        return self.FAN_NUM_ON_MAIN_BROAD

    def get_idx_fan_start(self):
        return self.FAN_NUM_1_1_IDX

    def _syscmd(self, cmd):
        status, output = commands.getstatusoutput(cmd)
        return status, output

    def ipmi_poll_fan(self):
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

        for d in self.DATA:
            self.DATA[d]['status'] = log.split('\n')[d-1].split('|')[3]
            temp_value = log.split('\n')[d-1].split('|')[1]
            try:
                temp_value = int(float(temp_value))
                self.DATA[d]['rpm'] = temp_value
            except ValueError:
                self.DATA[d]['rpm'] = 0

        return True

    def get_all(self):
        self.ipmi_poll_fan()
        return self.DATA

    def get_fan_fault(self, fan_num):
        if fan_num < self.FAN_NUM_1_1_IDX or fan_num > self.FAN_NUM_ON_MAIN_BROAD:
            logging.debug('GET. Parameter error. fan_num:%d', fan_num)
            return None
        self.ipmi_poll_fan()
        if self.DATA[fan_num]['status'] != 'ok':
            return True

        return False

    def get_fan_duty_cycle(self):
        self.ipmi_poll_fan()
        #Get a none zero outer fan rpm as current duty cycle.
        for fan_num in range((self.FAN_NUM_ON_MAIN_BROAD/2)):
            temp_rpm = self.DATA[fan_num*2+1]['rpm']
            if temp_rpm != 0:
                break

        return int(temp_rpm*100/self.max_rpm_1)

    def set_fan_duty_cycle(self, val):
        cmd = "ipmitool raw 0x34 0xaa 0x5a 0x54 0x40 0x04 0x03 0xff > unclock"
        st, log = self._syscmd(cmd)
        if st != 0:
            raise 'error on syscmd'
        val = hex(val)
        cmd = "ipmitool raw 0x34 0xaa 0x5a 0x54 0x40 0x04 0x01 0xff " + val + " > " + val
        st, log = self._syscmd(cmd)
        if st != 0:
            raise 'error on syscmd'
        st, log = self._syscmd(cmd)
        if st != 0:
            raise 'error on syscmd'
        return True

    def get_fanr_speed(self, fan_num):
        if fan_num < self.FAN_NUM_1_1_IDX or fan_num > self.FAN_NUM_ON_MAIN_BROAD:
            logging.debug('GET. Parameter error. fan_num:%d', fan_num)
            return None
        self.ipmi_poll_fan()
        return self.DATA[fan_num]['rpm']

    def get_fan_status(self, fan_num):
        if fan_num < self.FAN_NUM_1_1_IDX or fan_num > self.FAN_NUM_ON_MAIN_BROAD:
            logging.debug('GET. Parameter error. fan_num:%d', fan_num)
            return None
        self.ipmi_poll_fan()
        if self.DATA[fan_num]['status'] == 'ok':
            return True

        return False

def main():
    fan = FanUtil()
    #print "get_idx_fan_start=%d" %fan.get_idx_fan_start()
    #print "get_num_fans=%d" %fan.get_num_fans()
    #print "fan1=%d" %fan.get_fanr_speed(9)
    #print "fan5=%d" %fan.get_fan_status(5)
    #fan.set_fan_duty_cycle(30)
    #print "duty_cycle=%d" %fan.get_fan_duty_cycle()
    #print "get_fan_fault=%d" %fan.get_fan_fault(3)
    #print "get_fan_fault=%d" %fan.get_fan_fault(10)
    #print "get_all=%s" %fan.get_all()

if __name__ == '__main__':
    main()
