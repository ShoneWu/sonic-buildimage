# docker image for innovium syncd with rpc

DOCKER_SYNCD_INVM_RPC = docker-syncd-invm-rpc.gz
$(DOCKER_SYNCD_INVM_RPC)_PATH = $(PLATFORM_PATH)/docker-syncd-invm-rpc
$(DOCKER_SYNCD_INVM_RPC)_DEPENDS += $(SYNCD_RPC) $(LIBTHRIFT) $(INVM_LIBSAI) $(PTF)
$(DOCKER_SYNCD_INVM_RPC)_LOAD_DOCKERS += $(DOCKER_SYNCD_BASE)
SONIC_DOCKER_IMAGES += $(DOCKER_SYNCD_INVM_RPC)
ifeq ($(ENABLE_SYNCD_RPC),y)
SONIC_INSTALL_DOCKER_IMAGES += $(DOCKER_SYNCD_INVM_RPC)
endif

$(DOCKER_SYNCD_INVM_RPC)_CONTAINER_NAME = syncd
$(DOCKER_SYNCD_INVM_RPC)_VERSION = 1.0.0-rpc
$(DOCKER_SYNCD_INVM_RPC)_PACKAGE_NAME = syncd
$(DOCKER_SYNCD_INVM_RPC)_RUN_OPT += --privileged -t
$(DOCKER_SYNCD_INVM_RPC)_RUN_OPT += -v /host/machine.conf:/etc/machine.conf
$(DOCKER_SYNCD_INVM_RPC)_RUN_OPT += -v /var/run/docker-syncd:/var/run/sswsyncd
$(DOCKER_SYNCD_INVM_RPC)_RUN_OPT += -v /etc/sonic:/etc/sonic:ro
$(DOCKER_SYNCD_INVM_RPC)_RUN_OPT += -v /host/warmboot:/var/warmboot
