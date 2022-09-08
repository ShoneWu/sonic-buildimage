ifneq ($(KERNELRELEASE),)
obj-m:= x86-64-accton-as9926-24d-cpld.o  x86-64-accton-as9926-24d-leds.o \
        x86-64-accton-as9926-24d-fan.o   x86-64-accton-as9926-24d-psu.o \
        x86-64-accton-as9926-24d-fpga.o  x86-64-accton-as9926-24d-sys.o \
        dps850.o switch_i2c-mux-pca954x.o switch_optoe.o

else
ifeq (,$(KERNEL_SRC))
$(error KERNEL_SRC is not defined)
else
KERNELDIR:=$(KERNEL_SRC)
endif
PWD:=$(shell pwd)
default:
	$(MAKE) -C $(KERNELDIR)  M=$(PWD) modules
clean:
	rm -rf *.o *.mod.o *.mod.o *.ko .*cmd .tmp_versions Module.markers Module.symvers modules.order
endif
