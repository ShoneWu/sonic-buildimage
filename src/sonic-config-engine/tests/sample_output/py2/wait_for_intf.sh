#!/usr/bin/env bash

function wait_until_iface_ready
{
    IFACE_NAME=$1
    IFACE_CIDR=$2

    echo "Waiting until interface ${IFACE_NAME} is ready..."

    # Wait for the interface to come up
    # (i.e., interface is present in STATE_DB and state is "ok")
    while true; do
        RESULT=$(sonic-db-cli STATE_DB HGET "INTERFACE_TABLE|${IFACE_NAME}|${IFACE_CIDR}" "state" 2> /dev/null)
        if [ x"$RESULT" == x"ok" ]; then
            break
        fi

        sleep 1
    done

    echo "Interface ${IFACE_NAME} is ready!"
}

function check_for_ipv6_link_local
{
    IFACE_NAME=$1
    echo "Waiting until interface ${IFACE_NAME} has a link-local ipv6 address configured...."

    # Status of link local address is not populated in STATE_DB
    while true; do
        HAS_LL=$(ip -6 addr show ${IFACE_NAME} scope link 2> /dev/null)
        RC=$?
        if [[ ${RC} == "0" ]] && [[ ! -z ${HAS_LL} ]]; then
            break
        fi

        sleep 1
    done

    echo "Link-Local address is configured on ${IFACE_NAME}"
}

# Wait for all interfaces with IPv4 addresses to be up and ready
# dhcp6relay binds to ipv6 addresses configured on these vlan ifaces
# Thus check if they are ready before launching dhcp6relay
wait_until_iface_ready Vlan2000 192.168.200.1/27
wait_until_iface_ready Vlan1000 192.168.0.1/27
wait_until_iface_ready Vlan1000 fc02:2000::2/24
check_for_ipv6_link_local Vlan1000
wait_until_iface_ready PortChannel02 10.0.0.58/31
wait_until_iface_ready PortChannel03 10.0.0.60/31
wait_until_iface_ready PortChannel04 10.0.0.62/31
wait_until_iface_ready PortChannel01 10.0.0.56/31

# Wait 10 seconds for the rest of interfaces to get added/populated.
# dhcrelay listens on each of the interfaces (in addition to the port
# channels and vlan interfaces)
sleep 10
