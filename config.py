import json
import os

#OSPF_PID = 1

# Charger le fichier JSON
with open("intents.json") as f:
    data = json.load(f)

for router in data["routers"]:
    gns3_dir = router["gns3_path"]

    if not os.path.isdir(gns3_dir):
        print(f"[ERREUR] Dossier introuvable : {gns3_dir}")
        continue

    startup_config = None
    for file in os.listdir(gns3_dir):
        if file.endswith("startup-config.cfg"):
            startup_config = os.path.join(gns3_dir, file)
            break

    if startup_config is None:
        print(f"[ERREUR] Aucun fichier startup-config trouvé dans {gns3_dir}")
        continue


    # Écrire le fichier de config
    with open(startup_config, "w") as f_out:
        # Hostname et routage IPv6
        f_out.write(f"hostname {router['hostname']}\n")
        f_out.write("ipv6 unicast-routing\n\n")


        # Interfaces
        for iface in router["interfaces"]:
            f_out.write(f"interface {iface['name']}\n")
            f_out.write(" no ip address\n")
            f_out.write(" ipv6 enable\n")
            f_out.write(f" ipv6 address {iface['ipv6']}\n")
            f_out.write(" no shutdown\n")
            f_out.write("exit\n\n")

        f_out.write("end\n")
    print(f"[OK] Config déployée pour {router['hostname']} → {startup_config}")
    