# Flight Price Tracker - Frontend

Interface web para configurar e monitorar rotas de voos.

## 🚀 Como Usar

1. **Inicie a API:**
   ```bash
   py -m uvicorn app.main:app --reload --port 8000
   ```

2. **Acesse o frontend:**
   - Abra http://localhost:8000 no seu navegador
   - Ou acesse diretamente: http://localhost:8000/static/index.html

## 📱 Funcionalidades

### ✈️ Minhas Rotas
- Visualizar todas as rotas monitoradas
- Filtrar por rotas ativas/inativas
- Verificar preço manualmente
- Ativar/desativar rotas
- Editar configurações de alerta

### ➕ Adicionar Rota
- Configurar origem e destino (códigos IATA)
- Definir datas de ida e volta
- Escolher número de passageiros e classe
- Configurar alertas:
  - Diferença mínima para alertar
  - Cooldown entre alertas
  - Preço alvo

### 📊 Histórico
- Ver histórico de preços de cada rota
- Detalhes de cada consulta (companhia, escalas, horários)
- Ordenação por data

## 🎨 Interface

- **Design responsivo** - funciona em desktop e mobile
- **Tema moderno** com gradientes e animações
- **Ícones Font Awesome** para melhor UX
- **Feedback visual** com alertas de sucesso/erro

## 🔧 Configuração

O frontend se conecta automaticamente com a API em `http://localhost:8000`.

Para alterar a URL da API, edite a variável `API_BASE_URL` no arquivo `script.js`.

## 📋 Códigos IATA Comuns

### Portugal
- **LIS** - Lisboa
- **OPO** - Porto
- **FAO** - Faro

### Brasil
- **GRU** - São Paulo (Guarulhos)
- **GIG** - Rio de Janeiro (Galeão)
- **BSB** - Brasília
- **SSA** - Salvador
- **FOR** - Fortaleza

### Europa
- **MAD** - Madrid
- **BCN** - Barcelona
- **CDG** - Paris
- **LHR** - Londres
- **FCO** - Roma

### América do Norte
- **JFK** - Nova York
- **LAX** - Los Angeles
- **MIA** - Miami
- **YYZ** - Toronto

## 🛠️ Desenvolvimento

O frontend é uma SPA (Single Page Application) usando:
- **HTML5** semântico
- **CSS3** com Flexbox/Grid
- **JavaScript ES6+** vanilla (sem frameworks)
- **Font Awesome** para ícones

### Estrutura de Arquivos
```
frontend/
├── index.html      # Página principal
├── style.css       # Estilos CSS
├── script.js       # Lógica JavaScript
└── README.md       # Esta documentação
```