#!/bin/bash

echo "[*] Configurando IPs das redes..."

# --- REDE DE SERVIÇO (192.168.10.0/26) ---
# Roteadores conectados à rede de serviço (As interfaces eth1 deles)
docker exec r1_hq ip addr add 192.168.10.1/26 dev eth1
docker exec r2_br1 ip addr add 192.168.10.2/26 dev eth1
docker exec r3_br2 ip addr add 192.168.10.3/26 dev eth1
docker exec r4_edge ip addr add 192.168.10.4/26 dev eth1

# Servidores
docker exec srv_dns ip addr add 192.168.10.10/26 dev eth0
docker exec srv_web ip addr add 192.168.10.11/26 dev eth0
docker exec srv_db ip addr add 192.168.10.12/26 dev eth0

# --- REDE POLO 1 (192.168.10.64/26) ---
docker exec r2_br1 ip addr add 192.168.10.65/26 dev eth0
docker exec pc1_br1 ip addr add 192.168.10.71/26 dev eth0
docker exec pc2_br1 ip addr add 192.168.10.72/26 dev eth0
docker exec pc3_br1 ip addr add 192.168.10.73/26 dev eth0

# --- REDE POLO 2 (192.168.10.128/26) ---
docker exec r3_br2 ip addr add 192.168.10.129/26 dev eth0
docker exec pc1_br2 ip addr add 192.168.10.131/26 dev eth0
docker exec pc2_br2 ip addr add 192.168.10.132/26 dev eth0
docker exec pc3_br2 ip addr add 192.168.10.133/26 dev eth0

# --- REDE GERÊNCIA (192.168.10.192/26) ---
docker exec r1_hq ip addr add 192.168.10.193/26 dev eth0
docker exec admin_pc ip addr add 192.168.10.200/26 dev eth0

# --- REDE INTERNET (Já definida na imagem) ---
docker exec r4_edge ip addr add 203.0.113.1/24 dev eth0
docker exec srv_public_web ip addr add 203.0.113.10/24 dev eth0
docker exec ext_client ip addr add 203.0.113.20/24 dev eth0

echo "[+] IPs configurados com sucesso!"