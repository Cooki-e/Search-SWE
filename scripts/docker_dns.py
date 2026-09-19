"""Opt-in upstream DNS for Harbor's isolated Docker network namespace.

Docker's embedded resolver otherwise forwards to the host's systemd-resolved
stub. Explicit upstreams execute in the container namespace, where Harbor's
UDP deny rule also blocks DNS. Exempt only those servers on DNS port 53.
"""

import ipaddress
import json
from pathlib import Path
import tempfile


def parse_servers(value):
    servers = []
    for item in value.split(','):
        address = ipaddress.IPv4Address(item.strip())
        if address.is_loopback or address.is_multicast or address.is_unspecified or address.is_link_local:
            raise ValueError('CONTAINER_DNS requires reachable unicast IPv4 addresses')
        if str(address) not in servers:
            servers.append(str(address))
    return servers


def create_overlay(servers):
    from harbor.environments.docker import docker

    original = Path(docker.__file__).parent / 'harbor-docker-egress-control-sidecar/bin/network-policy'
    if not original.is_file():
        raise RuntimeError('Installed Harbor does not provide the expected network-policy helper')
    wrapper = Path(__file__).with_name('docker_dns_policy.sh').resolve()
    directory = Path(tempfile.mkdtemp(prefix='searchswe-dns-'))
    # Keep the installed Harbor policy implementation; no duplicated firewall.
    snapshot = directory / 'network-policy-original'
    snapshot.write_bytes(original.read_bytes())
    overlay = {
        'services': {'harbor-docker-egress-control-sidecar': {
            'dns': servers,
            'environment': {'SEARCH_SWE_DNS_SERVERS': ' '.join(servers)},
            'volumes': [
                {'type': 'bind', 'source': str(snapshot),
                 'target': '/opt/searchswe/network-policy-original', 'read_only': True},
                {'type': 'bind', 'source': str(wrapper),
                 'target': '/usr/local/bin/network-policy', 'read_only': True},
            ],
        }},
    }
    path = directory / 'compose.json'
    path.write_text(json.dumps(overlay, indent=2) + '\n')
    return path
