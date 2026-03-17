#!/bin/bash

echo "Iniciando Flight Price Tracker..."
echo

# Verificar se Python está instalado
if ! command -v python3 &> /dev/null; then
    echo "ERRO: Python 3 não encontrado. Instale Python 3.12+ primeiro."
    exit 1
fi

# Verificar se .env existe
if [ ! -f .env ]; then
    echo "AVISO: Arquivo .env não encontrado."
    echo "Copiando .env.example para .env..."
    cp .env.example .env
    echo
    echo "IMPORTANTE: Edite o arquivo .env com suas credenciais antes de continuar."
    echo "- SERPAPI_API_KEY: Sua chave da SerpApi"
    echo "- TELEGRAM_BOT_TOKEN: Token do seu bot do Telegram"
    echo "- TELEGRAM_CHAT_ID: Seu chat ID do Telegram"
    echo
    read -p "Pressione Enter para continuar..."
fi

# Instalar dependências se necessário
echo "Verificando dependências..."
python3 -c "import fastapi, uvicorn, sqlalchemy, httpx, apscheduler" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Instalando dependências..."
    python3 -m pip install fastapi uvicorn[standard] sqlalchemy httpx apscheduler python-dotenv pydantic-settings
fi

# Inicializar banco de dados
echo "Inicializando banco de dados..."
python3 scripts/init_db.py

# Iniciar aplicação
echo
echo "Iniciando aplicação..."
echo "Frontend disponível em: http://localhost:8000"
echo "API docs disponível em: http://localhost:8000/docs"
echo
echo "Pressione Ctrl+C para parar"
echo

python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000