#!/usr/bin/python
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

import subprocess
import time

I210_DRIVER = "igb"
KR_DRIVER = "ice"
CX_DRIVER = "mlx5_core"


def exec_check_output_no_chk_retcode(cmd):
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    outs = p.communicate()
    return outs[0]+outs[1]


def eth_swap(eth_1, eth_2):
    print("SWAP %s with %s" % (eth_1, eth_2) )
    temp_eth = 'temp_eth'
    subprocess.call("ifconfig %s down" % eth_1, stderr=subprocess.STDOUT, shell=True)
    subprocess.call("ip link set %s name %s" % (eth_1, temp_eth), stderr=subprocess.STDOUT, shell=True)
    subprocess.call("ifconfig %s up" % temp_eth, stderr=subprocess.STDOUT, shell=True)

    subprocess.call("ifconfig %s down" % eth_2, stderr=subprocess.STDOUT, shell=True)
    subprocess.call("ip link set %s name %s" % (eth_2, eth_1), stderr=subprocess.STDOUT, shell=True)
    subprocess.call("ifconfig %s up" % eth_1, stderr=subprocess.STDOUT, shell=True)

    subprocess.call("ifconfig %s down" % temp_eth, stderr=subprocess.STDOUT, shell=True)
    subprocess.call("ip link set %s name %s" % (temp_eth, eth_2), stderr=subprocess.STDOUT, shell=True)
    subprocess.call("ifconfig %s up" % eth_2, stderr=subprocess.STDOUT, shell=True)
    return True


def print_eth_list():
    print("=======================================")
    eth_num = exec_check_output_no_chk_retcode("ip -o link show | grep \" eth\" | grep -v \".4088\" -c")
    eth_num = int(eth_num)
    for i in range(eth_num):
        cmd = "/usr/sbin/ethtool -i eth%s | grep \"driver\|bus-info\"" % i
        print(cmd)
        out_str = exec_check_output_no_chk_retcode(cmd)
        print(out_str)
    print("=======================================")
    return True


# Slot1 3b:00.0
# Slot2 5e:00.0  5e:00.1
# Slot3 af:00.0  af:00.1
# Slot4 d8:00.0
def diag_item_rename_eth():
    #print_eth_list()

    #sleep a while to make sure driver install is done
    time.sleep(2)
    eth_num = exec_check_output_no_chk_retcode("ip -o link show | grep \" eth\" | grep -v \".4088\" -c")
    eth_num = int(eth_num)
    expect_driver=[I210_DRIVER, KR_DRIVER, CX_DRIVER]
    slot_serial = ['3b', '5e', 'af', 'd8']
    target_driver_name = ''
    target_bus_major = ''
    target_bus_minor = ''
    compare_driver_name = ''
    #compare_bus_name = ''
    compare_bus_major = ''
    compare_bus_minor = ''
    for i in range(eth_num):
        for j in range(i, eth_num):
            if i == j:
                continue
            # get  eth target  one
            get_driver_cmd = "/usr/sbin/ethtool -i eth%s | grep driver" % i
            target_driver_name = exec_check_output_no_chk_retcode(get_driver_cmd).split(':')[1].strip()
            get_bus_cmd = "/usr/sbin/ethtool -i eth%s | grep bus-info" % i
            bus_str_split = exec_check_output_no_chk_retcode(get_bus_cmd).split(':')
            target_bus_major = bus_str_split[2].strip()
            target_bus_minor = float(bus_str_split[3].strip())
            # get  eth compare one
            get_driver_cmd = "/usr/sbin/ethtool -i eth%s | grep driver" % j
            compare_driver_name = exec_check_output_no_chk_retcode(get_driver_cmd).split(':')[1].strip()
            get_bus_cmd = "/usr/sbin/ethtool -i eth%s | grep bus-info" % j
            bus_str_split = exec_check_output_no_chk_retcode(get_bus_cmd).split(':')
            compare_bus_major = bus_str_split[2].strip()
            compare_bus_minor = float(bus_str_split[3].strip())

            # Sort driver name by index
            if target_driver_name in expect_driver and compare_driver_name in expect_driver:
                if expect_driver.index(target_driver_name) > expect_driver.index(compare_driver_name) :
                    eth_swap("eth%s"% i, "eth%s"% j)
                    continue
            # swap backward  if driver is unknow
            elif (target_driver_name not in expect_driver and compare_driver_name in expect_driver) or (target_driver_name in expect_driver and compare_driver_name not in expect_driver):
                eth_swap("eth%s"% i, "eth%s"% j)
                continue
            # if driver name eque, sort increasing
            if (compare_driver_name == target_driver_name):
                if target_driver_name == CX_DRIVER:
                    if (slot_serial.index(target_bus_major) > slot_serial.index(compare_bus_major)):
                        eth_swap("eth%s"% i, "eth%s"% j)
                        continue
                    elif (slot_serial.index(target_bus_major) == slot_serial.index(compare_bus_major) and target_bus_minor > compare_bus_minor):
                        eth_swap("eth%s"% i, "eth%s"% j)
                        continue
                else:
                    if (int(target_bus_major, 16) > int (compare_bus_major, 16)):
                        eth_swap("eth%s"% i, "eth%s"% j)
                        continue
                    elif (int(target_bus_major, 16) == int (compare_bus_major, 16) and target_bus_minor > compare_bus_minor):
                        eth_swap("eth%s"% i, "eth%s"% j)
                        continue

    #print("After sort eth:")
    #print_eth_list()
    return True
    
    
def __main__():
    ret = diag_item_rename_eth()
    return ret

__main__()
