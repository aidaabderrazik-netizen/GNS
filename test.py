import json
import os

OSPF_PID = 1

with open("config.json") as f:
    data = json.load(f)

for router in data["routers"]:
    gns3_dir = router["gns3_path"]
    startup_config = os.path.join(gns3_dir, "i1_startup-config.cfg")

    if not os.path.isdir(gns3_dir):
        print(f"[ERREUR] Dossier introuvable : {gns3_dir}")
        continue

    with open(startup_config, "w") as f_out:
        f_out.write(f"hostname {router['hostname']}\n")
        f_out.write("ipv6 unicast-routing\n\n")

        # Interfaces
        for iface in router["interfaces"]:
            f_out.write(f"interface {iface['name']}\n")
            f_out.write(f" ipv6 address {iface['ipv6']}\n")
            f_out.write(" no shutdown\n")
            f_out.write(f" ipv6 ospf {OSPF_PID} area {iface['ospf_area']}\n")
            f_out.write("exit\n\n")

        # OSPFv3
        f_out.write(f"ipv6 router ospf {OSPF_PID}\n")
        f_out.write(f" router-id {router['router_id']}\n")
        f_out.write("exit\n")

    print(f"[OK] Config déployée pour {router['hostname']} → {startup_config}")
