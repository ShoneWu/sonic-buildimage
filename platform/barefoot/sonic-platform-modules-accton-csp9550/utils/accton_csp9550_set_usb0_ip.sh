#!/bin/sh


ifconfig -a | grep usb0 > /dev/null
ret=$?
if [ $ret -eq 0 ]; then
	ip addr add 240.1.1.2/30 dev usb0
	ifconfig usb0 up
fi
