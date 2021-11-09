#!/bin/bash
read=`busybox devmem 0xfc80002d 8`
write=$((($read | 0x08)&~0x04))
busybox devmem 0xfc80002d 8 $write
sleep 1 
busybox devmem 0xfc80002d 8 $write
sleep 1 
busybox devmem 0xfc80002d 8 $write

