ifneq ($(KERNELRELEASE),)
obj-m:= x86-64-accton-as7946-74xkb-cpld.o  x86-64-accton-as7946-74xkb-leds.o \
        x86-64-accton-as7946-74xkb-fan.o   x86-64-accton-as7946-74xkb-psu.o \
        x86-64-accton-as7946-74xkb-thermal.o  x86-64-accton-as7946-74xkb-sys.o \
        switch_optoe.o

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
