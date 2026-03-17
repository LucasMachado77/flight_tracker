# Flight Price Tracker

Sistema de rastreamento de preços de passagens aéreas que monitora rotas específicas periodicamente, armazena histórico de preços e envia alertas quando detecta novos preços mínimos históricos.

## Características

- Monitoramento automático de preços de voos via SerpApi (Google Flights)
- Armazenamento completo de histórico de preços
- Detecção de novos mínimos históricos
- Alertas via Telegram
- API REST para gerenciamento de rotas
- Suporte a múltiplas rotas simultâneas
- Configuração de cooldown e margem mínima para alertas

## Requisitos

- Python 3.12+
- Conta SerpApi com API key
- Bot do Telegram configurado

## Instalação

1. Clone o repositório:
```bash
git clone <repository-url>
cd flight-price-tracker
```

2. Crie um ambiente virtual:
```bash
python -m venv venv
source venv/bin/activate  # No Windows: venv\Scripts\activate
```

3. Instale as dependências:
```bash
pip install -r requirements.txt
```

4. Configure as variáveis de ambiente:
```bash
cp .env.example .env
# Edite .env com suas credenciais
```

## Configuração

Edite o arquivo `.env` com suas credenciais:

```env
# Database Configuration
DATABASE_URL=sqlite:///./flight_tracker.db

# SerpApi Configuration
SERPAPI_API_KEY=your_serpapi_api_key_here
SERPAPI_TIMEOUT=30.0

# Telegram Configuration
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
TELEGRAM_CHAT_ID=your_telegram_chat_id_here

# Logging Configuration
LOG_LEVEL=INFO
```

### Obtendo Credenciais

**SerpApi:**
1. Crie uma conta em https://serpapi.com/
2. Obtenha sua API key no dashboard
3. Configure `SERPAPI_API_KEY` no arquivo `.env`

**Telegram:**
1. Crie um bot conversando com @BotFather no Telegram
2. Obtenha o token do bot
3. Inicie uma conversa com seu bot
4. Obtenha seu chat ID usando: https://api.telegram.org/bot<TOKEN>/getUpdates
5. Configure `TELEGRAM_BOT_TOKEN` e `TELEGRAM_CHAT_ID` no arquivo `.env`

## Estrutura do Projeto

```
flight-price-tracker/
├── app/
│   ├── api/          # Endpoints FastAPI
│   ├── core/         # Configuração e utilitários
│   ├── jobs/         # Jobs agendados
│   ├── models/       # Modelos SQLAlchemy
│   ├── repositories/ # Camada de acesso a dados
│   └── services/     # Lógica de negócio
├── scripts/          # Scripts auxiliares
├── tests/            # Testes
├── .env              # Variáveis de ambiente (não versionado)
├── .env.example      # Exemplo de configuração
├── requirements.txt  # Dependências Python
└── README.md         # Este arquivo
```

## Uso

### Início Rápido

**Windows:**
```bash
# Executar script de inicialização
start.bat
```

**Linux/Mac:**
```bash
# Dar permissão e executar
chmod +x start.sh
./start.sh
```

**Manual:**
```bash
# 1. Configurar ambiente
cp .env.example .env
# Edite .env com suas credenciais

# 2. Instalar dependências
py -m pip install fastapi uvicorn[standard] sqlalchemy httpx apscheduler python-dotenv pydantic-settings

# 3. Inicializar banco
py scripts/init_db.py

# 4. Iniciar aplicação
py -m uvicorn app.main:app --reload --port 8000
```

### Acessar a Aplicação

- **Frontend:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health

### ⚡ Verificação Automática

**O sistema agora roda automaticamente!** 🎉

- **Scheduler integrado** roda junto com a API
- **Não precisa executar jobs separados**
- **Verifica rotas baseado no intervalo individual** de cada rota
- **Primeira verificação** após 1 minuto de inicialização
- **Verificações subsequentes** respeitam o intervalo configurado

### Configurar Rotas

1. **Acesse o frontend** em http://localhost:8000
2. **Clique em "Adicionar Rota"**
3. **Configure:**
   - Origem e destino (códigos IATA)
   - Datas de ida e volta
   - Número de passageiros e classe
   - **Intervalo de verificação** (3h, 6h, 12h, 24h)
   - **Alertas:** diferença mínima, cooldown, preço alvo

### Monitoramento

- **Aba "Minhas Rotas":** Ver todas as rotas e status
- **Aba "Histórico":** Acompanhar evolução de preços
- **Aba "Admin":** Status do sistema e verificação forçada

## API Endpoints

### Rotas Monitoradas

- `POST /route-watches` - Criar nova rota monitorada
- `GET /route-watches` - Listar todas as rotas
- `GET /route-watches?is_active=true` - Listar apenas rotas ativas
- `GET /route-watches/{id}` - Obter rota específica
- `PATCH /route-watches/{id}` - Atualizar rota (ativar/desativar)

### Histórico e Consultas

- `GET /route-watches/{id}/history` - Consultar histórico de preços
- `POST /route-watches/{id}/check` - Forçar consulta manual de preço

### Exemplo de Requisição

```bash
# Criar rota monitorada
curl -X POST http://localhost:8000/route-watches \
  -H "Content-Type: application/json" \
  -d '{
    "origin": "LIS",
    "destination": "GRU",
    "departure_date": "2026-07-15",
    "return_date": "2026-07-30",
    "adults": 2,
    "cabin_class": "ECONOMY",
    "check_interval_minutes": 360,
    "notify_on_new_low": true
  }'
```

## Testes

Executar todos os testes:
```bash
pytest
```

Executar apenas testes unitários:
```bash
pytest -m unit
```

Executar apenas testes de propriedade:
```bash
pytest -m property
```

Executar com cobertura:
```bash
pytest --cov=app --cov-report=html
```

## Desenvolvimento

### Adicionar Nova Dependência

```bash
pip install <package>
pip freeze > requirements.txt
```

### Estrutura de Camadas

1. **API Layer** (`app/api/`): Endpoints FastAPI, validação de entrada
2. **Service Layer** (`app/services/`): Lógica de negócio, coordenação
3. **Repository Layer** (`app/repositories/`): Acesso a dados, queries
4. **Model Layer** (`app/models/`): Definições SQLAlchemy
5. **Core** (`app/core/`): Configuração, utilitários compartilhados

### Convenções de Código

- Usar type hints em todas as funções
- Documentar funções públicas com docstrings
- Seguir PEP 8 para estilo de código
- Escrever testes para novas funcionalidades

## Troubleshooting

### Erro: "Missing required configuration"

Verifique se todas as variáveis obrigatórias estão definidas no arquivo `.env`:
- `SERPAPI_API_KEY`
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

### Erro: "Provider error 401 Unauthorized"

Sua API key do SerpApi está inválida ou expirada. Verifique no dashboard da SerpApi.

### Alertas não estão sendo enviados

1. Verifique se `notify_on_new_low=true` na RouteWatch
2. Verifique se há cooldown configurado bloqueando alertas
3. Verifique os logs para erros de comunicação com Telegram
4. Teste o bot manualmente enviando uma mensagem

## Licença

MIT License

## Suporte

Para reportar bugs ou solicitar funcionalidades, abra uma issue no repositório.
