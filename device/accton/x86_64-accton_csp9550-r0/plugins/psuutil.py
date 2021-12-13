#!/usr/bin/env python

#############################################################################
# Accton
#
# Module contains an implementation of SONiC PSU Base API and
# provides the PSUs PowerStatus which are available in the platform
#
#############################################################################
import commands
import time
import os.path
import re
import sys
import json
try:
    from sonic_psu.psu_base import PsuBase
except ImportError as e:
    raise ImportError (str(e) + "- required module not found")


IPMI_CMD ="ipmitool sensor" 
subcmd = "grep PSU "

###240.1.1.1 is BMC usb0 ip addr###
CURL_CMD1 = "curl -s http://240.1.1.1:8080/api/sys/psu_psu1"
CURL_CMD2 = "curl -s http://240.1.1.1:8080/api/sys/psu_psu2"

class PsuUtil(PsuBase):
    """Platform-specific PSUutil class"""

    IPMIT_INTV = 10 # in seconds
    _ipmi_last_poll = 0
    DATA = {'Number': 0,
            'PSU1': {'name':'psu1',
                'Present':False,
                'Status':False,
                'PIN':0.0,
                'POUT':0.0,
                'VIN':0.0,
                'VOUT':0.0,
                'TEMP':0.0,
                'FAN':0
                #'PN':"na",
                #'SN':"na",
                },
            'PSU2': {'name':'psu2',
                'Present':False,
                'Status':False,
                'PIN':0.0,
                'POUT':0.0,
                'VIN':0.0,
                'VOUT':0.0,
                'TEMP':0.0,
                'FAN':0
                #'PN':"na",
                #'SN':"na",
                }
           }

    _present_read_time = 0
    def __init__(self):
        self.num = 0
        PsuBase.__init__(self)

    def get_num_psus(self):
        return len(self.DATA)-1

    def _syscmd(self, cmd):
        status, output = commands.getstatusoutput(cmd)
        return status, output

    def ipmit_poll_psu(self):
        now = time.time()
        if now < (self._ipmi_last_poll + self.IPMIT_INTV):
            return True
        else:
            self._ipmi_last_poll = now
        cmd = IPMI_CMD + "|" + subcmd
        st, log = self._syscmd(cmd)
        if st == 0:
            log = re.sub(r' ', "", log)

            for line in log.split("\n"):
                for d in self.DATA:
                    if d != 'Number':
                        if str.upper(self.DATA[d]['name']) in line:
                            if 'PIN' in line:
                                self.DATA[d]['PIN'] = line.split('|')[1]
                            if 'POUT' in line:
                                self.DATA[d]['POUT'] = line.split('|')[1]
                            if 'VIN' in line:
                                self.DATA[d]['VIN'] = line.split('|')[1]
                            if 'VOUT' in line:
                                self.DATA[d]['VOUT'] = line.split('|')[1]
                            if 'TEMP' in line:
                                self.DATA[d]['TEMP'] = line.split('|')[1]
                            if 'FAN' in line:
                                self.DATA[d]['FAN'] = line.split('|')[1]
                    
                        if self.DATA[d]['PIN'] == 'na':
                            self.DATA[d]['Status'] = False
                            self.DATA[d]['Present'] = False
                        else:
                            try:
                                self.DATA[d]['PIN'] = float(self.DATA[d]['PIN'])
                                if self.DATA[d]['PIN'] == 0:
                                    self.DATA[d]['Status'] = False
                                    self.DATA[d]['Present'] = True
                                else:
                                    self.DATA[d]['Status'] = True
                                    self.DATA[d]['Present'] = True
                            except ValueError:
                                self.DATA[d]['Status'] = False
                                self.DATA[d]['Present'] = False
            self.DATA['Number'] =  self.num
            return True

        else:
            st1, log1 = self._syscmd(CURL_CMD1)
            if st1 != 0:
                raise 'error on syscmd'
            st2, log2 = self._syscmd(CURL_CMD2)
            if st2 != 0:
                raise 'error on syscmd'
            log1 = log1 + "\n"
            log = log1 + log2
            for line in log.split("\n"):
                for d in self.DATA:
                    if d != 'Number':
                        if self.DATA[d]['name'] in line:
                            self.num = self.num + 1
                            value = json.loads(line)
                            #self.DATA[d]['PN'] = value['Information'].get('MFR_MODEL', "na")
                            #self.DATA[d]['SN'] = value['Information'].get('MFR_SERIAL', "na")
                            self.DATA[d]['PIN'] = value['Information'].get('READ_PIN', "na")
                            self.DATA[d]['VIN'] = value['Information'].get('READ_VIN', "na")
                            self.DATA[d]['POUT'] = value['Information'].get('READ_POUT', "na")
                            self.DATA[d]['VOUT'] = value['Information'].get('READ_VOUT', "na")
                            self.DATA[d]['TEMP'] = value['Information'].get('READ_TEMPERATURE_1', "na")
                            self.DATA[d]['FAN'] = value['Information'].get('READ_FAN_SPEED_1', "na")
                            if value['Information'].get('PWR_OK', False) == False:        
                                self.DATA[d]['Status'] = False
                            else:
                                if value['Information'].get('PWR_OK', False) == "1":
                                    self.DATA[d]['Status'] = True
                                else:
                                    self.DATA[d]['Status'] = False
                                    
                            if value['Information'].get('READ_VIN', "na") == "na":
                                self.DATA[d]['Present'] = False
                            else:
                                if value['Information'].get('READ_VIN', "na") == "0.00 W":
                                    self.DATA[d]['Present'] = True
                                else:
                                    self.DATA[d]['Present'] = True

            self.DATA['Number'] =  self.num
            return True

    def get_all(self):
        self.ipmit_poll_psu()
        return self.DATA

    def get_psu_status(self, index):
        if index == 1:
            self.ipmit_poll_psu()
            d = self.DATA['PSU1']
            return d['Status']
        elif index == 2:
            self.ipmit_poll_psu()
            d = self.DATA['PSU2']
            return d['Status']
        else:
            return False

    def get_psu_presence(self, index):
        if index == 1:
            self.ipmit_poll_psu()
            d = self.DATA['PSU1']
            return d['Present']
        elif index == 2:
            self.ipmit_poll_psu()
            d = self.DATA['PSU2']
            return d['Present']
        else:
            return False

    #def get_psu_sn(self, index):
    #    if index == 1:
    #        self.ipmit_poll_psu()
    #        d = self.DATA['PSU1']
    #        return d['SN']
    #    elif index == 2:
    #        self.ipmit_poll_psu()
    #        d = self.DATA['PSU2']
    #        return d['SN']
    #    else:
    #        return False

    #def get_psu_pn(self, index):
    #    if index == 1:
    #        self.ipmit_poll_psu()
    #        d = self.DATA['PSU1']
    #        return d['PN']
    #    elif index == 2:
    #        self.ipmit_poll_psu()
    #        d = self.DATA['PSU2']
    #        return d['PN']
    #    else:
    #        return False


def main():
    psu = PsuUtil()
    print("\nlog:")
    #print "get_all=%s" %psu.get_all()
    #print "get_psu_sn 1=%r" %psu.get_psu_sn(1)
    #print "get_psu_pn 2=%r" %psu.get_psu_pn(2)