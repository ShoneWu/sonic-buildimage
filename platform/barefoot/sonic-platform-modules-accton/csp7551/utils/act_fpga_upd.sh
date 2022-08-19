#!/bin/bash
setpci -d 1172:0001 0x04.B=0x7
REG_MEM=`lspci -d 1172:0001 -vv | grep "Region 0" | awk '{print $5}'`

RD=`busybox devmem $((16#$REG_MEM+0x3)) 8`
echo "Device ID = $RD"
RD=`busybox devmem $((16#$REG_MEM+0x2)) 8`
echo "Major Versino = $RD"
RD=`busybox devmem $((16#$REG_MEM+0x1)) 8`
echo "Minor Version = $RD"
RD=`busybox devmem $((16#$REG_MEM+0x0)) 8`
echo "Test Version = $RD"
RD=`busybox devmem $((16#$REG_MEM+0x100000)) 32`
echo "Build Version = $RD"

MB_MEM=`lspci -d 1172:0001 -vv | grep "Region 1" | awk '{print $5}'`
echo "Memory mapping at ${MB_MEM}"

/usr/local/bin/act_fpga_upd $@ $MB_MEM