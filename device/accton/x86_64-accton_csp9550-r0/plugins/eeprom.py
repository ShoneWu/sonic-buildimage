#!/usr/bin/env python

try:
    import exceptions
    import binascii
    import time
    import optparse
    import warnings
    import commands
    import os
    import sys
    from sonic_eeprom import eeprom_base
    from sonic_eeprom import eeprom_tlvinfo
    import subprocess
except ImportError, e:
    raise ImportError (str(e) + "- required module not found")

class board(eeprom_tlvinfo.TlvInfoDecoder):
    _TLV_INFO_MAX_LEN = 256
    def __init__(self, name, path, cpld_root, ro):
        self.eeprom_path = "/sys/bus/i2c/devices/1-0056/eeprom"
        #Two i2c buses might get flipped order, check them both.
        if not os.path.exists(self.eeprom_path):
            self.eeprom_path = "/sys/bus/i2c/devices/0-0056/eeprom"
        super(board, self).__init__(self.eeprom_path, 0, '', True)

    def _syscmd(self, cmd):
        status, output = commands.getstatusoutput(cmd)
        return status, output

    def _get_eeprom_content(self):
        lab_ver = "R01"
        onie_ver = "2019.03.05"
        diag_ver = "0.0.0.1"
        manuf_name = "Joytech"
        manuf_country = "CN"
           
        mfg_date_cmd = "ipmitool fru print 0 | grep 'Board Mfg Date'"
        platf_name_cmd = "ipmitool fru print 0 | grep 'Product Extra'"
        manuf_cmd ="ipmitool fru print 0 | grep 'Board Mfg   '"
        mac_addr_cmd = "ipmitool fru print 0 | grep 'Board Extra'"
        serial_num_cmd = "ipmitool fru print 0 | grep 'Chassis Serial'"
        part_num_cmd = "ipmitool fru print 0 | grep 'Board Part Number'"
        product_name_cmd = "ipmitool fru print 0 | grep 'Product Part Number'"

        '''
        Get Manufacture Date from fru eeprom.
        '''
        st, da = self._syscmd(mfg_date_cmd)
        if st != 0:
            raise 'error on get mfg_data syscmd'

        temp = da.split(':',1)
        mfg_date_data = temp[1].strip()

        '''
        Get Platform Name.
        '''
        st, da = self._syscmd(platf_name_cmd)
        if st != 0:
            raise 'error on get platf_name syscmd'

        temp = da.split(':')[1]
        platf_name_data = temp.strip()

        '''
        Get Manufacturer and Manufacture Country from fru eeprom.
        '''
        st, da = self._syscmd(manuf_cmd)
        if st != 0:
            raise 'error on get manuf syscmd'

        temp = da.split(':')[1]
        manuf_data = temp.strip()
        verder_name = manuf_data[0:6]

        '''
        Get Base MAC Address from eth0.
        '''
        st, da = self._syscmd(mac_addr_cmd)
        if st != 0:
            raise 'error on get mac_addr syscmd'
        mac_addr = da.split()[3].strip()
        mac_str = mac_addr.split(':')
        for i in range(len(mac_str)):
            mac_str[i] = '0x'+mac_str[i]

        '''
        Get Serial Number from fru eeprom.
        '''
        st, da = self._syscmd(serial_num_cmd)
        if st != 0:
            raise 'error on get serial_num syscmd'

        temp = da.split(':')[1]
        serial_data = temp.strip()

        '''
        Get Part Number from fru eeprom.
        '''
        st, da = self._syscmd(part_num_cmd)
        if st != 0:
            raise 'error on get part_num syscmd'

        temp = da.split(':')[1]
        part_num_data = temp.strip()

        '''
        Get Product Name from fru eeprom.
        '''
        st, da = self._syscmd(product_name_cmd)
        if st != 0:
            raise 'error on get product_name syscmd'

        temp = da.split(':')[1]
        product_name_data = temp.strip()

        '''
        This is tlv_eeprom_content without crc32 checksum.
        '''
        tlv_eeprom_content = chr(37)+chr(len(mfg_date_data))+mfg_date_data+chr(39)+chr(len(lab_ver))+lab_ver+chr(40) \
                            +chr(len(platf_name_data))+platf_name_data+chr(43)+chr(len(manuf_name))+manuf_name+chr(44) \
                            +chr(len(manuf_country))+manuf_country+chr(36)+chr(6)+chr(int(mac_str[0],16))+chr(int(mac_str[1],16)) \
                            +chr(int(mac_str[2],16))+chr(int(mac_str[3],16))+chr(int(mac_str[4],16))+chr(int(mac_str[5],16)) \
                            +chr(35)+chr(len(serial_data))+serial_data+chr(34)+chr(len(part_num_data))+part_num_data+chr(33) \
                            +chr(len(product_name_data))+product_name_data+chr(42)+chr(2)+chr(0)+chr(9)+chr(45) \
                            +chr(len(verder_name))+verder_name+chr(41)+chr(len(onie_ver))+onie_ver+chr(46)+chr(len(diag_ver)) \
                            +diag_ver+chr(254)+chr(4)
        return tlv_eeprom_content

    def _get_eeprom_hdr(self):

        content_str = self._get_eeprom_content()
        '''
        crc32 checksum len is 4 character.
        '''
        tlv_hdr = 'TlvInfo'+chr(0)+chr(1)+chr(0)+chr((len(content_str)+4))
        return tlv_hdr
        
    def _calculate_crc32_checksum(self):
        crc = 0
        hdr_str = self._get_eeprom_hdr()
        content_str = self._get_eeprom_content()
        total_str = hdr_str+content_str
        crc = binascii.crc32(total_str,crc)&0xffffffff
        crcstr = hex(crc)[2:]
        crc_chr=[]
        for k in range(0,len(crcstr),2):
            crc_chr.append(chr(int(crcstr[k:k+2],16)))

        return crc_chr
        
    def _eeprom_content_len(self):
       '''
       Get tlv eeprom total len(tlv header + eeprom content + crc32 checksum).
       '''
       content_len = 0
       content_str = self._get_eeprom_content()
       '''
       crc32 checksum len is 4 character.
       '''
       content_len = len(content_str)+4
       return content_len
            
    def read_eeprom_bytes(self, byteCount, offset=0):
        #print("byteCount is ",byteCount," offset is ",offset)
        if byteCount == 11:
            '''
            Get tlv eeprom header.
            '''
            tlv_hdr = self._get_eeprom_hdr()
            #print(tlv_hdr)
            #for c in tlv_hdr:
                #print("ASCII is ",ord(c)," chr is ",c)

            return tlv_hdr
           
        elif byteCount == self._eeprom_content_len():
            '''
            Get tlv eeprom content.
            '''
            crc_chr = self._calculate_crc32_checksum()
            #print(type(crc_chr))
            eeprom_content = self._get_eeprom_content()+crc_chr[0]+crc_chr[1]+crc_chr[2]+crc_chr[3]
            
            return eeprom_content

        else:
           raise 'This is temporarily unavailable.'
           