# Usa uma imagem oficial e leve do Python
FROM python:3.10-slim

# Instala ferramentas de rede essenciais e a biblioteca rich que o prof usou
RUN apt-get update && apt-get install -y iproute2 net-tools tcpdump iputils-ping \
    && pip install rich \
    && rm -rf /var/lib/apt/lists/*

# Define a pasta de trabalho dentro do container
WORKDIR /app

# Mantém o container rodando no fundo infinitamente para podermos entrar nele depois
CMD ["tail", "-f", "/dev/null"]