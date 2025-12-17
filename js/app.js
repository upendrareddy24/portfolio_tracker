// Portfolio Tracker Logic

// Default Categories (7 static topics)
const defaultPortfolio = [
    { id: 2, name: "SH Swing", tickers: [], icon: "fa-bolt", color: "red", period: "1-5D" },
    { id: 3, name: "Swing/Sq", tickers: [], icon: "fa-arrow-trend-up", color: "green", period: "2-20D" },
    { id: 4, name: "POS- BO/SQ", tickers: [], icon: "fa-arrow-up-right-dots", color: "yellow", period: "2-20W (6mo)" },
    { id: 5, name: "POS-HVOL", tickers: [], icon: "fa-chart-line", color: "yellow", period: "2-20W (6mo)" },
    { id: 6, name: "POS-PAT", tickers: [], icon: "fa-diagram-project", color: "yellow", period: "2-20W (6mo)" },
    { id: 7, name: "INV", tickers: [], icon: "fa-piggy-bank", color: "blue", period: "3M-2Y" },
    { id: 8, name: "OPT-Swing", tickers: [], icon: "fa-clover", color: "red", period: "1D-90D" },
    { id: 9, name: "Lot", tickers: [], icon: "fa-dice", color: "red", period: "1-5D" }
];

let portfolio = JSON.parse(localStorage.getItem('stellarPortfolio')) || defaultPortfolio;
let currentEditingId = null;

// DOM Elements
const grid = document.getElementById('category-grid');
const modal = document.getElementById('ticker-modal');
const closeModal = document.querySelector('.close-modal');
const tickerForm = document.getElementById('ticker-form');
const tickerListTextarea = document.getElementById('ticker-list');
const excelInput = document.getElementById('excel-upload');

// Initialize Dashboard
function renderDashboard() {
    grid.innerHTML = '';
    portfolio.forEach(cat => {
        const card = document.createElement('div');
        card.className = `category-card color-${cat.color}`;
        card.innerHTML = `
            <div class="card-header">
                <span class="account-number">#${cat.id}</span>
                <span class="holding-period">${cat.period}</span>
            </div>
            <i class="fas ${cat.icon} card-icon"></i>
            <h3>${cat.name}</h3>
            <div class="ticker-list">
                ${cat.tickers.length > 0 ? cat.tickers.map(t => `<span class="ticker-tag">${t}</span>`).join('') : '<span class="empty-msg">No tickers added</span>'}
            </div>
            <button class="edit-btn" onclick="openEditModal(${cat.id})">
                <i class="fas fa-edit"></i> Edit Tickers
            </button>
        `;
        grid.appendChild(card);
    });

    // Animate entries
    gsap.from(".category-card", {
        duration: 0.8,
        y: 30,
        opacity: 0,
        stagger: 0.1,
        ease: "power2.out"
    });
}

// Modal Logic
function openEditModal(id) {
    currentEditingId = id;
    const cat = portfolio.find(c => c.id === id);
    document.getElementById('modal-title').innerText = `Edit ${cat.name}`;
    tickerListTextarea.value = cat.tickers.join(', ');
    modal.style.display = 'flex';
}

closeModal.onclick = () => modal.style.display = 'none';
window.onclick = (e) => { if (e.target == modal) modal.style.display = 'none'; }

tickerForm.onsubmit = (e) => {
    e.preventDefault();
    const newTickers = tickerListTextarea.value.split(',').map(t => t.trim().toUpperCase()).filter(t => t);
    const catIndex = portfolio.findIndex(c => c.id === currentEditingId);
    if (catIndex !== -1) {
        portfolio[catIndex].tickers = newTickers;
        saveAndRefresh();
        modal.style.display = 'none';
    }
};

function saveAndRefresh() {
    localStorage.setItem('stellarPortfolio', JSON.stringify(portfolio));
    renderDashboard();
}

// Excel Parsing with SheetJS
excelInput.onchange = (e) => {
    const file = e.target.files[0];
    const reader = new FileReader();

    reader.onload = (event) => {
        const data = new Uint8Array(event.target.result);
        const workbook = XLSX.read(data, { type: 'array' });
        const firstSheet = workbook.Sheets[workbook.SheetNames[0]];
        const rows = XLSX.utils.sheet_to_json(firstSheet);

        // Expecting columns: Topic/Category, Ticker
        // We will map the excel data to our 7 IDs
        const newPortfolioData = JSON.parse(JSON.stringify(defaultPortfolio)); // Start with fresh structure

        rows.forEach(row => {
            const categoryName = row.Topic || row.Category;
            const ticker = row.Ticker;

            if (categoryName && ticker) {
                // Find matching category (case-insensitive)
                const cat = newPortfolioData.find(c =>
                    c.name.toLowerCase().includes(categoryName.trim().toLowerCase())
                );

                if (cat) {
                    if (!cat.tickers_reset) {
                        cat.tickers = []; // Clear defaults on first match
                        cat.tickers_reset = true;
                    }
                    cat.tickers.push(ticker.trim().toUpperCase());
                }
            }
        });

        portfolio = newPortfolioData;
        saveAndRefresh();
        alert("Portfolio synced with Excel!");
    };
    reader.readAsArrayBuffer(file);
};

// Initial Load
window.onload = renderDashboard;
