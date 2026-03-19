import socket
from rich import print
from utils import build_udp_packet, unpack_iph, unpack_udp, unpack_data

def send_catalog(sender, src_ip: str, src_port: int, client_ip: str, client_port: int):
    """Envia uma mensagem de catálogo para o cliente."""
    
    msg = "Catálogo de Vídeos:\n1. video1.ts\n2. video2.ts\n3. video3.ts"

    packet = build_udp_packet(
        src_ip=src_ip, 
        dest_ip=client_ip, 
        src_port=src_port, 
        dest_port=client_port, 
        data=msg
    )
    
    sender.sendto(packet, (client_ip, 0))
    print(f"[+] Catálogo enviado para {client_ip}:{client_port}")

def start_server(interface, src_ip, buffer_size, src_port, dst_port):
    """Loop principal do servidor que escuta pacotes brutos e processa comandos."""
    
    sender = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_RAW)
    sender.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)

    sniffer = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.ntohs(3))
    sniffer.bind((interface, 0))

    print(f"[+] Servidor rodando em {src_ip}:{src_port} na interface {interface}")

    try:
        while True:
            raw_packet, _ = sniffer.recvfrom(buffer_size)

            if len(raw_packet) < 28:
                continue

            # --- TAREFA: PROCESSAMENTO DO CABEÇALHO IP ---
            # 1. Chamar unpack_iph(raw_packet)
            iph = unpack_iph(raw_packet)

            # 2. Validar se o protocolo é UDP (valor 17)
            if iph[6] != 17:
                continue

            # --- TAREFA: PROCESSAMENTO DO CABEÇALHO UDP ---
            # 1. Chamar unpack_udp(raw_packet)
            udph = unpack_udp(raw_packet)
            
            # 2. Validar se a porta de destino do pacote é a porta do servidor (src_port)
            dst_port2 = udph[1]
            if dst_port2 != src_port:
                continue
            
            # --- TAREFA: PAYLOAD E LÓGICA ---
            # 1. Chamar unpack_data(raw_packet)
            data = unpack_data(raw_packet).decode('utf-8', errors='ignore').strip()

            client_ip = socket.inet_ntoa(iph[8])
            client_port = udph[0]

            print(f"[*] Mensagem recebida de {client_ip}:{client_port} -> '{data}'")

            # 2. Se o dado for 'catalog', chamar a função send_catalog()            
            if data == 'catalog':
                send_catalog(sender, src_ip, src_port, client_ip, client_port)
            
            # --- TAREFA: Streaming ---
            elif data.startswith('stream'):
                print(f"[*] Iniciando processo de stream para o pedido: {data}")
                # Por enquanto, mandamos um aviso de que estamos construindo essa parte
                msg_aviso = "[Servidor] Comando de stream recebido! Preparando os pacotes RTP..."
                pct = build_udp_packet(src_ip, client_ip, src_port, client_port, msg_aviso)
                sender.sendto(pct, (client_ip, 0))

    except KeyboardInterrupt:
        print("\n[!] Desligando servidor...")
    finally:
        sender.close()
        sniffer.close()

if __name__ == "__main__":
    start_server("eth0", "10.0.1.2", 65535, 9999, 12345)