// Configuração da API
const API_BASE_URL = 'http://localhost:8000';

// Estado global
let routes = [];
let currentEditingRoute = null;

// Inicialização
document.addEventListener('DOMContentLoaded', function() {
    // Configurar datas mínimas
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('departure_date').min = today;
    document.getElementById('return_date').min = today;
    
    // Carregar rotas iniciais
    loadRoutes();
    loadRoutesForHistory();
    
    // Event listeners
    document.getElementById('route-form').addEventListener('submit', handleAddRoute);
    document.getElementById('edit-form').addEventListener('submit', handleEditRoute);
    
    // Atualizar data de volta quando data de ida mudar
    document.getElementById('departure_date').addEventListener('change', function() {
        const departureDate = this.value;
        const returnDateInput = document.getElementById('return_date');
        returnDateInput.min = departureDate;
        
        if (returnDateInput.value && returnDateInput.value <= departureDate) {
            returnDateInput.value = '';
        }
    });
});

// Gerenciamento de tabs
function showTab(tabName, event = null) {
    // Esconder todas as tabs
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Remover classe active de todos os botões
    document.querySelectorAll('.tab-button').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Mostrar tab selecionada
    document.getElementById(tabName + '-tab').classList.add('active');
    
    // Ativar botão correspondente se event foi fornecido
    if (event && event.target) {
        event.target.classList.add('active');
    } else {
        // Se não há event, encontrar e ativar o botão correto
        const buttons = document.querySelectorAll('.tab-button');
        buttons.forEach(btn => {
            if (btn.onclick && btn.onclick.toString().includes(`showTab('${tabName}')`)) {
                btn.classList.add('active');
            }
        });
    }
    
    // Carregar dados específicos da tab
    if (tabName === 'routes') {
        loadRoutes();
    } else if (tabName === 'history') {
        loadRoutesForHistory();
    } else if (tabName === 'admin') {
        loadSystemStatus();
    }
}

// Carregar rotas
async function loadRoutes() {
    const routesList = document.getElementById('routes-list');
    const filterActive = document.getElementById('filter-active').checked;
    
    try {
        routesList.innerHTML = '<div class="loading">Carregando rotas...</div>';
        
        let url = `${API_BASE_URL}/route-watches`;
        if (filterActive) {
            url += '?is_active=true';
        }
        
        const response = await fetch(url);
        if (!response.ok) throw new Error('Erro ao carregar rotas');
        
        routes = await response.json();
        
        if (routes.length === 0) {
            routesList.innerHTML = `
                <div class="text-center" style="grid-column: 1 / -1;">
                    <p class="text-muted">Nenhuma rota encontrada.</p>
                    <button class="btn btn-primary" onclick="showTab('add-route')">
                        <i class="fas fa-plus"></i> Adicionar Primeira Rota
                    </button>
                </div>
            `;
            return;
        }
        
        routesList.innerHTML = routes.map(route => createRouteCard(route)).join('');
        
    } catch (error) {
        console.error('Erro ao carregar rotas:', error);
        routesList.innerHTML = `
            <div class="alert alert-error" style="grid-column: 1 / -1;">
                Erro ao carregar rotas. Verifique se a API está rodando.
            </div>
        `;
    }
}

// Criar card de rota
function createRouteCard(route) {
    const departureDate = new Date(route.departure_date).toLocaleDateString('pt-BR');
    const returnDate = new Date(route.return_date).toLocaleDateString('pt-BR');
    const createdDate = new Date(route.created_at).toLocaleDateString('pt-BR');
    
    return `
        <div class="route-card">
            <div class="route-header">
                <div class="route-title">
                    ${route.origin} → ${route.destination}
                </div>
                <div class="route-status ${route.is_active ? 'status-active' : 'status-inactive'}">
                    ${route.is_active ? 'Ativa' : 'Inativa'}
                </div>
            </div>
            
            <div class="route-details">
                <div class="route-detail">
                    <span><i class="fas fa-calendar-alt"></i> Modo:</span>
                    <strong>${route.flexible_dates ? '🎯 Flexível' : '📍 Exato'}</strong>
                </div>
                <div class="route-detail">
                    <span><i class="fas fa-calendar-alt"></i> ${route.flexible_dates ? 'Janela de Ida:' : 'Data de Ida:'}</span>
                    <strong>${route.flexible_dates ? 'A partir de ' : ''}${departureDate}</strong>
                </div>
                <div class="route-detail">
                    <span><i class="fas fa-calendar-alt"></i> ${route.flexible_dates ? 'Janela de Volta:' : 'Data de Volta:'}</span>
                    <strong>${route.flexible_dates ? 'Até ' : ''}${returnDate}</strong>
                </div>
                <div class="route-detail">
                    <span><i class="fas fa-users"></i> Passageiros:</span>
                    <strong>${route.adults}</strong>
                </div>
                <div class="route-detail">
                    <span><i class="fas fa-chair"></i> Classe:</span>
                    <strong>${translateCabinClass(route.cabin_class)}</strong>
                </div>
                <div class="route-detail">
                    <span><i class="fas fa-money-bill"></i> Moeda:</span>
                    <strong>${route.currency}</strong>
                </div>
                <div class="route-detail">
                    <span><i class="fas fa-bell"></i> Alertas:</span>
                    <strong>${route.notify_on_new_low ? 'Ativados' : 'Desativados'}</strong>
                </div>
                ${route.target_price ? `
                <div class="route-detail">
                    <span><i class="fas fa-bullseye"></i> Preço Alvo:</span>
                    <strong>${route.currency} ${route.target_price}</strong>
                </div>
                ` : ''}
                <div class="route-detail">
                    <span><i class="fas fa-plus"></i> Criada em:</span>
                    <strong>${createdDate}</strong>
                </div>
            </div>
            
            <div class="route-actions">
                <button class="btn btn-primary btn-sm" onclick="checkRoutePrice(${route.id})">
                    <i class="fas fa-search"></i> Verificar Preço
                </button>
                <button class="btn btn-secondary btn-sm" onclick="openEditModal(${route.id})">
                    <i class="fas fa-edit"></i> Editar
                </button>
                <button class="btn btn-warning btn-sm" onclick="viewHistory(${route.id})">
                    <i class="fas fa-chart-line"></i> Histórico
                </button>
                <button class="btn ${route.is_active ? 'btn-warning' : 'btn-success'} btn-sm" 
                        onclick="toggleRouteStatus(${route.id}, ${!route.is_active})">
                    <i class="fas fa-power-off"></i> ${route.is_active ? 'Desativar' : 'Ativar'}
                </button>
            </div>
        </div>
    `;
}

// Traduzir classe da cabine
function translateCabinClass(cabinClass) {
    const translations = {
        'ECONOMY': 'Econômica',
        'PREMIUM_ECONOMY': 'Econômica Premium',
        'BUSINESS': 'Executiva',
        'FIRST': 'Primeira Classe'
    };
    return translations[cabinClass] || cabinClass;
}

// Adicionar nova rota
async function handleAddRoute(event) {
    event.preventDefault();
    
    const formData = new FormData(event.target);
    const routeData = {
        origin: document.getElementById('origin').value.toUpperCase(),
        destination: document.getElementById('destination').value.toUpperCase(),
        departure_date: document.getElementById('departure_date').value,
        return_date: document.getElementById('return_date').value,
        adults: parseInt(document.getElementById('adults').value),
        cabin_class: document.getElementById('cabin_class').value,
        currency: document.getElementById('currency').value,
        check_interval_minutes: parseInt(document.getElementById('check_interval_minutes').value),
        notify_on_new_low: document.getElementById('notify_on_new_low').checked,
        flexible_dates: document.getElementById('flexible_dates').checked,
    };
    
    // Campos opcionais
    const minPriceDiff = document.getElementById('min_price_difference').value;
    if (minPriceDiff) routeData.min_price_difference = parseFloat(minPriceDiff);
    
    const cooldown = document.getElementById('alert_cooldown_hours').value;
    if (cooldown) routeData.alert_cooldown_hours = parseInt(cooldown);
    
    const targetPrice = document.getElementById('target_price').value;
    if (targetPrice) routeData.target_price = parseFloat(targetPrice);
    
    try {
        const response = await fetch(`${API_BASE_URL}/route-watches/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(routeData)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Erro ao criar rota');
        }
        
        // Limpar formulário
        event.target.reset();
        
        // Mostrar sucesso
        showAlert('Rota adicionada com sucesso!', 'success');
        
        // Voltar para tab de rotas (sem event)
        showTab('routes');
        
    } catch (error) {
        console.error('Erro ao adicionar rota:', error);
        showAlert('Erro ao adicionar rota: ' + error.message, 'error');
    }
}

// Verificar preço de uma rota
async function checkRoutePrice(routeId) {
    try {
        const response = await fetch(`${API_BASE_URL}/route-watches/${routeId}/check`, {
            method: 'POST'
        });
        
        if (!response.ok) throw new Error('Erro ao verificar preço');
        
        const result = await response.json();
        
        if (result.success) {
            const searchDate = new Date(result.searched_at).toLocaleString('pt-BR');
            const source = result.from_cache ? 'histórico' : 'nova consulta';
            const airline = result.airline ? ` (${result.airline})` : '';

            // Comentário (pt-BR): calcula informações de passageiros e preço por pessoa para deixar o alerta mais claro
            const passengers = result.passengers || 1;
            const totalPrice = result.price_total;
            const pricePerPassenger = totalPrice && passengers
                ? (totalPrice / passengers).toFixed(2)
                : null;

            const passengersInfo = passengers > 1
                ? ` | ${passengers} passageiros`
                : ' | 1 passageiro';

            const perPassengerInfo = pricePerPassenger
                ? ` (≈ ${result.currency} ${pricePerPassenger} por pessoa)`
                : '';
            
            // Mostrar informação sobre a melhor combinação encontrada
            let flightInfo = '';
            if (result.departure_at && result.return_at) {
                const depDate = new Date(result.departure_at).toLocaleDateString('pt-BR');
                const retDate = new Date(result.return_at).toLocaleDateString('pt-BR');
                flightInfo = ` - Melhor combinação: ${depDate} até ${retDate}`;
            }
            
            showAlert(
                `Preço total: ${result.currency} ${totalPrice}${perPassengerInfo}${airline}${passengersInfo}${flightInfo} - ${source} em ${searchDate}`, 
                'success'
            );
        } else {
            showAlert('Falha na verificação: ' + result.message, 'error');
        }
        
    } catch (error) {
        console.error('Erro ao verificar preço:', error);
        showAlert('Erro ao verificar preço', 'error');
    }
}

// Alternar status da rota
async function toggleRouteStatus(routeId, newStatus) {
    try {
        const response = await fetch(`${API_BASE_URL}/route-watches/${routeId}`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ is_active: newStatus })
        });
        
        if (!response.ok) throw new Error('Erro ao alterar status');
        
        showAlert(`Rota ${newStatus ? 'ativada' : 'desativada'} com sucesso!`, 'success');
        loadRoutes();
        
    } catch (error) {
        console.error('Erro ao alterar status:', error);
        showAlert('Erro ao alterar status da rota', 'error');
    }
}

// Abrir modal de edição
function openEditModal(routeId) {
    const route = routes.find(r => r.id === routeId);
    if (!route) return;
    
    currentEditingRoute = route;
    
    // Preencher formulário - campos básicos
    document.getElementById('edit-route-id').value = route.id;
    document.getElementById('edit-is-active').checked = route.is_active;
    document.getElementById('edit-departure-date').value = route.departure_date;
    document.getElementById('edit-return-date').value = route.return_date;
    document.getElementById('edit-adults').value = route.adults;
    document.getElementById('edit-cabin-class').value = route.cabin_class;
    document.getElementById('edit-currency').value = route.currency;
    document.getElementById('edit-max-stops').value = route.max_stops || '';
    document.getElementById('edit-check-interval').value = route.check_interval_minutes;
    document.getElementById('edit-flexible-dates').checked = route.flexible_dates;
    
    // Atualizar labels baseado no modo
    toggleEditDateMode();
    
    // Preencher formulário - configurações de alerta
    document.getElementById('edit-notify-on-new-low').checked = route.notify_on_new_low;
    document.getElementById('edit-min-price-difference').value = route.min_price_difference || '';
    document.getElementById('edit-alert-cooldown').value = route.alert_cooldown_hours || '';
    document.getElementById('edit-target-price').value = route.target_price || '';
    
    // Configurar datas mínimas
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('edit-departure-date').min = today;
    document.getElementById('edit-return-date').min = today;
    
    // Atualizar data de volta quando data de ida mudar
    document.getElementById('edit-departure-date').addEventListener('change', function() {
        const departureDate = this.value;
        const returnDateInput = document.getElementById('edit-return-date');
        returnDateInput.min = departureDate;
        
        if (returnDateInput.value && returnDateInput.value <= departureDate) {
            returnDateInput.value = '';
        }
    });
    
    // Mostrar modal
    document.getElementById('edit-modal').style.display = 'block';
}

// Fechar modal de edição
function closeEditModal() {
    document.getElementById('edit-modal').style.display = 'none';
    currentEditingRoute = null;
}

// Salvar edição da rota
async function handleEditRoute(event) {
    event.preventDefault();
    
    const routeId = document.getElementById('edit-route-id').value;
    const updateData = {
        is_active: document.getElementById('edit-is-active').checked,
        departure_date: document.getElementById('edit-departure-date').value,
        return_date: document.getElementById('edit-return-date').value,
        adults: parseInt(document.getElementById('edit-adults').value),
        cabin_class: document.getElementById('edit-cabin-class').value,
        currency: document.getElementById('edit-currency').value,
        check_interval_minutes: parseInt(document.getElementById('edit-check-interval').value),
        notify_on_new_low: document.getElementById('edit-notify-on-new-low').checked,
        flexible_dates: document.getElementById('edit-flexible-dates').checked,
    };
    
    // Campos opcionais
    const maxStops = document.getElementById('edit-max-stops').value;
    if (maxStops) updateData.max_stops = parseInt(maxStops);
    
    const minPriceDiff = document.getElementById('edit-min-price-difference').value;
    if (minPriceDiff) updateData.min_price_difference = parseFloat(minPriceDiff);
    
    const cooldown = document.getElementById('edit-alert-cooldown').value;
    if (cooldown) updateData.alert_cooldown_hours = parseInt(cooldown);
    
    const targetPrice = document.getElementById('edit-target-price').value;
    if (targetPrice) updateData.target_price = parseFloat(targetPrice);
    
    try {
        const response = await fetch(`${API_BASE_URL}/route-watches/${routeId}`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(updateData)
        });
        
        if (!response.ok) throw new Error('Erro ao atualizar rota');
        
        closeEditModal();
        showAlert('Rota atualizada com sucesso!', 'success');
        loadRoutes();
        
    } catch (error) {
        console.error('Erro ao atualizar rota:', error);
        showAlert('Erro ao atualizar rota', 'error');
    }
}

// Carregar rotas para seleção de histórico
async function loadRoutesForHistory() {
    try {
        // Buscar apenas rotas ativas
        const response = await fetch(`${API_BASE_URL}/route-watches?is_active=true`);
        if (!response.ok) throw new Error('Erro ao carregar rotas');
        
        const routes = await response.json();
        const select = document.getElementById('route-select');
        
        select.innerHTML = '<option value="">Selecione uma rota...</option>';
        routes.forEach(route => {
            const option = document.createElement('option');
            option.value = route.id;
            const modeIcon = route.flexible_dates ? '🎯' : '📍';
            option.textContent = `${modeIcon} ${route.origin} → ${route.destination} (${new Date(route.departure_date).toLocaleDateString('pt-BR')})`;
            select.appendChild(option);
        });
        
        if (routes.length === 0) {
            select.innerHTML = '<option value="">Nenhuma rota ativa encontrada</option>';
        }
        
    } catch (error) {
        console.error('Erro ao carregar rotas para histórico:', error);
        const select = document.getElementById('route-select');
        select.innerHTML = '<option value="">Erro ao carregar rotas</option>';
    }
}

// Ver histórico de uma rota
function viewHistory(routeId) {
    // Mudar para tab de histórico
    showTab('history');
    
    // Selecionar a rota
    document.getElementById('route-select').value = routeId;
    
    // Carregar histórico
    loadHistory();
}

// Carregar histórico de preços
async function loadHistory() {
    const routeId = document.getElementById('route-select').value;
    const historyContent = document.getElementById('history-content');
    
    if (!routeId) {
        historyContent.innerHTML = '<p class="text-muted">Selecione uma rota para ver o histórico de preços</p>';
        return;
    }
    
    try {
        historyContent.innerHTML = '<div class="loading">Carregando histórico...</div>';
        
        const response = await fetch(`${API_BASE_URL}/route-watches/${routeId}/history`);
        if (!response.ok) throw new Error('Erro ao carregar histórico');
        
        const history = await response.json();
        
        if (history.length === 0) {
            historyContent.innerHTML = '<p class="text-muted">Nenhum histórico de preços encontrado para esta rota.</p>';
            return;
        }
        
        historyContent.innerHTML = history.map(item => createHistoryItem(item)).join('');
        
    } catch (error) {
        console.error('Erro ao carregar histórico:', error);
        historyContent.innerHTML = '<div class="alert alert-error">Erro ao carregar histórico de preços</div>';
    }
}

// Criar item de histórico
function createHistoryItem(item) {
    const searchDate = new Date(item.searched_at).toLocaleString('pt-BR');
    
    // Formatar datas de saída e retorno se existirem
    const departureFormatted = item.departure_at ? 
        new Date(item.departure_at).toLocaleString('pt-BR') : 'N/A';
    const returnFormatted = item.return_at ? 
        new Date(item.return_at).toLocaleString('pt-BR') : 'N/A';
    
    // Mostrar informação sobre a janela vs voos encontrados
    const route = routes.find(r => r.id === parseInt(document.getElementById('route-select').value));
    let windowInfo = '';
    
    if (route && item.departure_at && item.return_at) {
        const windowStart = new Date(route.departure_date).toLocaleDateString('pt-BR');
        const windowEnd = new Date(route.return_date).toLocaleDateString('pt-BR');
        
        windowInfo = `
            <div class="window-info">
                <i class="fas fa-info-circle"></i>
                <strong>Janela de busca:</strong> ${windowStart} até ${windowEnd}
                <br><strong>Melhor combinação encontrada:</strong> ${new Date(item.departure_at).toLocaleDateString('pt-BR')} até ${new Date(item.return_at).toLocaleDateString('pt-BR')}
            </div>
        `;
    }
    
    const passengers = item.passengers || (route ? route.adults : 1) || 1;
    const pricePerPassenger = item.price_per_passenger || (item.price_total && passengers
        ? (item.price_total / passengers)
        : null);

    const passengersInfo = passengers > 1
        ? `${passengers} passageiros`
        : '1 passageiro';

    const perPassengerInfo = pricePerPassenger
        ? ` (≈ ${item.currency} ${pricePerPassenger.toFixed(2)} por pessoa)`
        : '';

    return `
        <div class="history-item">
            <div class="history-header">
                <div class="history-price">
                    ${item.currency} ${item.price_total}${perPassengerInfo}
                    <div class="history-passengers">${passengersInfo}</div>
                </div>
                <div class="history-date">${searchDate}</div>
            </div>
            ${windowInfo}
            <div class="history-details">
                <div><strong>Companhia:</strong> ${item.airline || 'N/A'}</div>
                <div><strong>Código:</strong> ${item.airline_code || 'N/A'}</div>
                <div>
                    <strong>Escalas:</strong>
                    ${item.stops === 0
                        ? 'Direto'
                        : item.stops !== null
                            ? item.stops
                            : 'N/A'}
                </div>
                <div><strong>Voo de Ida:</strong> ${departureFormatted}</div>
                <div><strong>Voo de Volta:</strong> ${returnFormatted}</div>
                <div><strong>Provider:</strong> ${item.provider}</div>
            </div>
        </div>
    `;
}

// Mostrar alerta
function showAlert(message, type) {
    // Remover alertas existentes
    document.querySelectorAll('.alert').forEach(alert => alert.remove());
    
    // Criar novo alerta
    const alert = document.createElement('div');
    alert.className = `alert alert-${type}`;
    alert.textContent = message;
    
    // Inserir no topo do container
    const container = document.querySelector('.container');
    container.insertBefore(alert, container.firstChild);
    
    // Remover após 5 segundos
    setTimeout(() => {
        alert.remove();
    }, 5000);
}

// Fechar modal ao clicar fora
window.onclick = function(event) {
    const modal = document.getElementById('edit-modal');
    if (event.target === modal) {
        closeEditModal();
    }
}

// Funções da aba Admin
async function loadSystemStatus() {
    const statusDiv = document.getElementById('system-status');
    
    try {
        statusDiv.innerHTML = '<div class="loading">Carregando status...</div>';
        
        const response = await fetch(`${API_BASE_URL}/health`);
        if (!response.ok) throw new Error('Erro ao carregar status');
        
        const status = await response.json();
        
        statusDiv.innerHTML = `
            <div class="status-item">
                <span class="status-label">Status da API</span>
                <span class="status-value status-healthy">Online</span>
            </div>
            <div class="status-item">
                <span class="status-label">Scheduler</span>
                <span class="status-value ${status.scheduler === 'running' ? 'status-healthy' : 'status-error'}">
                    ${status.scheduler === 'running' ? 'Rodando' : 'Parado'}
                </span>
            </div>
            <div class="status-item">
                <span class="status-label">Última Verificação</span>
                <span class="status-value">${new Date().toLocaleString('pt-BR')}</span>
            </div>
        `;
        
    } catch (error) {
        console.error('Erro ao carregar status:', error);
        statusDiv.innerHTML = `
            <div class="status-item">
                <span class="status-label">Status da API</span>
                <span class="status-value status-error">Offline</span>
            </div>
        `;
    }
}

async function forceCheckAll() {
    try {
        showAlert('Iniciando verificação forçada de todas as rotas...', 'info');
        
        const response = await fetch(`${API_BASE_URL}/admin/force-check`, {
            method: 'POST'
        });
        
        if (!response.ok) throw new Error('Erro ao forçar verificação');
        
        const result = await response.json();
        
        if (result.error) {
            showAlert('Erro: ' + result.error, 'error');
        } else {
            showAlert('Verificação forçada executada com sucesso!', 'success');
        }
        
    } catch (error) {
        console.error('Erro ao forçar verificação:', error);
        showAlert('Erro ao executar verificação forçada', 'error');
    }
}

async function checkSystemHealth() {
    await loadSystemStatus();
    showAlert('Status do sistema atualizado', 'success');
}
// Função para alternar modo de data
function toggleDateMode() {
    const isFlexible = document.getElementById('flexible_dates').checked;
    const departureLabel = document.getElementById('departure-label');
    const returnLabel = document.getElementById('return-label');
    const departureHelp = document.getElementById('departure-help');
    const returnHelp = document.getElementById('return-help');
    const explanation = document.getElementById('search-explanation');
    
    if (isFlexible) {
        // Modo flexível
        departureLabel.textContent = 'Data de Ida (início da janela)';
        returnLabel.textContent = 'Data de Volta (fim da janela)';
        departureHelp.textContent = 'Data mais cedo que você pode viajar';
        returnHelp.textContent = 'Data mais tarde que você pode voltar';
        
        explanation.innerHTML = `
            <p><strong>Janela de Busca Inteligente:</strong></p>
            <p>• <strong>Data de Ida:</strong> A partir de quando você pode viajar</p>
            <p>• <strong>Data de Volta:</strong> Até quando você pode voltar</p>
            <p>• <strong>O sistema encontra a combinação mais barata</strong> dentro dessa janela</p>
            <p>• Exemplo: Janela 01/09 até 06/09 → Melhor oferta: ida 01/09 + volta 02/09</p>
        `;
    } else {
        // Modo exato
        departureLabel.textContent = 'Data de Ida (exata)';
        returnLabel.textContent = 'Data de Volta (exata)';
        departureHelp.textContent = 'Data exata da viagem de ida';
        returnHelp.textContent = 'Data exata da viagem de volta';
        
        explanation.innerHTML = `
            <p><strong>Busca por Datas Exatas:</strong></p>
            <p>• <strong>Data de Ida:</strong> Voos apenas nesta data específica</p>
            <p>• <strong>Data de Volta:</strong> Voos apenas nesta data específica</p>
            <p>• <strong>O sistema busca apenas voos nas datas escolhidas</strong></p>
            <p>• Exemplo: Ida 01/09 + Volta 06/09 → Apenas voos nessas datas exatas</p>
        `;
    }
}

// Função para alternar modo de data no modal de edição
function toggleEditDateMode() {
    const isFlexible = document.getElementById('edit-flexible-dates').checked;
    const departureLabel = document.getElementById('edit-departure-label');
    const returnLabel = document.getElementById('edit-return-label');
    const departureHelp = document.getElementById('edit-departure-help');
    const returnHelp = document.getElementById('edit-return-help');
    
    if (isFlexible) {
        // Modo flexível
        departureLabel.textContent = 'Data de Ida (início da janela)';
        returnLabel.textContent = 'Data de Volta (fim da janela)';
        departureHelp.textContent = 'Data mais cedo que você pode viajar';
        returnHelp.textContent = 'Data mais tarde que você pode voltar';
    } else {
        // Modo exato
        departureLabel.textContent = 'Data de Ida (exata)';
        returnLabel.textContent = 'Data de Volta (exata)';
        departureHelp.textContent = 'Data exata da viagem de ida';
        returnHelp.textContent = 'Data exata da viagem de volta';
    }
}