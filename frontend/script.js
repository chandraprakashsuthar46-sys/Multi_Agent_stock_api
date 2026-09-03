// ======================================================
// STOCKMIND AI - COMPLETE SCRIPT.JS
// ======================================================


// ======================================================
// DOM ELEMENTS
// ======================================================

const symbolInput = document.getElementById("symbol");
const analyzeButton = document.getElementById("analyzeBtn");
const loading = document.getElementById("loading");
const loadingText = document.getElementById("loadingText");
const errorBox = document.getElementById("error");
const results = document.getElementById("results");
const empty = document.getElementById("empty");


// ======================================================
// ANALYZE STOCK
// ======================================================

async function analyzeStock() {

    const symbol = symbolInput.value.trim().toUpperCase();

    if (!symbol) {
        showError("Please enter a stock symbol.");
        symbolInput.focus();
        return;
    }

    hideError();
    showLoading();
    hideResults();

    analyzeButton.disabled = true;
    analyzeButton.style.opacity = "0.7";
    analyzeButton.style.cursor = "wait";

    try {

        updateLoading("Connecting to AI orchestrator...");
        await sleep(350);

        updateLoading("Running Fundamental Agent...");
        await sleep(350);

        updateLoading("Running Technical Agent...");
        await sleep(350);

        updateLoading("Running Sentiment Agent...");
        await sleep(350);

        updateLoading("Running Risk Agent...");
        await sleep(350);

        updateLoading("Decision Agent is synthesizing results...");

        const response = await fetch(
            `/stock/${encodeURIComponent(symbol)}/analyze`
        );

        if (!response.ok) {

            let message = "Stock analysis failed.";

            try {
                const err = await response.json();
                message = err.detail || message;
            } catch {}

            throw new Error(message);
        }

        const data = await response.json();

        updateLoading("Building final AI report...");
        await sleep(400);

        displayResults(data);

        await loadStockMetrics(
            data.symbol || symbol
        );

        saveRecentSearch(symbol);

    } catch (error) {

        console.error(error);

        showError(
            "Unable to analyze stock: " +
            error.message
        );

    } finally {

        hideLoading();

        analyzeButton.disabled = false;
        analyzeButton.style.opacity = "1";
        analyzeButton.style.cursor = "pointer";
    }
}


// ======================================================
// DISPLAY RESULTS
// ======================================================

function displayResults(data) {

    results.style.display = "block";
    empty.style.display = "none";

    document.getElementById("stock-name").textContent =
        data.symbol || "-";

    document.getElementById("market-symbol").textContent =
        data.market_symbol || "-";

    const decision =
        data.final_decision || {};

    const agents =
        data.agent_data || {};

    // FUNDAMENTAL

    const fundamental =
        decision.fundamental_view || "NEUTRAL";

    const fundamentalEl =
        document.getElementById("fundamental-view");

    fundamentalEl.textContent = fundamental;

    setStatusClass(fundamentalEl, fundamental);

    document.getElementById("fundamental-reason").textContent =
        decision.fundamental_reason ||
        buildFundamentalReason(agents.fundamental);


    // TECHNICAL

    const technical =
        decision.technical_view || "NEUTRAL";

    const technicalEl =
        document.getElementById("technical-view");

    technicalEl.textContent = technical;

    setStatusClass(technicalEl, technical);

    document.getElementById("technical-reason").textContent =
        decision.technical_reason ||
        buildTechnicalReason(agents.technical);


    // SENTIMENT

    const sentiment =
        decision.news_view || "NEUTRAL";

    const sentimentEl =
        document.getElementById("news-view");

    sentimentEl.textContent = sentiment;

    setStatusClass(sentimentEl, sentiment);

    document.getElementById("news-reason").textContent =
        decision.news_reason ||
        "Sentiment analysis completed.";


    // RISK

    const risk =
        decision.risk_view || "MEDIUM";

    const riskEl =
        document.getElementById("risk-view");

    riskEl.textContent = risk;

    setStatusClass(riskEl, risk);

    document.getElementById("risk-reason").textContent =
        decision.risk_reason ||
        buildRiskReason(agents.risk);


    // OVERALL VIEW

    let overall =
        decision.overall_view ||
        decision.reasoning ||
        "No overall AI view available.";

    if (overall.length < 45 && decision.reasoning) {
        overall = decision.reasoning;
    }

    document.getElementById("overall-view").textContent =
        overall;


    // RECOMMENDATION

    const recommendation =
        decision.recommendation || "HOLD";

    const rec =
        document.getElementById("recommendation");

    rec.textContent = recommendation;

    setRecommendationColor(rec, recommendation);


    // CONFIDENCE

    let confidence =
        Number(decision.confidence || 0);

    confidence = Math.max(0, Math.min(100, confidence));

    document.getElementById("confidence").textContent =
        confidence + "%";

    const fill =
        document.getElementById("confidence-fill");

    fill.style.width = "0%";

    setTimeout(() => {
        fill.style.width = confidence + "%";
    }, 100);


    // REASONING

    document.getElementById("reasoning").textContent =
        decision.reasoning ||
        "No reasoning available.";


    // RISKS

    document.getElementById("important-risks").textContent =
        decision.important_risks ||
        "No major risks reported.";


    // HEADLINES

    displayHeadlines(agents.sentiment);


    // RAW DATA

    document.getElementById("raw-data").textContent =
        JSON.stringify(data, null, 2);


    setTimeout(() => {

        results.scrollIntoView({
            behavior: "smooth",
            block: "start"
        });

    }, 200);
}


// ======================================================
// LIVE STOCK METRICS
// ======================================================

async function loadStockMetrics(symbol) {

    try {

        const response = await fetch(
            `/stock/${encodeURIComponent(symbol)}`,
            {
                cache: "no-store"
            }
        );

        if (!response.ok) {
            throw new Error("Stock API failed");
        }

        const stock = await response.json();

        document.getElementById("current-price").textContent =
            formatRupee(stock.current_price);

        document.getElementById("open-price").textContent =
            formatRupee(stock.open);

        document.getElementById("high-price").textContent =
            formatRupee(stock.high);

        document.getElementById("low-price").textContent =
            formatRupee(stock.low);

        document.getElementById("volume").textContent =
            formatVolume(stock.volume);

    } catch (error) {

        console.error("Metrics:", error);
    }
}


// ======================================================
// HEADLINES
// ======================================================

function displayHeadlines(sentiment) {

    const container =
        document.getElementById("headlines");

    const count =
        document.getElementById("news-count");

    const headlines =
        sentiment?.headlines || [];

    count.textContent =
        headlines.length + " articles";

    container.innerHTML = "";

    if (!headlines.length) {

        container.innerHTML =
            "<p>No recent headlines available.</p>";

        return;
    }

    headlines.forEach((item, index) => {

        const div =
            document.createElement("div");

        div.className = "news-item";

        let title = "";
        let url = "";
        let source = "";

        if (typeof item === "string") {

            title = item;

        } else {

            title =
                item.title ||
                item.headline ||
                "Untitled";

            url =
                item.url ||
                item.link ||
                item.article_url ||
                "";

            source =
                item.source ||
                item.publisher ||
                "";
        }

        if (url) {

            div.innerHTML = `
                <a
                    href="${escapeAttribute(url)}"
                    target="_blank"
                    rel="noopener noreferrer"
                    class="news-link"
                >
                    <p>
                        <span class="news-number">
                            ${index + 1}
                        </span>
                        ${escapeHTML(title)}
                    </p>

                    ${source ? `
                        <span class="news-source">
                            ${escapeHTML(source)}
                        </span>
                    ` : ""}
                </a>
            `;

        } else {

            div.innerHTML = `
                <p>
                    <span class="news-number">
                        ${index + 1}
                    </span>
                    ${escapeHTML(title)}
                </p>

                <span class="news-source">
                    Source URL unavailable
                </span>
            `;
        }

        container.appendChild(div);
    });
}


// ======================================================
// RECENT SEARCHES
// ======================================================

function saveRecentSearch(symbol) {

    let recent =
        JSON.parse(
            localStorage.getItem("stockmind_recent") || "[]"
        );

    recent =
        recent.filter(item => item !== symbol);

    recent.unshift(symbol);

    recent = recent.slice(0, 6);

    localStorage.setItem(
        "stockmind_recent",
        JSON.stringify(recent)
    );

    displayRecentSearches();
}


function displayRecentSearches() {

    const container =
        document.getElementById("recent-searches");

    if (!container) return;

    const recent =
        JSON.parse(
            localStorage.getItem("stockmind_recent") || "[]"
        );

    container.innerHTML = "";

    if (!recent.length) {

        container.innerHTML =
            '<span class="no-recent">No recent searches</span>';

        return;
    }

    recent.forEach(symbol => {

        const btn =
            document.createElement("button");

        btn.className = "recent-stock";

        btn.textContent = symbol;

        btn.onclick = () => {

            symbolInput.value = symbol;

            analyzeStock();
        };

        container.appendChild(btn);
    });
}


// ======================================================
// SIDEBAR NAVIGATION
// ======================================================

const dashboardBtn =
    document.getElementById("dashboardBtn");

const agentsBtn =
    document.getElementById("agentsBtn");

const apiBtn =
    document.getElementById("apiBtn");


function activateSidebar(button) {

    document
        .querySelectorAll(".side-item")
        .forEach(item =>
            item.classList.remove("active")
        );

    button.classList.add("active");
}


dashboardBtn?.addEventListener("click", () => {

    activateSidebar(dashboardBtn);

    window.scrollTo({
        top: 0,
        behavior: "smooth"
    });

});


agentsBtn?.addEventListener("click", () => {

    activateSidebar(agentsBtn);

    document.querySelector(".flow")
        ?.scrollIntoView({
            behavior: "smooth",
            block: "center"
        });

});


apiBtn?.addEventListener("click", async () => {

    activateSidebar(apiBtn);

    try {

        const res =
            await fetch("/docs", {
                method: "GET"
            });

        if (res.ok) {

            alert(
                "API STATUS\n\nFastAPI: ONLINE\nYahoo Finance: CONNECTED\nGemini AI: ACTIVE"
            );

        } else {

            alert(
                "API is currently unavailable."
            );
        }

    } catch {

        alert(
            "Unable to connect with API."
        );
    }

});


// ======================================================
// AGENT CARD
// ======================================================

function toggleCard(card) {
    card.classList.toggle("open");
}


// ======================================================
// RAW DATA
// ======================================================

function toggleData() {

    const raw =
        document.getElementById("raw-data");

    const arrow =
        document.getElementById("data-arrow");

    raw.classList.toggle("show");

    arrow.textContent =
        raw.classList.contains("show")
            ? "⌃"
            : "⌄";
}


// ======================================================
// STATUS
// ======================================================

function setStatusClass(element, value) {

    element.className = "status";

    const v =
        String(value).toLowerCase();

    if (v.includes("positive") || v.includes("bullish")) {
        element.classList.add("positive");
    }

    else if (v.includes("negative") || v.includes("bearish")) {
        element.classList.add("negative");
    }

    else if (v.includes("buy")) {
        element.classList.add("buy");
    }

    else if (v.includes("sell")) {
        element.classList.add("sell");
    }

    else if (v.includes("hold")) {
        element.classList.add("hold");
    }

    else {
        element.classList.add("neutral");
    }
}


function setRecommendationColor(el, value) {

    const v =
        String(value).toUpperCase();

    if (v === "BUY") {
        el.style.color = "#16a34a";
    }

    else if (v === "SELL") {
        el.style.color = "#dc2626";
    }

    else {
        el.style.color = "#ca8a04";
    }
}


// ======================================================
// BUILD REASONS
// ======================================================

function buildFundamentalReason(data) {

    if (!data)
        return "Fundamental analysis completed.";

    return `Revenue: ${formatNumber(data.revenue)} | EPS: ${formatNumber(data.eps)} | P/E: ${formatNumber(data.pe_ratio)} | ROE: ${formatNumber(data.roe)}`;
}


function buildTechnicalReason(data) {

    if (!data)
        return "Technical analysis completed.";

    return `Trend: ${data.trend || "-"} | Signal: ${data.signal || "-"} | RSI: ${formatNumber(data.rsi_14)} | MACD: ${formatNumber(data.macd)}`;
}


function buildRiskReason(data) {

    if (!data)
        return "Risk analysis completed.";

    return `Volatility: ${formatNumber(data.volatility_percentage)}% | RSI: ${formatNumber(data.rsi)} | P/E: ${formatNumber(data.pe_ratio)}`;
}


// ======================================================
// HELPERS
// ======================================================

function formatRupee(value) {

    if (value === null || value === undefined)
        return "₹—";

    return "₹" +
        Number(value).toLocaleString("en-IN", {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        });
}


function formatVolume(value) {

    if (value === null || value === undefined)
        return "—";

    const n = Number(value);

    if (n >= 10000000)
        return (n / 10000000).toFixed(2) + " Cr";

    if (n >= 100000)
        return (n / 100000).toFixed(2) + " L";

    if (n >= 1000)
        return (n / 1000).toFixed(2) + " K";

    return n.toString();
}


function formatNumber(value) {

    if (value === null || value === undefined)
        return "-";

    return value;
}


function escapeHTML(text) {

    const div = document.createElement("div");

    div.textContent = String(text);

    return div.innerHTML;
}


function escapeAttribute(value) {

    return String(value)
        .replace(/&/g, "&amp;")
        .replace(/"/g, "&quot;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;");
}


function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}


function showLoading() {
    loading.style.display = "flex";
}


function hideLoading() {
    loading.style.display = "none";
}


function updateLoading(text) {
    loadingText.textContent = text;
}


function hideResults() {
    results.style.display = "none";
}


function showError(msg) {
    errorBox.textContent = msg;
    errorBox.style.display = "block";
}


function hideError() {
    errorBox.style.display = "none";
}


// ======================================================
// ENTER KEY
// ======================================================

symbolInput.addEventListener("keydown", event => {

    if (event.key === "Enter") {
        analyzeStock();
    }

});


// ======================================================
// INITIAL LOAD
// ======================================================

window.addEventListener("load", () => {

    symbolInput.value = "";

    displayRecentSearches();

});