BFN_PLATFORM = bfnplatform_1.0.0_amd64.deb

#BFN_PLATFORM = bfnplatform_20191115_deb9.deb
#$(BFN_PLATFORM)_URL = "https://github.com/barefootnetworks/sonic-release-pkgs/raw/dev/bfnplatform_20191115_deb9.deb"

#SONIC_ONLINE_DEBS += $(BFN_PLATFORM)

$(BFN_PLATFORM)_PATH = files/pre_build_deb
SONIC_COPY_DEBS += $(BFN_PLATFORM)
$(BFN_SAI_DEV)_DEPENDS += $(BFN_PLATFORM)
