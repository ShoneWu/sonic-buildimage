# openssh package

OPENSSH_VERSION = 8.4p1-5+deb11u1

export OPENSSH_VERSION

OPENSSH_SERVER = openssh-server_$(OPENSSH_VERSION)_$(CONFIGURED_ARCH).deb
$(OPENSSH_SERVER)_SRC_PATH = $(SRC_PATH)/openssh
$(OPENSSH_SERVER)_DEPENDS +=  $(LIBNL3_DEV) $(LIBNL_ROUTE3_DEV)
SONIC_MAKE_DEBS += $(OPENSSH_SERVER)

# The .c, .cpp, .h & .hpp files under src/{$DBG_SRC_ARCHIVE list}
# are archived into debug one image to facilitate debugging.
#
DBG_SRC_ARCHIVE += openssh
