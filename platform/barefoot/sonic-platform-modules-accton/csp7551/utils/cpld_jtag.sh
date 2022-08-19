#!/bin/bash

usage() {
    echo "Usage: $prog <device> <file>"
    echo
    echo "device:"
    echo "       control: CTRL CPLD + FAN CPLD"
    echo "       port: PORT1 CPLD + PORT2 CPLD"
    echo
}
if [ $# -lt 2 ]||[ $# -ge 3 ]; then
    usage
    exit -1
fi
device=$1
file=$2
cmd="cpldupd -u CSP7551-PCH ${file} -c DO_REAL_TIME_ISP 1"
case "$device" in
    control)
        busybox devmem 0xfdaf05a8 8 0x01
        ;;
    port)
        busybox devmem 0xfdaf05a8 8 0x00
        ;;
    *)
        usage
        exit -1
        ;;
esac
$cmd
