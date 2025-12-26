import json
import os

JSON_FILE = "routers.json"
DEFAULT_GNS_PATH = "/home/user/gns3/project/GNS"

# Load existing data or create a dictionary if the file doesn't exist
if os.path.exists(JSON_FILE):
    with open(JSON_FILE, "r") as f:
        data_list = json.load(f)
        data = {r["name"]: r for r in data_list}
else:
    data = {}

AS_X = 10
AS_Y = 20


# IGP mapping
AS_IGP = {
    AS_X: "RIP",
    AS_Y: "OSPF"
}

link_counter = {AS_X: 1, AS_Y: 1, "EBGP": 1}  # track link IDs per AS/internal/ebgp

def generate_router(router_num, as_number,
                    peer_links=None,
                    ibgp_peers=None,
                    ebgp_peers=None):
    global link_counter

    if peer_links is None: peer_links = []
    if ibgp_peers is None: ibgp_peers = []
    if ebgp_peers is None: ebgp_peers = []

    name = f"R{router_num}"
    igp = AS_IGP.get(as_number, "RIP")
    router_id_bgp = f"{1 if as_number == AS_X else 2}.1.1.{router_num}"
    loopback = f"2001:192:100:255::{router_num}/128"

    if name not in data:
        router = {
            "name": name,
            "as_number": as_number,
            "router_id_bgp": router_id_bgp,
            "loopback": loopback,
            "interfaces": [],
            "routing": {
                "igp": igp,
                "ibgp_peers": [],
                "ebgp_peers": []
            }
        }
    else:
        router = data[name]
        router["routing"]["igp"] = igp

    # -------------------------
    # Internal interfaces (iBGP / IGP)
    # -------------------------
    for peer_num, _ in peer_links:
        peer_name = f"R{peer_num}"
        subnet_id = link_counter[as_number]
        link_counter[as_number] += 1

        if as_number == AS_X:
            subnet = f"2001:192:168:{subnet_id}::"
        else:  # AS_Y
            subnet = f"2001:192:169:{subnet_id}::"

        if any(i["peer"] == peer_name for i in router["interfaces"]):
            continue

        router["interfaces"].append({
            "peer": peer_name,
            "local_ip": f"{subnet}1/64",
            "peer_ip": f"{subnet}2/64",
            "type": "internal"
        })

    # -------------------------
    # iBGP
    # -------------------------
    for peer in ibgp_peers:
        peer_name = f"R{peer}"
        if peer_name not in router["routing"]["ibgp_peers"]:
            router["routing"]["ibgp_peers"].append(peer_name)

    # -------------------------
    # eBGP
    # -------------------------
    for peer in ebgp_peers:
        peer_name = f"R{peer['peer']}"
        peer_as = peer['peer_as']

        # Assign a unique eBGP subnet per link
        subnet_id = link_counter["EBGP"]
        link_counter["EBGP"] += 1
        subnet = f"2001:192:170:{subnet_id}::"

        if all(i.get("peer") != peer_name or i.get("type") != "ebgp" for i in router["interfaces"]):
            router["interfaces"].append({
                "peer": peer_name,
                "local_ip": f"{subnet}1/64",
                "peer_ip": f"{subnet}2/64",
                "type": "ebgp"
            })

        if all(p["peer"] != peer_name for p in router["routing"]["ebgp_peers"]):
            router["routing"]["ebgp_peers"].append({"peer": peer_name, "peer_as": peer_as, "protocol": "BGP"})

    # -------------------------
    # Save router
    # -------------------------
    data[name] = router
    with open(JSON_FILE, "w") as f:
        json.dump(list(data.values()), f, indent=4)

# ---------------------------
# AS X
# ---------------------------
generate_router(1, AS_X, peer_links=[(2,1),(3,2)], ibgp_peers=[2,3])
generate_router(2, AS_X, peer_links=[(1,1),(3,3),(4,4)], ibgp_peers=[1,3,4])
generate_router(3, AS_X, peer_links=[(1,2),(2,3),(5,5)], ibgp_peers=[1,2,5])
generate_router(4, AS_X, peer_links=[(2,4),(5,6),(7,7)], ibgp_peers=[2,5,7])
generate_router(5, AS_X, peer_links=[(3,5),(4,6),(6,8),(7,10)], ibgp_peers=[3,4,6,7])
generate_router(6, AS_X, peer_links=[(4,9),(5,8)], ibgp_peers=[4,5], ebgp_peers=[{"peer": 9, "peer_as": AS_Y}])
generate_router(7, AS_X, peer_links=[(4,7),(5,10)], ibgp_peers=[4,5], ebgp_peers=[{"peer": 8, "peer_as": AS_Y}])

# ---------------------------
# AS Y
# ---------------------------
generate_router(8, AS_Y, peer_links=[(10,1),(13,2)], ibgp_peers=[10,13], ebgp_peers=[{"peer": 7, "peer_as": AS_X}])
generate_router(9, AS_Y, peer_links=[(10,3),(13,4)], ibgp_peers=[10,13], ebgp_peers=[{"peer": 6, "peer_as": AS_X}])
generate_router(10, AS_Y, peer_links=[(8,1),(9,3),(11,5),(12,6)], ibgp_peers=[8,9,11,12])
generate_router(11, AS_Y, peer_links=[(10,5),(13,7)], ibgp_peers=[8,9,10,13])
generate_router(12, AS_Y, peer_links=[(10,6),(13,8),(14,9)], ibgp_peers=[10,13,14])
generate_router(13, AS_Y, peer_links=[(11,7),(12,8),(14,10)], ibgp_peers=[11,12,14])
generate_router(14, AS_Y, peer_links=[(12,9),(13,10)], ibgp_peers=[12,13])
