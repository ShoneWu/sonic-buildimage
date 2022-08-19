obj-m += x86-64-accton-csp7551-sfp.o accton_i2c_cpld.o fpga_driver.o 
$(info $$KVERSION is [${KVERSION}])
ifeq ($(KVERSION), 4.19.0-12-2-amd64)
    obj-m += at24_csp7551.o
else
endif