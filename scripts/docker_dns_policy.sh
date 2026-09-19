#!/bin/sh
# Preserve Harbor's dynamic policies; exceptions exist only in allowlist mode.
set -eu
/bin/sh /opt/searchswe/network-policy-original "$@"
if [ "${1:-}" = allow ] && [ "$#" -gt 1 ]; then
    for server in ${SEARCH_SWE_DNS_SERVERS:?}; do
        # Server values are IPv4-validated by the trusted host launcher.
        nft insert rule inet gost_egress output ip daddr "$server" tcp dport 53 return
        nft insert rule inet gost_egress egress ip daddr "$server" udp dport 53 accept
    done
fi
