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

sleep 1

data1=($(i2cget -y $i2c_bus $i2c_addr))
RV1=$?
if [ "$RV1" -ne "0" ]; then
    echo -e "\n tofino i2c get reg data1 fail!!!\n"
    exit 1
fi

data2=($(i2cget -y $i2c_bus $i2c_addr))
RV2=$?
if [ "$RV2" -ne "0" ]; then
    echo -e "\n tofino i2c get reg data2 fail!!!\n"
    exit 1
fi

data3=($(i2cget -y $i2c_bus $i2c_addr))
RV3=$?
if [ "$RV3" -ne "0" ]; then
    echo -e "\n tofino i2c get reg data3 fail!!!\n"
    exit 1
fi

data4=($(i2cget -y $i2c_bus $i2c_addr))
RV4=$?
if [ "$RV4" -ne "0" ]; then
    echo -e "\n tofino i2c get reg data4 fail!!!\n"
    exit 1
fi

echo -e "\n======================================================"
echo -e "\nData is:${data4} ${data3} ${data2} ${data1}\n"
echo -e "======================================================\n"
