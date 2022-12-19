#!/bin/bash
#

PATH=/sbin:/bin:/usr/sbin:/usr/bin:/usr/local/bin

prog="$0"
BUS_ID=35
CHIP_ADDR="0x6f"

DEBUGING=0

usage() {
    echo "Usage: "
    echo "$prog read <addr> <length>"
    echo "$prog write <addr> <length> <data1> <data2> <data3> <data4> <data5> <data6> <data7> <data8>"
    echo "$prog img_upd <file_name>"
    echo "$prog cfg_upd <file_name>"    
    echo "$prog inc_freq <int>"
    echo "$prog sub_freq <int>"
    echo
    echo "Commands:"
    echo "  read: Read Si5383 register."
    echo "  write: Write Si5383 register."
    echo "  img_upd: Upgrade Si5383 image."
    echo "  cfg_upd: Upgrade Si5383 configuration."    
    echo "  inc_freq: Increase Si5383 frequency PPM."
    echo "  sub_freq: Substract Si5383 frequency PPM."
    echo
    echo "Input Format: "    
    echo "  <addr>   : 4-byte hex. ex. \"0x1234\""
    echo "  <length> : int 1-8. ex. \"3\" "
    echo "  <data>   : 2-byte hex. ex. 0x12"
}

do_read(){
    address=$1
    length=$2

    # write MSB & LSB into RD_ADDR
    MSB=${address:2:2}
    LSB=${address:4:2}    
    i2cset -y -f $BUS_ID $CHIP_ADDR 0x30 0x$MSB
    i2cset -y -f $BUS_ID $CHIP_ADDR 0x31 0x$LSB
     
    # write RD_LENGTH and RD_CMD(0x32) reg to trigger read target register
    i2cset -y -f $BUS_ID $CHIP_ADDR 0x32 0x$(($length-1))1
    RD_STATUS=$(i2cget -y -f $BUS_ID $CHIP_ADDR 0x32)

    if [ ${RD_STATUS:3:1} -ne 0 ]; then
        echo "Read status is incorrect, please try again!"
        exit -1
    fi

    # check the read result with below reg
    data0=$(i2cget -y -f $BUS_ID $CHIP_ADDR 0x33)
    data1=$(i2cget -y -f $BUS_ID $CHIP_ADDR 0x34)
    data2=$(i2cget -y -f $BUS_ID $CHIP_ADDR 0x35)
    data3=$(i2cget -y -f $BUS_ID $CHIP_ADDR 0x36)
    data4=$(i2cget -y -f $BUS_ID $CHIP_ADDR 0x37)
    data5=$(i2cget -y -f $BUS_ID $CHIP_ADDR 0x38)
    data6=$(i2cget -y -f $BUS_ID $CHIP_ADDR 0x39)
    data7=$(i2cget -y -f $BUS_ID $CHIP_ADDR 0x3a)

    echo "Read register:$address"
    if [ $length -eq 1 ]; then   
        echo "Return Data: $data0"
    elif [ $length -eq 2 ]; then  
        echo "Return Data: $data0 $data1"
    elif [ $length -eq 3 ]; then  
        echo "Return Data: $data0 $data1 $data2"
    elif [ $length -eq 4 ]; then  
        echo "Return Data: $data0 $data1 $data2 $data3"
    elif [ $length -eq 5 ]; then  
        echo "Return Data: $data0 $data1 $data2 $data3 $data4"
    elif [ $length -eq 6 ]; then  
        echo "Return Data: $data0 $data1 $data2 $data3 $data4 $data5"
    elif [ $length -eq 7 ]; then  
        echo "Return Data: $data0 $data1 $data2 $data3 $data4 $data5 $data6"
    elif [ $length -eq 8 ]; then  
        echo "Return Data: $data0 $data1 $data2 $data3 $data4 $data5 $data6 $data7"
    else
        echo "Incorrect input length"
    fi
}

do_write(){
    address=$1
    length=$2
    
    # write MSB & LSB into WD_ADDR
    MSB=${address:2:2}
    LSB=${address:4:2}    
    i2cset -y -f $BUS_ID $CHIP_ADDR 0x20 0x$MSB
    i2cset -y -f $BUS_ID $CHIP_ADDR 0x21 0x$LSB
    
    # write WR_DATAX to store write data
    if [ $length -eq 1 ]; then
        data0=$3
        i2cset -y -f $BUS_ID $CHIP_ADDR 0x22 $data0
    elif [ $length -eq 2 ]; then
        data0=$3
        data1=$4
        i2cset -y -f $BUS_ID $CHIP_ADDR 0x22 $data0
        i2cset -y -f $BUS_ID $CHIP_ADDR 0x23 $data1
    elif [ $length -eq 3 ]; then
        data0=$3
        data1=$4
        data2=$5        
        i2cset -y -f $BUS_ID $CHIP_ADDR 0x22 $data0
        i2cset -y -f $BUS_ID $CHIP_ADDR 0x23 $data1
        i2cset -y -f $BUS_ID $CHIP_ADDR 0x24 $data2
    elif [ $length -eq 4 ]; then
        data0=$3
        data1=$4
        data2=$5
        data3=$6
        i2cset -y -f $BUS_ID $CHIP_ADDR 0x22 $data0
        i2cset -y -f $BUS_ID $CHIP_ADDR 0x23 $data1
        i2cset -y -f $BUS_ID $CHIP_ADDR 0x24 $data2
        i2cset -y -f $BUS_ID $CHIP_ADDR 0x25 $data3
    elif [ $length -eq 5 ]; then
        data0=$3
        data1=$4
        data2=$5
        data3=$6
        data4=$7
        i2cset -y -f $BUS_ID $CHIP_ADDR 0x22 $data0
        i2cset -y -f $BUS_ID $CHIP_ADDR 0x23 $data1
        i2cset -y -f $BUS_ID $CHIP_ADDR 0x24 $data2
        i2cset -y -f $BUS_ID $CHIP_ADDR 0x25 $data3
        i2cset -y -f $BUS_ID $CHIP_ADDR 0x26 $data4
    elif [ $length -eq 6 ]; then
        data0=$3
        data1=$4
        data2=$5
        data3=$6
        data4=$7
        data5=$8
        i2cset -y -f $BUS_ID $CHIP_ADDR 0x22 $data0
        i2cset -y -f $BUS_ID $CHIP_ADDR 0x23 $data1
        i2cset -y -f $BUS_ID $CHIP_ADDR 0x24 $data2
        i2cset -y -f $BUS_ID $CHIP_ADDR 0x25 $data3
        i2cset -y -f $BUS_ID $CHIP_ADDR 0x26 $data4
        i2cset -y -f $BUS_ID $CHIP_ADDR 0x27 $data5
    elif [ $length -eq 7 ]; then
        data0=$3
        data1=$4
        data2=$5
        data3=$6
        data4=$7
        data5=$8
        data6=$9
        i2cset -y -f $BUS_ID $CHIP_ADDR 0x22 $data0
        i2cset -y -f $BUS_ID $CHIP_ADDR 0x23 $data1
        i2cset -y -f $BUS_ID $CHIP_ADDR 0x24 $data2
        i2cset -y -f $BUS_ID $CHIP_ADDR 0x25 $data3
        i2cset -y -f $BUS_ID $CHIP_ADDR 0x26 $data4
        i2cset -y -f $BUS_ID $CHIP_ADDR 0x27 $data5
        i2cset -y -f $BUS_ID $CHIP_ADDR 0x28 $data6
    elif [ $length -eq 8 ]; then
        data0=$3
        data1=$4
        data2=$5
        data3=$6
        data4=$7
        data5=$8
        data6=$9
        data7=${10}
        i2cset -y -f $BUS_ID $CHIP_ADDR 0x22 $data0
        i2cset -y -f $BUS_ID $CHIP_ADDR 0x23 $data1
        i2cset -y -f $BUS_ID $CHIP_ADDR 0x24 $data2
        i2cset -y -f $BUS_ID $CHIP_ADDR 0x25 $data3
        i2cset -y -f $BUS_ID $CHIP_ADDR 0x26 $data4
        i2cset -y -f $BUS_ID $CHIP_ADDR 0x27 $data5
        i2cset -y -f $BUS_ID $CHIP_ADDR 0x28 $data6
        i2cset -y -f $BUS_ID $CHIP_ADDR 0x29 $data7
    else
        echo "Incorrect input length"
    fi
     
    # write WR_LENGTH and WR_CMD(0x2A) reg to trigger write target register
    i2cset -y -f $BUS_ID $CHIP_ADDR 0x2a 0x$(($length-1))1
    sleep 1
    WR_STATUS=$(i2cget -y -f $BUS_ID $CHIP_ADDR 0x2a)

    if [ $DEBUGING -eq 1 ]; then
        echo "i2cset -y -f $BUS_ID $CHIP_ADDR 0x2a 0x$(($length-1))1"
        echo "WR_STATUS:$WR_STATUS"
    fi

    if [ ${WR_STATUS:3:1} -ne 0 ]; then
        echo "Write status is incorrect, please try again!"
        exit -1
    fi

    echo "Write register success!"
}


do_config_upgrade(){
    filename=$1

    #open file and read line by line
    while IFS='' read -r line || [[ -n "$line" ]]; do
        if [[ $line == *"Delay 300 msec"* ]]; then
            echo "Sleep for device to complete any calibration!"
            sleep 1
        elif [[ $line == *"0x"* ]]; then
            # start to write registers into Si5383
            reg_addr=${line:0:6}
            reg_data=${line:7:4}
            
            do_write $reg_addr 1 $reg_data
        fi
    done < $filename

    echo "Upgrade Si5383 config finished!"

}

do_image_upgrade(){
    filename=$1

    echo "Start updating Si5383 img, take about 2 to 3 min..."

    echo "Put device in boot loader mode"
    #set device to bootloader mode
    do_write "0x5305" 1 "0x57"
    do_write "0x5305" 1 "0xba"
    
    #hex dump from bin file and store char by char into array format
    IMG_HEX=($(od -v -An -txC < $filename | awk '{ for (i = 1; i <= NF; ++i) print $i }'))

    I2CSET_CMD="fpga_i2c write $BUS_ID $CHIP_ADDR"
    boot_record=""
    data_length=0

    sub_num=1
    cmd_prefix_length=2
    first_bootcmd=0

    echo "Sending boot_record into device"
    
    for ((index=0 ; index < ${#IMG_HEX[@]} ; index++ ))
    do
        if [ ${IMG_HEX[$index]} = "24" ]; then
            # put start cmd in boot_record
            boot_record="0x${IMG_HEX[$index]}"
            index=$(( $index+1 ))

            # put data length in boot_record, need add 1 for leng byte
            data_length=$((16#$(expr ${IMG_HEX[$index]})))
            data_length=$(( $data_length + 1 ))
            boot_record="$boot_record $data_length"

            # put data in boot_record
            temp_string=("${IMG_HEX[@]:$index:$(expr $data_length)}")
            temp_string=$(printf ' 0x%s' "${temp_string[@]}")
            boot_record="$boot_record$temp_string"

            #move index to next boot_record
            index=$(expr $index + $data_length - $cmd_prefix_length)

            # Send boot_record to Si5383
            # cmd example: 
            #fpga_i2c write $BUS_ID $CHIP_ADDR 0x$CMD $LENGTH $DATA ....
            #fpga_i2c write 35 0x6f 0x24 5 0x04 0x31 0xa5 0xf1 0x00
            echo "$I2CSET_CMD $boot_record"
            $I2CSET_CMD $boot_record

            if [ $data_length -lt 30 ]; then
                # by si5383-84-rm 4.3.4 the last three boot_record need to wait 6 sec to complete.
                echo "Wait 6 sec to write boot_record"
                sleep 6
            fi

        fi  
    done

    echo "Upgrade Si5383 image finished!"
}


increase_frequency(){
    step=$(expr $1)

    reg_addr="0x001d"

    for i in $(seq 1 $step); do
        do_write $reg_addr 1 1
    done

    echo "Increase frequency step $step done."
}

substract_frequency(){
    step=$(expr $1)

    reg_addr="0x001d"

    for i in $(seq 1 $step); do
        do_write $reg_addr 1 2
    done

    echo "Substract frequency step $step done."
}

command="$1"
case "$command" in
    read)
        if [ $# -ne 3 ]; then
            usage
            exit -1
        fi
        shift
        do_read $@
        ;;
    write)
        if [ $# -gt 11 ]; then
            usage
            exit -1
        fi
        shift
        do_write $@
        ;;
    cfg_upd)
        if [ $# -ne 2 ]; then
            usage
            exit -1
        fi
        shift
        do_config_upgrade $@
        ;;
    img_upd)
        if [ $# -ne 2 ]; then
            usage
            exit -1
        fi
        shift
        do_image_upgrade $@
        ;;
    inc_freq)
        if [ $# -ne 2 ]; then
            usage
            exit -1
        fi
        shift
        increase_frequency $@
        ;;
    sub_freq)
        if [ $# -ne 2 ]; then
            usage
            exit -1
        fi
        shift
        substract_frequency $@
        ;;
    *)
        usage
        exit -1
        ;;
esac

exit $?


