import json
import os

OSPF_PID = 1
RIP_NAME = "RIP-ASX"

# Load routers JSON
with open("routers.json") as f:
    routers = json.load(f)

for r in routers:
    gns_path = r.get("gns_path", ".")  # fallback if not defined
    startup = os.path.join(gns_path, "i1_startup-config.cfg")

    if not os.path.isdir(gns_path):
        print(f"[ERROR] GNS path not found for {r['name']}")
        continue

    with open(startup, "w") as cfg:
        # -------------------------
        # Base config
        # -------------------------
        cfg.write(f"hostname {r['name']}\n")
        cfg.write("ipv6 unicast-routing\n\n")

        # -------------------------
        # Loopback interface
        # -------------------------
        cfg.write("interface Loopback0\n")
        cfg.write(f" ipv6 address {r['loopback']}\n")

        if r["routing"]["igp"] == "OSPF":
            cfg.write(f" ipv6 ospf {OSPF_PID} area 0\n")
        else:
            cfg.write(f" ipv6 rip {RIP_NAME} enable\n")

        cfg.write("exit\n\n")

        # -------------------------
        # Physical / internal / eBGP interfaces
        # -------------------------
        for idx, iface in enumerate(r["interfaces"]):
            ifname = f"GigabitEthernet0/{idx}"
            cfg.write(f"interface {ifname}\n")
            cfg.write(f" ipv6 address {iface['local_ip']}\n")
            cfg.write(" no shutdown\n")

            if r["routing"]["igp"] == "OSPF" and iface.get("type") != "ebgp":
                cfg.write(f" ipv6 ospf {OSPF_PID} area 0\n")
            elif r["routing"]["igp"] == "RIP" and iface.get("type") != "ebgp":
                cfg.write(f" ipv6 rip {RIP_NAME} enable\n")

            cfg.write("exit\n\n")

        # -------------------------
        # IGP process
        # -------------------------
        if r["routing"]["igp"] == "OSPF":
            cfg.write(f"ipv6 router ospf {OSPF_PID}\n")
            cfg.write(f" router-id {r['router_id_bgp']}\n")
            cfg.write("exit\n\n")
        elif r["routing"]["igp"] == "RIP":
            cfg.write(f"ipv6 router rip {RIP_NAME}\n")
            cfg.write("exit\n\n")

        # -------------------------
        # BGP process
        # -------------------------
        cfg.write(f"router bgp {r['as_number']}\n")
        cfg.write(f" bgp router-id {r['router_id_bgp']}\n")
        cfg.write(" no bgp default ipv4-unicast\n")

        # iBGP peers
        for peer in r["routing"]["ibgp_peers"]:
            peer_id = next(x["loopback"] for x in routers if x["name"] == peer)
            cfg.write(f" neighbor {peer_id.split('/')[0]} remote-as {r['as_number']}\n")
            cfg.write(" address-family ipv6\n")
            cfg.write(f"  neighbor {peer_id.split('/')[0]} activate\n")
            cfg.write(" exit-address-family\n")

        # eBGP peers
        for peer in r["routing"]["ebgp_peers"]:
            peer_router = next(x for x in routers if x["name"] == peer["peer"])
            # Find the interface connected to this eBGP peer
            iface = next(i for i in r["interfaces"] if i["peer"] == peer["peer"] and i.get("type") == "ebgp")
            peer_ip = iface["peer_ip"].split("/")[0]

            cfg.write(f" neighbor {peer_ip} remote-as {peer['peer_as']}\n")
            cfg.write(" address-family ipv6\n")
            cfg.write(f"  neighbor {peer_ip} activate\n")
            cfg.write(" exit-address-family\n")

        cfg.write("exit\n")

    print(f"[OK] Deployed config for {r['name']}")
