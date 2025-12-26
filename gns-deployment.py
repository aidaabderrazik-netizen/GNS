import json
import os

OSPF_PID = 1
RIP_NAME = "RIP-ASX"

with open("routers.json") as f:
    routers = json.load(f)

for r in routers:
    gns_path = r["gns_path"]
    startup = os.path.join(gns_path, "i1_startup-config.cfg")

    if not os.path.isdir(gns_path):
        print(f"[ERROR] GNS path not found for {r['name']}")
        continue

    with open(startup, "w") as cfg:
        # -------------------------
        # Base
        # -------------------------
        cfg.write(f"hostname {r['name']}\n")
        cfg.write("ipv6 unicast-routing\n\n")

        # -------------------------
        # Loopback
        # -------------------------
        cfg.write("interface Loopback0\n")
        cfg.write(f" ipv6 address {r['loopback']}\n")

        if r["IGP"] == "OSPF":
            cfg.write(f" ipv6 ospf {OSPF_PID} area 0\n")
        else:
            cfg.write(f" ipv6 rip {RIP_NAME} enable\n")

        cfg.write("exit\n\n")

        # -------------------------
        # Interfaces
        # -------------------------
        for idx, iface in enumerate(r["interfaces"]):
            ifname = f"GigabitEthernet0/{idx}"

            cfg.write(f"interface {ifname}\n")
            cfg.write(f" ipv6 address {iface['local_ip']}\n")
            cfg.write(" no shutdown\n")

            if r["IGP"] == "OSPF":
                cfg.write(f" ipv6 ospf {OSPF_PID} area 0\n")
            else:
                cfg.write(f" ipv6 rip {RIP_NAME} enable\n")

            cfg.write("exit\n\n")

        # -------------------------
        # OSPF process (AS Y)
        # -------------------------
        if r["IGP"] == "OSPF":
            cfg.write(f"ipv6 router ospf {OSPF_PID}\n")
            cfg.write(f" router-id {r['router_id_bgp']}\n")
            cfg.write("exit\n\n")

        # -------------------------
        # RIP process (AS X)
        # -------------------------
        if r["IGP"] == "RIP":
            cfg.write(f"ipv6 router rip {RIP_NAME}\n")
            cfg.write("exit\n\n")

        # -------------------------
        # BGP
        # -------------------------
        cfg.write(f"router bgp {r['as_number']}\n")
        cfg.write(f" bgp router-id {r['router_id_bgp']}\n")
        cfg.write(" no bgp default ipv4-unicast\n")

        # iBGP
        for peer in r["iBGP_peers"]:
            peer_id = next(x["loopback"] for x in routers if x["name"] == peer)
            cfg.write(f" neighbor {peer_id.split('/')[0]} remote-as {r['as_number']}\n")
            cfg.write(" address-family ipv6\n")
            cfg.write(f"  neighbor {peer_id.split('/')[0]} activate\n")
            cfg.write(" exit-address-family\n")

        # eBGP
        for peer in r["eBGP_peers"]:
            peer_router = next(x for x in routers if x["name"] == peer["peer"])
            peer_ip = peer_router["interfaces"][0]["local_ip"].split("/")[0]

            cfg.write(f" neighbor {peer_ip} remote-as {peer['peer_as']}\n")
            cfg.write(" address-family ipv6\n")
            cfg.write(f"  neighbor {peer_ip} activate\n")
            cfg.write(" exit-address-family\n")

        cfg.write("exit\n")

    print(f"[OK] Deployed config for {r['name']}")
