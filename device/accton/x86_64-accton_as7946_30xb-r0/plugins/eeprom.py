#!/usr/bin/env python

import os

try:
    from sonic_eeprom import eeprom_tlvinfo
except ImportError as e:
    raise ImportError(str(e) + "- required module not found")

class board(eeprom_tlvinfo.TlvInfoDecoder):
    _TLV_INFO_MAX_LEN = 256
    def __init__(self, name, path, cpld_root, ro):
        if not os.path.islink("/var/cache/sonic/decode-syseeprom"):
            os.system("mkdir -p /var/cache/sonic/decode-syseeprom/")
        os.system("sudo cp -f /sys/devices/platform/as7946_30xb_sys/eeprom /var/cache/sonic/decode-syseeprom/syseeprom_cache")
        self.eeprom_path = "/sys/devices/platform/as7946_30xb_sys/eeprom"
        super(board, self).__init__(self.eeprom_path, 0, '', True)
