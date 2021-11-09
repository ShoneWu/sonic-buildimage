#!/bin/bash

usage() {
  echo "Usage: $0 <bits 31-24> <bits 23-16> <bits 15-8> <register offset bits7-0>" >&2
}

if [ "$#" -lt 4 ]; then
    usage
    exit 1
fi

i2c_bus=0
cmd=0xa0
i2c_addr=0x58


addr_1=$1
addr_2=$2
addr_3=$3
addr_4=$4

i2cset -y $i2c_bus $i2c_addr $cmd $addr_4 $addr_3 $addr_2 $addr_1 i
RV=$?
if [ "$RV" -ne "0" ]; then
    echo -e "\n tofino i2c write reg: ${addr_1} ${addr_2} ${addr_3} ${addr_4} fail!!!\n"
    exit 1
fi
