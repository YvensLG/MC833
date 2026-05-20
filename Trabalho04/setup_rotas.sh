#!/bin/bash

echo "[*] Configurando Rotas e Gateways..."

# ==========================================
# 1. GATEWAYS PADRÕES DOS DISPOSITIVOS FINAIS
# ==========================================
# --- Polo 1 (Apontam para o R2_BR1)
docker exec pc1_br1 ip route replace default via 192.168.10.65
docker exec pc2_br1 ip route replace default via 192.168.10.65
docker exec pc3_br1 ip route replace default via 192.168.10.65

# --- Polo 2 (Apontam para o R3_BR2)
docker exec pc1_br2 ip route replace default via 192.168.10.129
docker exec pc2_br2 ip route replace default via 192.168.10.129
docker exec pc3_br2 ip route replace default via 192.168.10.129

# --- Gerência (Aponta para o R1_HQ)
docker exec admin_pc ip route replace default via 192.168.10.193

# --- Servidores (Apontam para o R1_HQ)
docker exec srv_dns ip route replace default via 192.168.10.1
docker exec srv_web ip route replace default via 192.168.10.1
docker exec srv_db ip route replace default via 192.168.10.1

# ==========================================
# 2. ROTEAMENTO DOS ROTEADORES DE BORDA
# ==========================================
# R2, R3 e R4 mandam tudo que não conhecem para o R1_HQ
docker exec r2_br1 ip route replace default via 192.168.10.1
docker exec r3_br2 ip route replace default via 192.168.10.1
docker exec r4_edge ip route replace default via 192.168.10.1

# ==========================================
# 3. ROTEAMENTO DO ROTEADOR CENTRAL (R1_HQ)
# ==========================================
# O R1_HQ precisa saber onde estão as redes dos Polos
docker exec r1_hq ip route replace 192.168.10.64/26 via 192.168.10.2
docker exec r1_hq ip route replace 192.168.10.128/26 via 192.168.10.3
docker exec r1_hq ip route replace default via 192.168.10.4

echo "[+] Rotas configuradas com sucesso (sem conflitos)!"