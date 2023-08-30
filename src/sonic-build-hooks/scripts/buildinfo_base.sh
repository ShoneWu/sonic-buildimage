#!/bin/bash

BUILDINFO_PATH=/usr/local/share/buildinfo

LOG_PATH=$BUILDINFO_PATH/log
VERSION_PATH=$BUILDINFO_PATH/versions
PRE_VERSION_PATH=$BUILDINFO_PATH/pre-versions
DIFF_VERSION_PATH=$BUILDINFO_PATH/diff-versions
BUILD_VERSION_PATH=$BUILDINFO_PATH/build-versions
POST_VERSION_PATH=$BUILDINFO_PATH/post-versions
VERSION_DEB_PREFERENCE=$BUILDINFO_PATH/versions/01-versions-deb
WEB_VERSION_FILE=$VERSION_PATH/versions-web
BUILD_WEB_VERSION_FILE=$BUILD_VERSION_PATH/versions-web
REPR_MIRROR_URL_PATTERN='http:\/\/packages.trafficmanager.net\/'
DPKG_INSTALLTION_LOCK_FILE=/tmp/.dpkg_installation.lock

. $BUILDINFO_PATH/config/buildinfo.config

URL_PREFIX=$(echo "${PACKAGE_URL_PREFIX}" | sed -E "s#(//[^/]*/).*#\1#")

if [ "$(whoami)" != "root" ] && [ -n "$(which sudo)" ];then
    SUDO=sudo
else
    SUDO=''
fi

log_err()
{
    echo "$1" >> $LOG_PATH/error.log
    echo "$1" 1>&2
}

# Get the real command not hooked by sonic-build-hook package
get_command()
{
    # Change the PATH env to get the real command by excluding the command in the hooked folders
    local path=$(echo $PATH | sed 's#[^:]*buildinfo/scripts:##' | sed "s#/usr/local/sbin:##")
    local command=$(PATH=$path which $1)
    echo $command
}

check_version_control()
{
    # The env variable SONIC_VERSION_CONTROL_COMPONENTS examples:
    # all            -- match all components
    # py2,py3,deb    -- match py2, py3 and deb only
    if [[ ",$SONIC_VERSION_CONTROL_COMPONENTS," == *,all,* ]] || [[ ",$SONIC_VERSION_CONTROL_COMPONENTS," == *,$1,* ]]; then
        echo "y"
    else
        echo "n"
    fi
}

get_url_version()
{
    local package_url=$1
    /usr/bin/curl -Lks $package_url | md5sum | cut -d' ' -f1
}

check_if_url_exist()
{
    local url=$1
    if /usr/bin/curl --output /dev/null --silent --head --fail "$1" > /dev/null 2>&1; then
        echo y
    else
        echo n
    fi
}

# Enable or disable the reproducible mirrors
set_reproducible_mirrors()
{
    # Remove the charater # in front of the line if matched
    local expression="s/^#\s*\(.*$REPR_MIRROR_URL_PATTERN\)/\1/"
    # Add the character # in front of the line, if not match the URL pattern condition
    local expression2="/^#*deb.*$REPR_MIRROR_URL_PATTERN/! s/^#*deb/#&/"
    local expression3="\$a#SET_REPR_MIRRORS"
    if [ "$1" = "-d" ]; then
        # Add the charater # in front of the line if match
        expression="s/^deb.*$REPR_MIRROR_URL_PATTERN/#\0/"
        # Remove the character # in front of the line, if not match the URL pattern condition
        expression2="/^#*deb.*$REPR_MIRROR_URL_PATTERN/! s/^#\s*(#*deb)/\1/"
        expression3="/#SET_REPR_MIRRORS/d"
    fi

    local mirrors="/etc/apt/sources.list $(find /etc/apt/sources.list.d/ -type f)"
    for mirror in $mirrors; do
        if ! grep -iq "$REPR_MIRROR_URL_PATTERN" "$mirror"; then
            continue
        fi

        # Make sure no duplicate operations on the mirror config file
        if ([ "$1" == "-d" ] && ! grep -iq "#SET_REPR_MIRRORS" "$mirror") ||
           ([ "$1" != "-d" ] && grep -iq "#SET_REPR_MIRRORS" "$mirror"); then
            continue
        fi

        # Enable or disable the reproducible mirrors
        $SUDO sed -i "$expression" "$mirror"

        # Enable or disable the none reproducible mirrors
        if [ "$MIRROR_SNAPSHOT" == y ]; then
            $SUDO sed -ri "$expression2" "$mirror"
        fi

        # Add or remove the SET_REPR_MIRRORS flag
        $SUDO sed -i "$expression3" "$mirror"
    done
}

download_packages()
{
    local parameters=("$@")
    declare -A filenames
    for (( i=0; i<${#parameters[@]}; i++ ))
    do
        local para=${parameters[$i]}
        local nexti=$((i+1))
        if [[ "$para" == *://* ]]; then
            local url=$para
            local real_version=

            # Skip to use the proxy, if the url has already used the proxy server
            if [[ $url == ${URL_PREFIX}* ]]; then
                continue
            fi

            if [ "$ENABLE_VERSION_CONTROL_WEB" == y ]; then
                local version=
                local filename=$(echo $url | awk -F"/" '{print $NF}' | cut -d? -f1 | cut -d# -f1)
                [ -f $WEB_VERSION_FILE ] && version=$(grep "^${url}=" $WEB_VERSION_FILE | awk -F"==" '{print $NF}')
                if [ -z "$version" ]; then
                    log_err "Warning: Failed to verify the package: $url, the version is not specified"
                    continue
                fi

                local version_filename="${filename}-${version}"
                local proxy_url="${PACKAGE_URL_PREFIX}/${version_filename}"
                local url_exist=$(check_if_url_exist $proxy_url)
                if [ "$url_exist" == y ]; then
                    parameters[$i]=$proxy_url
                    filenames[$version_filename]=$filename
                    real_version=$version
                else
                    real_version=$(get_url_version $url)
                    if [ "$real_version" != "$version" ]; then
                       log_err "Warning: Failed to verify url: $url, real hash value: $real_version, expected value: $version_filename"
                       continue
                    fi
                fi
            else
                real_version=$(get_url_version $url)
            fi
            # ignore md5sum for string ""
            # echo -n "" | md5sum    ==   d41d8cd98f00b204e9800998ecf8427e
            [[ $real_version == "d41d8cd98f00b204e9800998ecf8427e" ]] || echo "$url==$real_version" >> ${BUILD_WEB_VERSION_FILE}
        fi
    done

    $REAL_COMMAND "${parameters[@]}"
    local result=$?

    for filename in "${!filenames[@]}"
    do
        [ -f "$filename" ] && mv "$filename" "${filenames[$filename]}"
    done

    return $result
}

run_pip_command()
{
    parameters=("$@")

    if [ ! -x "$REAL_COMMAND" ] && [ " $1" == "freeze" ]; then
        return 1
    fi

    if [ "$ENABLE_VERSION_CONTROL_PY" != "y" ]; then
        $REAL_COMMAND "$@"
        return $?
    fi

    local found=n
    local install=n
    local pip_version_file=$PIP_VERSION_FILE
    local tmp_version_file=$(mktemp)
    [ -f "$pip_version_file" ] && cp -f $pip_version_file $tmp_version_file
    for para in "${parameters[@]}"
    do
        ([ "$para" == "-c" ] || [ "$para" == "--constraint" ]) && found=y
        if [ "$para" == "install" ]; then
            install=y
        elif [[ "$para" == *.whl ]]; then
            package_name=$(echo $para | cut -d- -f1 | tr _ .)
            $SUDO sed "/^${package_name}==/d" -i $tmp_version_file
        elif [[ "$para" == *==* ]]; then
            # fix pip package constraint conflict issue
            package_name=$(echo $para | cut -d= -f1)
            $SUDO sed "/^${package_name}==/d" -i $tmp_version_file
        fi
    done

    if [ "$found" == "n" ] && [ "$install" == "y" ]; then
        parameters+=("-c")
        parameters+=("${tmp_version_file}")
    fi

    $REAL_COMMAND "${parameters[@]}"
    local result=$?
    if [ "$result" != 0 ]; then
        echo "Failed to run the command with constraint, try to install with the original command" 1>&2
        $REAL_COMMAND "$@"
        result=$?
    fi
    rm $tmp_version_file
    return $result
}

# Check if the command is to install the debian packages
# The apt/apt-get command format: apt/apt-get [options] {update|install}
check_apt_install()
{
    for para in "$@"
    do
        if [[ "$para" == -* ]]; then
            continue
        fi

        if [[ "$para" == "install"  ]]; then
            echo y
        fi

        break
    done
}

# Print warning message if a debian package version not specified when debian version control enabled.
check_apt_version()
{
    VERSION_FILE="/usr/local/share/buildinfo/versions/versions-deb"
    local install=$(check_apt_install "$@")
    if [ "$ENABLE_VERSION_CONTROL_DEB" == "y" ] && [ "$install" == "y" ]; then
        for para in "$@"
        do
            if [[ "$para" == -* ]]; then
                continue
            fi

            if [ "$para" == "install" ]; then
                continue
            fi

            if [[ "$para" == *=* ]]; then
                continue
            else
                package=$para
                if ! grep -q "^${package}=" $VERSION_FILE; then
                    echo "Warning: the version of the package ${package} is not specified." 1>&2
                fi
            fi
        done
    fi
}

acquire_apt_installation_lock()
{
    local result=n
    local wait_in_second=10
    local count=60
    local info="$1"
    for ((i=1; i<=$count; i++)); do
        if [ -f $DPKG_INSTALLTION_LOCK_FILE ]; then
            local lock_info=$(cat $DPKG_INSTALLTION_LOCK_FILE || true)
            echo "Waiting dpkg lock for $wait_in_second, $i/$count, info: $lock_info" 1>&2
            sleep $wait_in_second
        else
            # Create file in an atomic operation
            if (set -o noclobber; echo "$info">$DPKG_INSTALLTION_LOCK_FILE) &>/dev/null; then
                result=y
                break
            else
                echo "Failed to creat lock, Waiting dpkg lock for $wait_in_second, $i/$count, info: $lock_info" 1>&2
                sleep $wait_in_second
            fi
        fi
    done

    echo $result
}

release_apt_installation_lock()
{
    rm -f $DPKG_INSTALLTION_LOCK_FILE
}

update_preference_deb()
{
    local version_file="$VERSION_PATH/versions-deb"
    if [ -f "$version_file" ]; then
        rm -f $VERSION_DEB_PREFERENCE
        for pacakge_version in $(cat "$version_file"); do
            package=$(echo $pacakge_version | awk -F"==" '{print $1}')
            version=$(echo $pacakge_version | awk -F"==" '{print $2}')
            echo -e "Package: $package\nPin: version $version\nPin-Priority: 999\n\n" >> $VERSION_DEB_PREFERENCE
        done
    fi
}

update_version_file()
{
    local version_name=$1
    local pre_version_file="$(ls $PRE_VERSION_PATH/${version_name}-* 2>/dev/null | head -n 1)"
    local version_file="$VERSION_PATH/$1"
    if [ ! -f "$pre_version_file" ]; then
        return 0
    fi
    local pacakge_versions="$(cat $pre_version_file)"
    [ -f "$version_file" ] && pacakge_versions="$pacakge_versions $(cat $version_file)"
    declare -A versions
    for pacakge_version in $pacakge_versions; do
        package=$(echo $pacakge_version | awk -F"==" '{print $1}')
        version=$(echo $pacakge_version | awk -F"==" '{print $2}')
        if [ -z "$package" ] || [ -z "$version" ]; then
            continue
        fi
        versions[$package]=$version
    done

    tmp_file=$(mktemp)
    for package in "${!versions[@]}"; do
        echo "$package==${versions[$package]}" >> $tmp_file
    done
    sort -u $tmp_file > $version_file
    rm -f $tmp_file
    
    if [[ "${version_name}" == *-deb ]]; then
        update_preference_deb
    fi
}

update_version_files()
{
    local version_names="versions-deb versions-py2 versions-py3"
    if [ "$MIRROR_SNAPSHOT" == y ]; then
        version_names="versions-py2 versions-py3"
    fi
    for version_name in $version_names; do
        update_version_file $version_name
    done
}

ENABLE_VERSION_CONTROL_DEB=$(check_version_control "deb")
ENABLE_VERSION_CONTROL_PY2=$(check_version_control "py2")
ENABLE_VERSION_CONTROL_PY3=$(check_version_control "py3")
ENABLE_VERSION_CONTROL_WEB=$(check_version_control "web")
ENABLE_VERSION_CONTROL_GIT=$(check_version_control "git")
ENABLE_VERSION_CONTROL_DOCKER=$(check_version_control "docker")
