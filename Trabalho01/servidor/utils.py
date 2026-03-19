import struct
import socket

# Formatos para auxiliar o struct.unpack e struct.pack
IP_FORMAT = "!BBHHHBBH4s4s"   
UDP_FORMAT = "!HHHH"          

def unpack_iph(pkg: bytes):
    """Realiza o unpack do header IP (os primeiros 20 bytes do pacote)."""
    return struct.unpack(IP_FORMAT, pkg[0:20])

def unpack_udp(pkg: bytes):
    """Realiza o unpack do header UDP (8 bytes logo após o IP)."""
    return struct.unpack(UDP_FORMAT, pkg[20:28])

def unpack_data(pkg: bytes):
    """Extrai o payload (dados) do pacote."""
    return pkg[28:]

def calculate_checksum(msg: bytes) -> int:
    """Calcula o Checksum de 16 bits para o cabeçalho."""
    if len(msg) % 2 == 1:
        msg += b'\x00'
    
    s = 0
    for i in range(0, len(msg), 2):
        w = (msg[i] << 8) + msg[i+1]
        s += w
        
    s = (s >> 16) + (s & 0xffff)
    s = s + (s >> 16)
    return (~s) & 0xffff

def build_udp_packet(src_ip: str, dest_ip: str, src_port: int, dest_port: int, data: str) -> bytes:
    """Constrói um pacote IP/UDP completo do zero."""
    data_bytes = data.encode('utf-8')
    
    # Header UDP
    udp_length = 8 + len(data_bytes)
    src_ip_bytes = socket.inet_aton(src_ip)
    dest_ip_bytes = socket.inet_aton(dest_ip)
    
    pseudo_header = struct.pack('!4s4sBBH', src_ip_bytes, dest_ip_bytes, 0, 17, udp_length)
    udp_header_temp = struct.pack(UDP_FORMAT, src_port, dest_port, udp_length, 0)
    
    udp_checksum = calculate_checksum(pseudo_header + udp_header_temp + data_bytes)
    udp_header_final = struct.pack(UDP_FORMAT, src_port, dest_port, udp_length, udp_checksum)
    
    # Header IP
    ihl_version = 0x45
    tos = 0
    tot_len = 20 + udp_length
    id_ip = 54321
    frag_off = 0
    ttl = 64
    protocol = 17 # UDP
    ip_check = 0
    
    ip_header_temp = struct.pack(IP_FORMAT, ihl_version, tos, tot_len, id_ip, frag_off, ttl, protocol, ip_check, src_ip_bytes, dest_ip_bytes)
    ip_checksum = calculate_checksum(ip_header_temp)
    ip_header_final = struct.pack(IP_FORMAT, ihl_version, tos, tot_len, id_ip, frag_off, ttl, protocol, ip_checksum, src_ip_bytes, dest_ip_bytes)
    
    return ip_header_final + udp_header_final + data_bytes