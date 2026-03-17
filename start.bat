@echo off
echo Iniciando Flight Price Tracker...
echo.

REM Verificar se Python está instalado
py --version >nul 2>&1
if errorlevel 1 (
    echo ERRO: Python não encontrado. Instale Python 3.12+ primeiro.
    pause
    exit /b 1
)

REM Verificar se .env existe
if not exist .env (
    echo AVISO: Arquivo .env não encontrado.
    echo Copiando .env.example para .env...
    copy .env.example .env
    echo.
    echo IMPORTANTE: Edite o arquivo .env com suas credenciais antes de continuar.
    echo - SERPAPI_API_KEY: Sua chave da SerpApi
    echo - TELEGRAM_BOT_TOKEN: Token do seu bot do Telegram  
    echo - TELEGRAM_CHAT_ID: Seu chat ID do Telegram
    echo.
    pause
)

REM Instalar dependências se necessário
echo Verificando dependências...
py -c "import fastapi, uvicorn, sqlalchemy, httpx, apscheduler" >nul 2>&1
if errorlevel 1 (
    echo Instalando dependências...
    py -m pip install fastapi uvicorn[standard] sqlalchemy httpx apscheduler python-dotenv pydantic-settings
)

REM Inicializar banco de dados
echo Inicializando banco de dados...
py scripts/init_db.py

REM Iniciar aplicação
echo.
echo Iniciando aplicação...
echo Frontend disponível em: http://localhost:8000
echo API docs disponível em: http://localhost:8000/docs
echo.
echo Pressione Ctrl+C para parar
echo.

py -m uvicorn app.main:app --host 0.0.0.0 --port 8000