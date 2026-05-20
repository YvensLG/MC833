#!/bin/bash

echo "[*] Configurando Regras de Firewall (iptables)..."

# ==============================================================
# REGRAS NO ROTEADOR CENTRAL (r1_hq) - Controla tráfego interno
# ==============================================================

# 1. Isolamento entre Polos (Bloqueio Bidirecional)
# Bloqueia Polo 1 (192.168.10.64/26) indo para Polo 2 (192.168.10.128/26) e vice-versa
docker exec r1_hq iptables -A FORWARD -s 192.168.10.64/26 -d 192.168.10.128/26 -j DROP
docker exec r1_hq iptables -A FORWARD -s 192.168.10.128/26 -d 192.168.10.64/26 -j DROP

# 2. Isolamento da Gerência (Bloqueio Bidirecional com Polos)
# Bloqueia Polo 1 <-> Gerência (192.168.10.192/26)
docker exec r1_hq iptables -A FORWARD -s 192.168.10.64/26 -d 192.168.10.192/26 -j DROP
docker exec r1_hq iptables -A FORWARD -s 192.168.10.192/26 -d 192.168.10.64/26 -j DROP
# Bloqueia Polo 2 <-> Gerência
docker exec r1_hq iptables -A FORWARD -s 192.168.10.128/26 -d 192.168.10.192/26 -j DROP
docker exec r1_hq iptables -A FORWARD -s 192.168.10.192/26 -d 192.168.10.128/26 -j DROP

# 3. Proteção do Banco de Dados (Ninguém além dos servidores pode acessar)
# Bloqueia Polos e Gerência tentando acessar o DB (192.168.10.12)
docker exec r1_hq iptables -A FORWARD -s 192.168.10.64/26 -d 192.168.10.12/32 -j DROP
docker exec r1_hq iptables -A FORWARD -s 192.168.10.128/26 -d 192.168.10.12/32 -j DROP
docker exec r1_hq iptables -A FORWARD -s 192.168.10.192/26 -d 192.168.10.12/32 -j DROP

# ==============================================================
# REGRAS NO ROTEADOR DE BORDA (r4_edge) - Controla a Internet
# ==============================================================

# 4. Stateful Firewall: Invasores não podem iniciar conexões
# Permite que pacotes de conexões JÁ ESTABELECIDAS (respostas) voltem para a rede interna (eth1)
docker exec r4_edge iptables -A FORWARD -i eth0 -o eth1 -m state --state ESTABLISHED,RELATED -j ACCEPT

# Bloqueia qualquer pacote novo tentando entrar da Internet (eth0) para a rede interna (eth1)
docker exec r4_edge iptables -A FORWARD -i eth0 -o eth1 -j DROP
# ... (restante do código anterior) ...

# 5. Correção do Atalho (Bloqueio direto nos Roteadores dos Polos para o DB)
docker exec r2_br1 iptables -A FORWARD -d 192.168.10.12 -j DROP
docker exec r3_br2 iptables -A FORWARD -d 192.168.10.12 -j DROP

echo "[+] Regras de Firewall aplicadas com sucesso!"