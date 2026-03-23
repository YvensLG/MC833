import socket
from rich import print
from rich.markdown import Markdown
from utils import build_udp_packet, unpack_iph, unpack_udp, unpack_data

# Porta onde o cliente espera receber a resposta
REC_PORT = 12345

def start_client():
    """
    Inicia o cliente de streaming utilizando Raw Sockets.
    Você deve garantir que as funções de unpack e build_packet estejam prontas.
    """

    # Socket para ENVIAR pacotes (Nível IP bruto)
    sender = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_RAW)
    sender.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)

    # Socket para SNIFFING (Capturar pacotes que chegam na interface)
    # Nota: "eth0" deve ser alterado conforme a interface da máquina
    sniffer = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.ntohs(3))
    sniffer.bind(("eth0", 0))

    dest_ip = "10.0.1.2" # IP do Servidor

    print(Markdown("""# Aplicação de Streaming (Client-Side)
    - Digite **catalog** para listar vídeos.
    - Digite **stream <nome_do_video>** para assistir.
    - Digite **q** para sair.
    """))
    print("-" * 25)

    try:
        while True:            
            msg = input("\nVocê (Cliente) > ")
            if msg == 'q': break

            is_streaming = msg.startswith('stream ')
            nome_video = msg[7:].strip() if is_streaming else ""

            # Você deve usar sua implementação de build_udp_packet aqui
            packet = build_udp_packet(
                src_ip="10.0.2.2", 
                dest_ip=dest_ip,
                src_port=REC_PORT,
                dest_port=9999,
                data=msg
            )

            sender.sendto(packet, (dest_ip, 0))
            print("[-] Pacote enviado. Aguardando resposta do servidor...")

            # Variáveis de controle para o download
            arquivo_destino = f"download_{nome_video}"
            f = None
            download_sucesso = False

            # --- TAREFA: FILTRAGEM E UNPACK ---
            try:
                while True:
                    # Captura o pacote bruto da rede
                    raw_packet, _ = sniffer.recvfrom(65535)
                    ip_packet = raw_packet[14:]

                    # 1. Verificar se o pacote tem o tamanho mínimo (IP + UDP = 28 bytes)
                    if len(ip_packet) < 28: 
                        continue

                    # 2. Extrair o Header IP usando unpack_iph()
                    iph = unpack_iph(ip_packet)
                    
                    # 3. Validar se o protocolo no Header IP é UDP (17)
                    if iph[6] != 17:
                        continue
                    
                    # 4. Extrair o Header UDP usando unpack_udp()
                    udph = unpack_udp(ip_packet)

                    # 5. Validar se a porta de destino (Dest Port) é a REC_PORT do cliente
                    if udph[1] != REC_PORT: continue
                    
                    # 6. Extrair os dados usando unpack_data()
                    data = unpack_data(ip_packet)

                    # Como saber se é texto do servidor ou se é byte de vídeo?
                    if data.startswith(b"[Servidor]") or data.startswith(b"[Erro]") or data.startswith(b"Cat"):
                        texto = data.decode("utf-8", errors="ignore")
                        print(f'> Server: {texto}')

                        if not is_streaming:
                            break
                            
                        if "[Erro]" in texto:
                            break
                            
                        if "Preparando stream" in texto:
                            f = open(arquivo_destino, "wb")
                            print(f"[*] Criando arquivo '{arquivo_destino}' no disco...")
                            
                        if "EOF" in texto:
                            download_sucesso = True
                            break
                    
                    else:
                        if is_streaming and f is not None:
                            if len(data) > 12:
                                chunk_video = data[12:]
                                f.write(chunk_video)

            finally:
                if f is not None and not f.closed:
                    f.close()
                
                if download_sucesso:
                    print(f"[+] Download do vídeo '{nome_video}' concluído com sucesso!\n")

    except KeyboardInterrupt:
        print("\n[!] Encerrando cliente...")
    finally:
        sender.close()
        sniffer.close()

if __name__ == "__main__":
    start_client()