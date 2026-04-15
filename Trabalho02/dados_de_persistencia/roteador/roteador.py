import csv
from datetime import datetime
from scapy.all import IP, Ether, TCP, UDP, Raw, sniff, sendp, get_if_hwaddr, getmacbyip

IFACE_A = "eth0" # Rede A
IFACE_B = "eth1" # Rede B

MAC_A = get_if_hwaddr(IFACE_A)
MAC_B = get_if_hwaddr(IFACE_B)

cache_mac = {}
LOG_FILE = "/app/data.csv"

# Inicializa o arquivo CSV com os cabeçalhos
with open(LOG_FILE, mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(["Timestamp", "IP_Origem", "IP_Destino", "Protocolo", "Tamanho_Bytes", "Status", "Motivo"])

def registrar_pacote(ip_src, ip_dst, proto, tamanho, status, motivo="OK"):
    try:
        with open(LOG_FILE, mode='a', newline='') as file:
            writer = csv.writer(file)
            agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            writer.writerow([agora, ip_src, ip_dst, proto, tamanho, status, motivo])
    except:
        pass

def is_malicious(pkt):
    if pkt.haslayer(TCP):
        flags = pkt[TCP].flags
        
        # Assinatura 1: XMAS Scan (Flags FIN, PSH, URG ativadas simultaneamente)
        if flags == 'FPU' or flags == 0x29:
            print("[BLOCK] XMAS Scan!")
            return True, "XMAS Scan"
            
        # Assinatura 2: NULL Scan (Nenhuma flag ativada)
        if flags == '' or flags == 0:
            print("[BLOCK] NULL Scan!")
            return True, "NULL Scan"
            
        # Assinatura 3: FIN Scan (Apenas a flag FIN ativada - A nossa correção!)
        if flags == 'F' or flags == 0x01:
            print("[BLOCK] FIN Scan!")
            return True, "FIN Scan"
            
        # Assinatura 4: Pacote SYN anômalo com Payload extra (Hping3)
        if flags == 'S' and pkt.haslayer(Raw) and len(pkt[Raw].load) > 0:
            print("[BLOCK] SYN com Payload!")
            return True, "SYN com Payload"

    return False, ""

def forward_packet(pkt):
    if not pkt.haslayer(IP) or not pkt.haslayer(Ether):
        return

    if pkt[Ether].src in [MAC_A, MAC_B]:
        return

    # Extraindo dados para o Log
    src_ip = pkt[IP].src
    dst_ip = pkt[IP].dst
    tamanho = len(pkt)
    
    proto = "Outro"
    if pkt.haslayer(TCP): proto = "TCP"
    elif pkt.haslayer(UDP): proto = "UDP"

    # Nosso IPS agindo e registrando no CSV
    malicioso, motivo = is_malicious(pkt)
    if malicioso:
        registrar_pacote(src_ip, dst_ip, proto, tamanho, "BLOQUEADO", motivo)
        return 

    # Roteamento normal (Pacote Limpo)
    if dst_ip.startswith("10.0.1."):
        out_iface = IFACE_A
        mac_origem = MAC_A
    elif dst_ip.startswith("10.0.2."):
        out_iface = IFACE_B
        mac_origem = MAC_B
    else:
        return

    mac_destino = cache_mac.get(dst_ip) or getmacbyip(dst_ip)
    if not mac_destino: return
    cache_mac[dst_ip] = mac_destino

    pkt[Ether].src = mac_origem
    pkt[Ether].dst = mac_destino
    pkt[IP].ttl -= 1
    
    del pkt[IP].chksum
    if pkt.haslayer('TCP'): del pkt['TCP'].chksum
    elif pkt.haslayer('UDP'): del pkt['UDP'].chksum

    # Registra o pacote legítimo e envia
    registrar_pacote(src_ip, dst_ip, proto, tamanho, "PERMITIDO")
    sendp(pkt, iface=out_iface, verbose=False)

print("Roteador + IPS V2 (Atualizado) + Data Logger Ativo...")
sniff(iface=[IFACE_A, IFACE_B], prn=forward_packet, store=0)