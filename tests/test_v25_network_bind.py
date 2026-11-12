"""Garde-fous de liaison réseau : loopback par défaut, IPv4 privée sur opt-in explicite."""
import importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('maclasse_server_network',ROOT/'server.py')
server=importlib.util.module_from_spec(spec)
spec.loader.exec_module(server)

for host in ('127.0.0.1','localhost','::1'):
    assert server._assert_server_host(host) is True
for host in ('192.168.1.20','10.0.0.12','172.20.0.4'):
    try:
        server._assert_server_host(host)
    except ValueError:
        pass
    else:
        raise AssertionError('Une adresse LAN ne doit jamais être activée par défaut.')
    assert server._assert_server_host(host,allow_lan=True) is True
for host in ('8.8.8.8','0.0.0.0','fe80::1','not-an-ip'):
    try:
        server._assert_server_host(host,allow_lan=True)
    except ValueError:
        continue
    raise AssertionError(f'Adresse réseau non sûre acceptée : {host}')
print('OK — loopback par défaut ; mode LAN limité à une IPv4 privée précise et explicitement activée.')
