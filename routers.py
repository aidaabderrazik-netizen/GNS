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

# AS numbers
AS_X = 10
AS_Y = 20

# Define IGP based on AS
AS_IGP = {
    AS_X: "RIP",
    AS_Y: "OSPF"
}

def generate_router(router_num, as_number, peer_links=None, gns_path=None, ibgp_peers=None, ebgp_peers=None):
    """
    Generate router details automatically based on router number.
    - router_num: integer, e.g., 4 for R4
    - as_number: AS number
    - peer_links: list of tuples (peer_num, link_num), e.g., [(5,6),(7,7)]
    - gns_path: path to the GNS3 project
    - ibgp_peers: list of router numbers for iBGP peers
    - ebgp_peers: list of dicts [{"peer": peer_router_num, "peer_as": AS}]
    """
    # These next lines are used because [] are mutable defaults, 
    # basically this leads to routers sharing the same list of 
    # interfaces of bgp peers.

    if peer_links is None:
        peer_links = []
    if gns_path is None:
        gns_path = DEFAULT_GNS_PATH
    if ibgp_peers is None:
        ibgp_peers = []
    if ebgp_peers is None:
        ebgp_peers = []

    name = f"R{router_num}"
    router_id_bgp = f"{1 if as_number == AS_X else 2}.{1}.{1}.{router_num}"
    loopback = f"2001:192:100:255::{router_num}/128"
    igp = AS_IGP.get(as_number, "RIP")  # Default to RIP if AS unknown

    # Check if router exists
    if name in data:
        router = data[name]
        print(f"Router {name} already exists. Updating IGP and gns_path if needed...")
        router["IGP"] = igp
        router["gns_path"] = gns_path
    else:
        router = {
            "name": name,
            "as_number": as_number,
            "router_id_bgp": router_id_bgp,
            "loopback": loopback,
            "IGP": igp,
            "ospf_area": 0,
            "gns_path": gns_path,
            "interfaces": [],
            "iBGP_peers": [],
            "eBGP_peers": []
        }

    # Add interfaces, avoiding duplicates
    for peer_num, link_num in peer_links:
        peer_name = f"R{peer_num}"
        local_ip = f"2001:192:168:{link_num}::1/64"
        peer_ip = f"2001:192:168:{link_num}::2/64"

        if any(iface["peer"] == peer_name for iface in router["interfaces"]):
            continue

        router["interfaces"].append({
            "peer": peer_name,
            "local_ip": local_ip,
            "peer_ip": peer_ip
        })

    # Add iBGP peers
    for peer_num in ibgp_peers:
        peer_name = f"R{peer_num}"
        if peer_name not in router["iBGP_peers"]:
            router["iBGP_peers"].append(peer_name)

    # Add eBGP peers
    for peer in ebgp_peers:
        peer_name = f"R{peer['peer']}"
        peer_as = peer['peer_as']
        if all(p["peer"] != peer_name for p in router["eBGP_peers"]):
            router["eBGP_peers"].append({"peer": peer_name, "peer_as": peer_as})

    # Save router back to dictionary
    data[name] = router

    # Save entire data to JSON
    with open(JSON_FILE, "w") as f:
        json.dump(list(data.values()), f, indent=4)
    print(f"Router {name} processed successfully!\n")


# ---------------------------
# Example usage: generate AS X routers
# ---------------------------
generate_router(1, AS_X, peer_links=[(2,1),(3,2)], ibgp_peers=[2,3])
generate_router(2, AS_X, peer_links=[(1,1),(3,3),(4,4)], ibgp_peers=[1,3,4])
generate_router(3, AS_X, peer_links=[(1,2),(2,3),(5,5)], ibgp_peers=[1,2,5])
generate_router(4, AS_X, peer_links=[(2,4),(5,6),(7,7)], ibgp_peers=[2,5,7])
generate_router(5, AS_X, peer_links=[(3,5),(4,6),(6,8),(7,10)], ibgp_peers=[3,4,6,7])
generate_router(6, AS_X, peer_links=[(4,9),(5,8)], ibgp_peers=[4,5])
generate_router(7, AS_X, peer_links=[(4,7),(5,10)], ibgp_peers=[4,5])



# ---------------------------
# Example usage: generate AS Y routers
# ---------------------------
generate_router(8, AS_Y, peer_links=[], ibgp_peers=[9,10,11,12,13,14])
# Continue adding AS Y routers as needed...
