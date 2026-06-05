/** 
 * RiskGuard — Интеграционная логика фронтенда 
 * Адаптировано под большие объемы данных (пагинация, лоадеры).
 */

// Состояние пагинации
const state = {
    passengers: { page: 1, limit: 15, total: 0 },
    operations: { page: 1, limit: 15, total: 0 }
};

// Помощник для уведомлений (Toast)
function showToast(msg, type = 'info') {
    const toast = document.getElementById('toast');
    const msgElem = document.getElementById('toastMsg');
    const icon = document.getElementById('toastIcon');
    
    msgElem.innerText = msg;
    icon.className = type === 'error' ? 'fas fa-exclamation-circle text-red-500' : 'fas fa-info-circle text-indigo-400';
    
    toast.classList.remove('translate-y-20', 'opacity-0');
    setTimeout(() => toast.classList.add('translate-y-20', 'opacity-0'), 3000);
}

// Управление лоадером
function toggleLoader(show) {
    const loader = document.getElementById('globalLoader');
    if (show) loader.classList.remove('hidden');
    else loader.classList.add('hidden');
}

// Помощник для API-запросов
async function apiCall(url, method = 'GET', body = null, quiet = false) {
    if (!quiet) toggleLoader(true);
    const options = {
        method,
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include'
    };
    if (body) options.body = JSON.stringify(body);

    try {
        const response = await fetch(url, options);
        if (response.status === 401) {
            window.location.href = 'login.html';
            return;
        }
        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || 'API Error');
        }
        return await response.json();
    } catch (e) {
        console.error(`API Call failed [${url}]:`, e);
        throw e;
    } finally {
        if (!quiet) toggleLoader(false);
    }
}

// Глобальное хранилище графиков
const charts = {
    riskTrend: null,
    riskChannel: null,
    liftTerminal: null,
    seatBlock: null
};

// --- ИНИЦИАЛИЗАЦИЯ ЧАРТОВ ---

function initCharts() {
    const gridStyle = { color: 'rgba(226, 232, 240, 0.4)', drawTicks: false };
    const commonOptions = {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { intersect: false, mode: 'index' },
        plugins: {
            legend: { display: false },
            tooltip: {
                backgroundColor: '#1e293b',
                titleFont: { size: 12, weight: 'bold' },
                padding: 12,
                cornerRadius: 10,
                displayColors: false
            }
        },
        scales: {
            x: { grid: { display: false }, ticks: { color: '#94a3b8', font: { size: 10 } } },
            y: { grid: gridStyle, ticks: { color: '#94a3b8', font: { size: 10 }, precision: 0 }, beginAtZero: true }
        }
    };

    const ctx1 = document.getElementById('riskTrendChart').getContext('2d');
    const grad1 = ctx1.createLinearGradient(0, 0, 0, 200);
    grad1.addColorStop(0, 'rgba(249, 115, 22, 0.2)');
    grad1.addColorStop(1, 'rgba(249, 115, 22, 0)');
    charts.riskTrend = new Chart(ctx1, { type: 'line', data: { labels: [], datasets: [{ label: 'Риск-операции', data: [], borderColor: '#f97316', borderWidth: 3, pointBackgroundColor: '#fff', pointBorderColor: '#f97316', pointBorderWidth: 2, pointRadius: 4, tension: 0.4, fill: true, backgroundColor: grad1 }] }, options: commonOptions });

    const ctx2 = document.getElementById('riskChannelChart').getContext('2d');
    charts.riskChannel = new Chart(ctx2, { type: 'bar', data: { labels: [], datasets: [{ label: 'Доля риска (%)', data: [], backgroundColor: '#3b82f6', borderRadius: 8, barThickness: 40 }] }, options: commonOptions });

    const ctx3 = document.getElementById('liftTerminalChart').getContext('2d');
    charts.liftTerminal = new Chart(ctx3, { type: 'bar', data: { labels: [], datasets: [{ label: 'Lift Factor (%)', data: [], backgroundColor: '#ef4444', borderRadius: 8, barThickness: 30 }] }, options: commonOptions });

    const ctx4 = document.getElementById('seatBlockingTrend').getContext('2d');
    const grad4 = ctx4.createLinearGradient(0, 0, 0, 200);
    grad4.addColorStop(0, 'rgba(99, 102, 241, 0.2)');
    grad4.addColorStop(1, 'rgba(99, 102, 241, 0)');
    charts.seatBlock = new Chart(ctx4, { type: 'line', data: { labels: [], datasets: [{ label: 'Инциденты', data: [], borderColor: '#6366f1', borderWidth: 3, pointBackgroundColor: '#fff', pointBorderColor: '#6366f1', pointBorderWidth: 2, pointRadius: 4, tension: 0.4, fill: true, backgroundColor: grad4 }] }, options: commonOptions });
}

// --- РЕНДЕР ДАШБОРДА ---

async function renderDashboard() {
    try {
        const summary = await apiCall('/dashboard/summary');
        document.getElementById('kpi-total-passengers').innerText = summary.total_passengers.toLocaleString();
        document.getElementById('kpi-high-risk').innerText = summary.high_risk_count;
        document.getElementById('kpi-critical-risk').innerText = summary.critical_risk_count;
        document.getElementById('kpi-share-suspicious').innerText = summary.share_suspicious_ops.toFixed(1) + '%';
        document.getElementById('kpi-top-channel').innerText = summary.top_risk_channel || '-';
        document.getElementById('kpi-top-terminal').innerText = summary.top_risk_terminal || '-';

        document.getElementById('trend-high-risk').innerHTML = `<i class="fas fa-arrow-up"></i> 12%`;
        document.getElementById('trend-share-suspicious').innerHTML = `<i class="fas fa-arrow-down"></i> 0.3%`;

        const trend = await apiCall('/dashboard/risk-trend', 'GET', null, true);
        if (trend.items && trend.items.length > 0) {
            charts.riskTrend.data.labels = trend.items.map(i => new Date(i.date).toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit' }));
            charts.riskTrend.data.datasets[0].data = trend.items.map(i => i.highrisk_ops);
        }
        charts.riskTrend.update();

        const channels = await apiCall('/dashboard/risk-concentration?dimension_type=CHANNEL', 'GET', null, true);
        if (channels.items && channels.items.length > 0) {
            charts.riskChannel.data.labels = channels.items.slice(0, 4).map(i => i.dimension_value);
            charts.riskChannel.data.datasets[0].data = channels.items.slice(0, 4).map(i => (i.share_highrisk_ops * 100).toFixed(1));
        }
        charts.riskChannel.update();

        const terminals = await apiCall('/dashboard/risk-concentration?dimension_type=TERMINAL', 'GET', null, true);
        if (terminals.items && terminals.items.length > 0) {
            charts.liftTerminal.data.labels = terminals.items.slice(0, 5).map(i => i.dimension_value);
            charts.liftTerminal.data.datasets[0].data = terminals.items.slice(0, 5).map(i => ((i.lift_vs_base - 1) * 100).toFixed(0));
        }
        charts.liftTerminal.update();

        if (trend.items && trend.items.length > 0) {
            charts.seatBlock.data.labels = trend.items.map((_, idx) => `W${idx+1}`);
            charts.seatBlock.data.datasets[0].data = trend.items.map(i => Math.floor(i.highrisk_ops * 0.4));
        }
        charts.seatBlock.update();
    } catch (e) {
        showToast('Ошибка загрузки дашборда', 'error');
    }
}

// --- ТАБЛИЦА ПАССАЖИРОВ ---

async function renderPassengersTable() {
    const filterRisk = document.getElementById('riskFilter').value;
    const search = document.getElementById('passengerSearchInput').value;
    const { page, limit } = state.passengers;
    const offset = (page - 1) * limit;

    try {
        let url = `/passengers/?limit=${limit}&offset=${offset}`;
        if (filterRisk !== 'all') url += `&risk_band=${filterRisk.toLowerCase()}`;
        if (search) url += `&search=${encodeURIComponent(search)}`;

        const data = await apiCall(url);
        state.passengers.total = data.total;
        
        let html = "";
        data.items.forEach(p => {
            const badgeClass = p.risk_band === 'critical' ? 'risk-critical' : 'risk-high';
            html += `
                <tr class="hover:bg-slate-50 transition-colors group cursor-pointer" onclick="viewProfile('${p.id}')">
                    <td class="px-4 py-4 font-mono font-medium text-slate-400">#${p.id}</td>
                    <td class="px-4 py-4"><span class="font-black text-slate-800 text-base">${p.final_score.toFixed(1)}</span></td>
                    <td class="px-4 py-4"><span class="px-3 py-1 rounded-lg text-[10px] font-bold uppercase tracking-wider ${badgeClass}">${p.risk_band}</span></td>
                    <td class="px-4 py-4 font-semibold text-slate-700">${p.fio_clean}</td>
                    <td class="px-4 py-4 text-slate-400">${p.fake_fio_score.toFixed(2)}</td>
                    <td class="px-4 py-4 whitespace-nowrap text-slate-500">${new Date(p.last_seen_at).toLocaleDateString()}</td>
                    <td class="px-4 py-4 text-right">
                        <button class="w-8 h-8 rounded-lg bg-slate-100 flex items-center justify-center text-slate-400 group-hover:bg-indigo-600 group-hover:text-white transition-all ml-auto">
                            <i class="fas fa-chevron-right text-xs"></i>
                        </button>
                    </td>
                </tr>
            `;
        });
        document.getElementById("passengersTableBody").innerHTML = html || '<tr><td colspan="7" class="p-10 text-center text-slate-400 font-medium">Ничего не найдено</td></tr>';
        
        // Обновление UI пагинации
        document.getElementById('passengersCounter').innerText = `Показано ${offset + 1}-${Math.min(offset + limit, data.total)} из ${data.total}`;
        document.getElementById('passengersPageNum').innerText = page;
        document.getElementById('prevPassengers').disabled = page === 1;
        document.getElementById('nextPassengers').disabled = offset + limit >= data.total;

    } catch (e) {
        showToast('Ошибка загрузки пассажиров', 'error');
    }
}

// --- ОПЕРАЦИИ ---

async function renderOperations() {
    const { page, limit } = state.operations;
    const offset = (page - 1) * limit;

    try {
        const data = await apiCall(`/operations/suspicious?limit=${limit}&offset=${offset}`);
        state.operations.total = data.total;

        let html = "";
        data.items.forEach(op => {
            html += `
                <tr class="hover:bg-slate-50">
                    <td class="p-4 text-slate-500">${new Date(op.op_datetime).toLocaleString()}</td>
                    <td class="p-4 font-mono font-bold text-indigo-600">${op.passenger_id}</td>
                    <td class="p-4">${op.train_no}</td>
                    <td class="p-4 text-slate-400">${op.channel}</td>
                    <td class="p-4">${op.terminal}</td>
                    <td class="p-4 font-bold text-right">${op.amount.toLocaleString()} ₸</td>
                    <td class="p-4 font-black ${op.op_type === 'RETURN' ? 'text-red-500' : 'text-emerald-600'}">${op.op_type}</td>
                </tr>
            `;
        });
        document.getElementById('suspiciousOpsBody').innerHTML = html || '<tr><td colspan="7" class="p-10 text-center">Нет данных</td></tr>';
        
        document.getElementById('operationsCounter').innerText = `Показано ${offset + 1}-${Math.min(offset + limit, data.total)} из ${data.total}`;
        document.getElementById('operationsPageNum').innerText = page;
        document.getElementById('prevOperations').disabled = page === 1;
        document.getElementById('nextOperations').disabled = offset + limit >= data.total;

    } catch (e) {
        showToast('Ошибка загрузки операций', 'error');
    }
}

// --- КАРТОЧКА ПАССАЖИРА ---

async function viewProfile(id) {
    try {
        const p = await apiCall(`/passengers/${id}`);
        const txs = await apiCall(`/passengers/${id}/transactions`, 'GET', null, true);

        document.querySelector('.sidebar-item[data-tab="profile"]').classList.remove('hidden');
        document.querySelector('.sidebar-item[data-tab="profile"]').click();
        
        document.getElementById('profileIdHeader').innerText = `Пассажир: ${p.id}`;
        document.getElementById('profileFioSub').innerText = `ФИО: ${p.fio_clean}`;
        
        const badge = document.getElementById('profileRiskBadge');
        badge.innerText = `Risk: ${p.score.risk_band.toUpperCase()} (${p.score.final_score.toFixed(0)}/100)`;
        badge.className = p.score.risk_band === 'critical' ? 'px-6 py-2 rounded-2xl font-black text-xl shadow-sm bg-red-100 text-red-600' : 'px-6 py-2 rounded-2xl font-black text-xl shadow-sm bg-orange-100 text-orange-600';

        document.getElementById('profileReasons').innerText = p.score.top_reasons.join(', ');
        
        if (p.features) {
            document.getElementById('profileTotalTickets').innerText = p.features.total_tickets;
            document.getElementById('profileRefunds').innerText = p.features.refund_cnt;
            document.getElementById('profileRefundShare').innerText = (p.features.refund_share * 100).toFixed(1) + '%';
            document.getElementById('profileMaxMonth').innerText = p.features.max_tickets_month;
        }

        const seatBox = document.getElementById('profileSeatBlockBox');
        if (p.score.seat_blocking_flag) {
            seatBox.className = "p-6 rounded-2xl flex items-center bg-red-50 border border-red-100 text-red-700";
            seatBox.innerHTML = `<i class="fas fa-user-slash text-2xl mr-4"></i><div><p class="font-bold">Обнаружен Seat-blocking</p><p class="text-xs">Зафиксировано удержание мест перед отправлением</p></div>`;
        } else {
            seatBox.className = "p-6 rounded-2xl flex items-center bg-emerald-50 border border-emerald-100 text-emerald-700";
            seatBox.innerHTML = `<i class="fas fa-check-double text-2xl mr-4"></i><div><p class="font-bold">Аномалий не выявлено</p><p class="text-xs">Признаков удержания мест не обнаружено</p></div>`;
        }

        let txHtml = "";
        txs.forEach(tx => {
            txHtml += `<tr><td class="p-3 text-slate-500">${new Date(tx.op_datetime).toLocaleDateString()}</td><td class="p-3 font-bold ${tx.op_type === 'RETURN' ? 'text-red-600' : 'text-slate-700'}">${tx.op_type}</td><td class="p-3 text-right font-mono">${tx.amount.toLocaleString()} ₸</td></tr>`;
        });
        document.getElementById('profileTxTable').innerHTML = txHtml || '<tr><td colspan="3" class="p-4 text-center">История пуста</td></tr>';
    } catch (e) {
        showToast('Не удалось загрузить профиль', 'error');
    }
}

// --- RISK CONCENTRATION ---

async function renderRiskConcentration() {
    const dims = ['CHANNEL', 'TERMINAL', 'CASHDESK', 'AGGREGATOR'];
    const ids = ['channelConcentrationTable', 'terminalRiskTable', 'cashdeskRiskTable', 'aggregatorTable'];
    for (let i = 0; i < dims.length; i++) {
        try {
            const data = await apiCall(`/dashboard/risk-concentration?dimension_type=${dims[i]}`, 'GET', null, true);
            let html = `<table class="w-full text-xs"><thead class="bg-slate-50 text-slate-400 font-bold uppercase tracking-wider"><tr><th class="p-2 text-left">Имя</th><th class="p-2">Доля</th><th class="p-2 text-right">Lift</th></tr></thead><tbody class="divide-y divide-slate-50">`;
            data.items.slice(0, 5).forEach(item => {
                const lift = ((item.lift_vs_base - 1) * 100).toFixed(0);
                const liftColor = lift > 0 ? 'text-red-500' : 'text-emerald-500';
                html += `<tr><td class="p-2 font-medium">${item.dimension_value}</td><td class="p-2 text-center text-slate-600">${(item.share_highrisk_ops * 100).toFixed(1)}%</td><td class="p-2 text-right font-black ${liftColor}">${lift > 0 ? '+' : ''}${lift}%</td></tr>`;
            });
            html += "</tbody></table>";
            document.getElementById(ids[i]).innerHTML = html;
        } catch (e) {}
    }
}

// --- НАВИГАЦИЯ ---

const tabs = document.querySelectorAll('.sidebar-item');
const contents = document.querySelectorAll('.tab-content');

tabs.forEach(tab => {
    tab.addEventListener('click', () => {
        const target = tab.getAttribute('data-tab');
        if (!target) return;
        contents.forEach(c => c.classList.remove('active-tab'));
        document.getElementById(target).classList.add('active-tab');
        tabs.forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        document.getElementById('pageTitle').innerText = { dashboard: "Дашборд аналитики", passengers: "Контроль пассажиров", operations: "История операций", riskmap: "Анализ концентрации", profile: "Детальный профиль", upload: "Центр управления данными", reports: "Экспорт и отчетность" }[target] || "Аналитика";
        
        if (target === 'dashboard') renderDashboard();
        if (target === 'passengers') { state.passengers.page = 1; renderPassengersTable(); }
        if (target === 'operations') { state.operations.page = 1; renderOperations(); }
        if (target === 'riskmap') renderRiskConcentration();
    });
});

// События пагинации
document.getElementById('prevPassengers').addEventListener('click', () => { if (state.passengers.page > 1) { state.passengers.page--; renderPassengersTable(); } });
document.getElementById('nextPassengers').addEventListener('click', () => { if (state.passengers.page * state.passengers.limit < state.passengers.total) { state.passengers.page++; renderPassengersTable(); } });
document.getElementById('prevOperations').addEventListener('click', () => { if (state.operations.page > 1) { state.operations.page--; renderOperations(); } });
document.getElementById('nextOperations').addEventListener('click', () => { if (state.operations.page * state.operations.limit < state.operations.total) { state.operations.page++; renderOperations(); } });

// Поиск и Фильтры
document.getElementById('riskFilter').addEventListener('change', () => { state.passengers.page = 1; renderPassengersTable(); });
document.getElementById('passengerSearchInput').addEventListener('input', () => { state.passengers.page = 1; renderPassengersTable(); });

// Загрузка файла
document.getElementById('excelInput').addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const formData = new FormData();
    formData.append('file', file);
    showToast('Начата загрузка файла...');
    try {
        const res = await fetch('/uploads/excel', { method: 'POST', body: formData, credentials: 'include' });
        const data = await res.json();
        showToast(`Файл принят. ID: ${data.id}. Подождите завершения обработки.`, 'info');
    } catch (e) {
        showToast('Ошибка загрузки', 'error');
    }
});

document.addEventListener('DOMContentLoaded', () => {
    initCharts();
    renderDashboard();
    renderPassengersTable();
    renderOperations();
    renderRiskConcentration();
});