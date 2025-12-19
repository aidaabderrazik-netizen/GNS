import json
import os

JSON_FILE = "routers.json"

# Load existing data or create a dictionary if the file doesn't exist
if os.path.exists(JSON_FILE):
    with open(JSON_FILE, "r") as f:
        data_list = json.load(f)
        # Convert list to dict keyed by router name for easy duplicate checking
        data = {r["name"]: r for r in data_list}
else:
    data = {}

AS_X = 10
AS_Y = 20

def generate_router(router_num, as_number=AS_X, peer_links=[], gns_path=""):
    """
    Generate router details automatically based on router number.
    - router_num: integer, e.g., 4 for R4
    - as_number: AS number
    - peer_links: list of tuples (peer_num, link_num), e.g., [(5,6),(7,7)]
    - gns_path: path to the GNS3 file, to build the configuration
    """
    name = f"R{router_num}"
    router_id_bgp = f"{1 if as_number==AS_X else 2}.{1}.{1}.{router_num}"
    loopback = f"2001:192:100:255::{router_num}/128"

    # If router exists, get its current interfaces; else create new
    if name in data:
        router = data[name]
        print(f"Router {name} already exists. Adding new interfaces if any...")
        # Update gns_path if provided
        if gns_path:
            router["gns_path"] = gns_path
    else:
        router = {
            "name": name,
            "as_number": as_number,
            "router_id_bgp": router_id_bgp,
            "loopback": loopback,
            "ospf_area": 0,
            "gns_path": gns_path,
            "interfaces": []
        }

    # Add interfaces, avoiding duplicates
    for peer_num, link_num in peer_links:
        peer_name = f"R{peer_num}"
        local_ip = f"2001:192:168:{link_num}::1/64"
        peer_ip = f"2001:192:168:{link_num}::2/64"

        # Check if interface to this peer already exists
        if any(iface["peer"] == peer_name for iface in router["interfaces"]):
            print(f"Interface to {peer_name} already exists for {name}, skipping...")
            continue

        router["interfaces"].append({
            "peer": peer_name,
            "local_ip": local_ip,
            "peer_ip": peer_ip
        })

    # Save router back to dictionary
    data[name] = router

    # Save entire data to JSON
    with open(JSON_FILE, "w") as f:
        json.dump(list(data.values()), f, indent=4)
    print(f"Router {name} processed successfully!\n")

# ---------------------------
# Example usage: generate routers
# ---------------------------

generate_router(1, AS_X, peer_links=[(2,1),(3,2)],gns_path="/home/user/gns3/project/GNS")
generate_router(2, AS_X, peer_links=[(1,1),(3,3),(4,4)],gns_path="/home/user/gns3/project/GNS")
generate_router(3, AS_X, peer_links=[(1,2),(2,3),(5,5)],gns_path="/home/user/gns3/project/GNS")
generate_router(4, AS_X, peer_links=[(2,4),(5,6),(7,7)],gns_path="/home/user/gns3/project/GNS")
generate_router(5, AS_X, peer_links=[(3,5),(4,6),(6,8),(7,10)],gns_path="/home/user/gns3/project/GNS")
generate_router(6, AS_X, peer_links=[(4,9),(5,8)],gns_path="/home/user/gns3/project/GNS")
generate_router(7, AS_X, peer_links=[(4,7),(5,10)],gns_path="/home/user/gns3/project/GNS")
