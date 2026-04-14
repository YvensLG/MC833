from scapy.all import IP, Ether, TCP, Raw, sniff, sendp, get_if_hwaddr, getmacbyip

IFACE_A = "eth0" # Rede A
IFACE_B = "eth1" # Rede B

MAC_A = get_if_hwaddr(IFACE_A)
MAC_B = get_if_hwaddr(IFACE_B)

# Cache de MAC para não travar o roteador com requisições ARP lentas
cache_mac = {}

# ---> NOVA FUNÇÃO DE DEFESA <---
def is_malicious(pkt):
    if pkt.haslayer(TCP):
        flags = pkt[TCP].flags
        
        # Assinatura 1: XMAS Scan (Flags FIN, PSH, URG ativadas = 'FPU' ou 0x29)
        if flags == 'FPU' or flags == 0x29:
            print("[BLOCK] Bloqueando pacote de TCP XMAS Scan!")
            return True
            
        # Assinatura 2: NULL Scan (Nenhuma flag ativada)
        if flags == '' or flags == 0:
            print("[BLOCK] Bloqueando pacote de TCP NULL Scan!")
            return True
            
        # Assinatura 3: Pacote SYN (início de conexão) contendo dados na camada Raw (Hping3)
        if flags == 'S' and pkt.haslayer(Raw) and len(pkt[Raw].load) > 0:
            print("[BLOCK] Bloqueando pacote SYN anômalo com Payload!")
            return True

    return False
# -------------------------------

def forward_packet(pkt):
    # 1. Verificações básicas
    if not pkt.haslayer(IP) or not pkt.haslayer(Ether):
        return

    # 2. Evitar loops
    if pkt[Ether].src in [MAC_A, MAC_B]:
        return

    # Se a função retornar True, nós interrompemos o roteamento (Drop)
    if is_malicious(pkt):
        return 

    # 3. Determinar interface de saída e MAC de origem
    dst_ip = pkt[IP].dst
    if dst_ip.startswith("10.0.1."):
        out_iface = IFACE_A
        mac_origem = MAC_A
    elif dst_ip.startswith("10.0.2."):
        out_iface = IFACE_B
        mac_origem = MAC_B
    else:
        return

    # 4. Descobrir MAC de destino
    mac_destino = cache_mac.get(dst_ip) or getmacbyip(dst_ip)
    if not mac_destino:
        return
    cache_mac[dst_ip] = mac_destino

    # 5. PREPARAÇÃO DO PACOTE PARA REENVIO
    pkt[Ether].src = mac_origem
    pkt[Ether].dst = mac_destino
    pkt[IP].ttl -= 1
    
    del pkt[IP].chksum
    if pkt.haslayer('TCP'):
        del pkt['TCP'].chksum
    elif pkt.haslayer('UDP'):
        del pkt['UDP'].chksum

    # 6. ENVIAR VIA CAMADA 2
    print(f"Encaminhando {pkt[IP].src} -> {pkt[IP].dst} via {out_iface}")
    sendp(pkt, iface=out_iface, verbose=False)

print("Roteador Scapy com IPS Ativo...")
sniff(iface=[IFACE_A, IFACE_B], prn=forward_packet, store=0)