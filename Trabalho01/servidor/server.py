import socket
import os
import time
from rich import print
from utils import build_udp_packet, unpack_iph, unpack_udp, unpack_data, build_rtp_header

def send_catalog(sender, src_ip: str, src_port: int, client_ip: str, client_port: int):
    """Envia uma mensagem de catálogo para o cliente."""

    video_dir = "./videos"

    try:
        # Busca todos os arquivos na pasta que terminam com .ts
        arquivos = [f for f in os.listdir(video_dir) if f.endswith('.ts')]
        
        if len(arquivos) == 0:
            msg = "Catálogo de Vídeos:\n[Vazio] Nenhum vídeo .ts encontrado no servidor."
        else:
            msg = "Catálogo de Vídeos:\n"
            for i, video in enumerate(arquivos, 1):
                msg += f"{i}. {video}\n"
                
    except FileNotFoundError:
        msg = "[Erro] A pasta 'videos' não existe no servidor!"

    packet = build_udp_packet(
        src_ip=src_ip, 
        dest_ip=client_ip, 
        src_port=src_port, 
        dest_port=client_port, 
        data=msg.strip()
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
            ip_packet = raw_packet[14:]

            if len(ip_packet) < 28:
                continue

            # --- TAREFA: PROCESSAMENTO DO CABEÇALHO IP ---
            # 1. Chamar unpack_iph(raw_packet)
            iph = unpack_iph(ip_packet)

            # 2. Validar se o protocolo é UDP (valor 17)
            if iph[6] != 17:
                continue

            # --- TAREFA: PROCESSAMENTO DO CABEÇALHO UDP ---
            # 1. Chamar unpack_udp(raw_packet)
            udph = unpack_udp(ip_packet)
            
            # 2. Validar se a porta de destino do pacote é a porta do servidor (src_port)
            dst_port2 = udph[1]
            if dst_port2 != src_port:
                continue
            
            # --- TAREFA: PAYLOAD E LÓGICA ---
            # 1. Chamar unpack_data(raw_packet)
            data = unpack_data(ip_packet).decode('utf-8', errors='ignore').strip()
            client_ip = socket.inet_ntoa(iph[8])
            client_port = udph[0]

            print(f"[*] Mensagem recebida de {client_ip}:{client_port} -> '{data}'")

            # 2. Se o dado for 'catalog', chamar a função send_catalog()            
            if data == 'catalog':
                send_catalog(sender, src_ip, src_port, client_ip, client_port)
            
            # --- TAREFA: Streaming ---
            elif data.startswith('stream '):
                nome_video = data[7:].strip()
                caminho_video = os.path.join("./videos", nome_video)
                
                print(f"[*] Cliente solicitou o vídeo: {nome_video}")
                
                if not os.path.exists(caminho_video):
                    msg_aviso = f"[Erro] O vídeo '{nome_video}' não foi encontrado no servidor!"

                    pct = build_udp_packet(src_ip, client_ip, src_port, client_port, msg_aviso)
                    sender.sendto(pct, (client_ip, 0))
                else:
                    msg_aviso = f"[Servidor] Arquivo '{nome_video}' encontrado! Preparando stream RTP..."
                    print(f"[+] Arquivo encontrado. Iniciando leitura...")
                    
                    pct = build_udp_packet(src_ip, client_ip, src_port, client_port, msg_aviso)
                    sender.sendto(pct, (client_ip, 0))
                    
                    stream_video(sender, src_ip, src_port, client_ip, client_port, caminho_video)
                    
            else:
                print(f"[-] Comando desconhecido recebido: '{data}'. Avisando cliente.")
                msg_erro = f"[Erro] Comando '{data}' não reconhecido. Use 'catalog' ou 'stream <nome_do_video>'."
                
                pct_erro = build_udp_packet(
                    src_ip=src_ip, 
                    dest_ip=client_ip, 
                    src_port=src_port, 
                    dest_port=client_port, 
                    data=msg_erro
                )
                sender.sendto(pct_erro, (client_ip, 0))

    except KeyboardInterrupt:
        print("\n[!] Desligando servidor...")
    finally:
        sender.close()
        sniffer.close()

def stream_video(sender, src_ip, src_port, client_ip, client_port, caminho_video):
    """Lê o arquivo de vídeo e envia em pacotes RTP."""
    
    CHUNK_SIZE = 1316
    seq_num = 0
    timestamp = 0
    
    print(f"[>] Iniciando transmissão de {caminho_video} para {client_ip}:{client_port}")
    
    try:
        with open(caminho_video, 'rb') as f:
            while True:
                # Lê um pedaço do vídeo
                chunk = f.read(CHUNK_SIZE)
                if not chunk:
                    break
                
                # Monta os cabeçalhos
                rtp_header = build_rtp_header(seq_num, timestamp)
                
                # O payload do UDP agora é o RTP + os bytes do vídeo
                pacote_completo = rtp_header + chunk
                
                packet = build_udp_packet(
                    src_ip=src_ip, 
                    dest_ip=client_ip, 
                    src_port=src_port, 
                    dest_port=client_port, 
                    data=pacote_completo
                )
                
                sender.sendto(packet, (client_ip, 0))
                
                # Atualiza os contadores do RTP
                seq_num = (seq_num + 1) % 65536 # Evita estourar o limite de 16 bits
                timestamp += 90000 // 30 # Incremento fictício para simular 30 FPS
                
                # IMPORTANTE: Um pequeno atraso para não "afogar" a rede e o cliente
                time.sleep(0.0005) 
                
        print(f"[+] Transmissão concluída com sucesso! ({seq_num} pacotes enviados)")
        
        # Envia uma mensagem final avisando que o stream acabou
        msg_fim = "[Servidor] EOF: Transmissão do vídeo encerrada."
        pct_fim = build_udp_packet(src_ip, client_ip, src_port, client_port, msg_fim)
        sender.sendto(pct_fim, (client_ip, 0))
        
    except Exception as e:
        print(f"[!] Erro durante o stream: {e}")

if __name__ == "__main__":
    start_server("eth0", "10.0.1.2", 65535, 9999, 12345)