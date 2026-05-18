const STORAGE_KEY = "stock-dashboard-v1-followed";
const SEARCH_HISTORY_KEY = "stock-dashboard-v1-recent-searches";
const DEFAULT_FOLLOWED = ["AAPL", "NVDA", "TSLA", "600519.SH"];

const symbols = [
  {
    symbol: "AAPL",
    name: "Apple",
    market: "US",
    last: 212.48,
    changePct: 1.34,
    changeAbs: 2.81,
    open: 210.22,
    high: 213.14,
    low: 209.8,
    prevClose: 209.67,
    volume: 68420012,
    turnover: 14530000000,
    bid: 212.45,
    ask: 212.49,
    volumeRatio: 1.42,
    volatilityPct: 1.59,
    sector: "Mega Cap Tech",
    trend: "up",
    spark: [42, 44, 45, 47, 48, 49, 52, 55, 57, 58, 60, 63],
  },
  {
    symbol: "NVDA",
    name: "NVIDIA",
    market: "US",
    last: 128.36,
    changePct: 2.76,
    changeAbs: 3.45,
    open: 125.6,
    high: 129.02,
    low: 124.98,
    prevClose: 124.91,
    volume: 118520441,
    turnover: 15110000000,
    bid: 128.35,
    ask: 128.38,
    volumeRatio: 1.88,
    volatilityPct: 3.24,
    sector: "Semiconductor",
    trend: "up",
    spark: [30, 31, 33, 36, 38, 42, 45, 49, 50, 53, 56, 58],
  },
  {
    symbol: "TSLA",
    name: "Tesla",
    market: "US",
    last: 171.24,
    changePct: -1.92,
    changeAbs: -3.35,
    open: 174.4,
    high: 175.12,
    low: 170.88,
    prevClose: 174.59,
    volume: 93210531,
    turnover: 15900000000,
    bid: 171.22,
    ask: 171.27,
    volumeRatio: 1.63,
    volatilityPct: 2.42,
    sector: "EV",
    trend: "down",
    spark: [65, 64, 63, 61, 60, 57, 56, 54, 52, 49, 47, 44],
  },
  {
    symbol: "PLTR",
    name: "Palantir",
    market: "US",
    last: 27.15,
    changePct: 4.68,
    changeAbs: 1.22,
    open: 26.12,
    high: 27.44,
    low: 25.98,
    prevClose: 25.93,
    volume: 74520311,
    turnover: 1980000000,
    bid: 27.14,
    ask: 27.17,
    volumeRatio: 2.41,
    volatilityPct: 4.02,
    sector: "AI Platform",
    trend: "up",
    spark: [26, 28, 29, 32, 36, 40, 45, 50, 53, 59, 62, 66],
  },
  {
    symbol: "600519.SH",
    name: "贵州茅台",
    market: "CN",
    last: 1712.0,
    changePct: 0.86,
    changeAbs: 14.6,
    open: 1698.0,
    high: 1718.5,
    low: 1692.8,
    prevClose: 1697.4,
    volume: 3184200,
    turnover: 5450000000,
    bid: 1711.8,
    ask: 1712.2,
    volumeRatio: 1.12,
    volatilityPct: 1.51,
    sector: "白酒",
    trend: "up",
    spark: [44, 45, 46, 46, 47, 49, 50, 53, 54, 54, 56, 57],
  },
  {
    symbol: "000858.SZ",
    name: "五粮液",
    market: "CN",
    last: 138.64,
    changePct: -0.72,
    changeAbs: -1.0,
    open: 139.5,
    high: 140.12,
    low: 138.22,
    prevClose: 139.64,
    volume: 12103211,
    turnover: 1680000000,
    bid: 138.63,
    ask: 138.66,
    volumeRatio: 0.94,
    volatilityPct: 1.36,
    sector: "白酒",
    trend: "down",
    spark: [56, 56, 55, 54, 53, 52, 50, 50, 49, 48, 47, 46],
  },
  {
    symbol: "300750.SZ",
    name: "宁德时代",
    market: "CN",
    last: 182.16,
    changePct: -2.14,
    changeAbs: -3.99,
    open: 185.6,
    high: 186.2,
    low: 181.9,
    prevClose: 186.15,
    volume: 25203410,
    turnover: 4610000000,
    bid: 182.14,
    ask: 182.18,
    volumeRatio: 1.82,
    volatilityPct: 3.31,
    sector: "新能源",
    trend: "down",
    spark: [62, 61, 59, 58, 56, 55, 53, 50, 49, 47, 45, 42],
  },
  {
    symbol: "688766.SH",
    name: "普冉股份",
    market: "CN",
    last: 96.8,
    changePct: 1.56,
    changeAbs: 1.49,
    open: 95.42,
    high: 97.36,
    low: 94.88,
    prevClose: 95.31,
    volume: 2684110,
    turnover: 259900000,
    bid: 96.77,
    ask: 96.83,
    volumeRatio: 1.37,
    volatilityPct: 2.61,
    sector: "芯片设计",
    trend: "up",
    spark: [42, 43, 45, 48, 49, 52, 54, 56, 58, 59, 61, 64],
  },
];

const stockCatalog = [
  { symbol: "AAPL", code: "AAPL", name: "Apple", market: "US", sector: "Mega Cap Tech", basePrice: 212.48, baseVolume: 68420012, trend: "up" },
  { symbol: "NVDA", code: "NVDA", name: "NVIDIA", market: "US", sector: "Semiconductor", basePrice: 128.36, baseVolume: 118520441, trend: "up" },
  { symbol: "TSLA", code: "TSLA", name: "Tesla", market: "US", sector: "EV", basePrice: 171.24, baseVolume: 93210531, trend: "down" },
  { symbol: "PLTR", code: "PLTR", name: "Palantir", market: "US", sector: "AI Platform", basePrice: 27.15, baseVolume: 74520311, trend: "up" },
  { symbol: "600519.SH", code: "600519", name: "贵州茅台", market: "CN", sector: "白酒", basePrice: 1712.0, baseVolume: 3184200, trend: "up" },
  { symbol: "000858.SZ", code: "000858", name: "五粮液", market: "CN", sector: "白酒", basePrice: 138.64, baseVolume: 12103211, trend: "down" },
  { symbol: "300750.SZ", code: "300750", name: "宁德时代", market: "CN", sector: "新能源", basePrice: 182.16, baseVolume: 25203410, trend: "down" },
  { symbol: "688766.SH", code: "688766", name: "普冉股份", market: "CN", sector: "芯片设计", basePrice: 96.8, baseVolume: 2684110, trend: "up" },
  { symbol: "688981.SH", code: "688981", name: "中芯国际", market: "CN", sector: "半导体制造", basePrice: 47.2, baseVolume: 62311840, trend: "up" },
  { symbol: "688111.SH", code: "688111", name: "金山办公", market: "CN", sector: "办公软件", basePrice: 286.5, baseVolume: 1524410, trend: "up" },
  { symbol: "603259.SH", code: "603259", name: "药明康德", market: "CN", sector: "CXO", basePrice: 51.6, baseVolume: 19842311, trend: "down" },
  { symbol: "601318.SH", code: "601318", name: "中国平安", market: "CN", sector: "保险", basePrice: 43.8, baseVolume: 48221360, trend: "neutral" },
  { symbol: "601127.SH", code: "601127", name: "赛力斯", market: "CN", sector: "智能汽车", basePrice: 89.6, baseVolume: 28511670, trend: "up" },
  { symbol: "002594.SZ", code: "002594", name: "比亚迪", market: "CN", sector: "新能源汽车", basePrice: 242.5, baseVolume: 18455430, trend: "up" },
  { symbol: "002415.SZ", code: "002415", name: "海康威视", market: "CN", sector: "安防", basePrice: 31.8, baseVolume: 22116320, trend: "neutral" },
];

const hermesModes = {
  normal: {
    label: "正常监控",
    riskBias: 0,
    summary: "常规盯盘，优先识别异动、放量和趋势反转。",
  },
  defensive: {
    label: "防守优先",
    riskBias: 6,
    summary: "降低容忍度，优先保住已有收益，提早提醒回撤风险。",
  },
  crash: {
    label: "崩坏守卫",
    riskBias: 12,
    summary: "市场急变时优先保护本金与利润，放大崩坏级提醒。",
  },
};

const workflowSteps = [
  "1. 搜索股票并加入关注池",
  "2. 查看实时状态与盘中风险",
  "3. Hermes 持续监控异动和急跌",
  "4. Hermes 输出快讯、排行和风险建议",
  "5. 用户按提醒保收益、降回撤、快响应",
];

const els = {
  symbolInput: document.getElementById("symbolInput"),
  searchSuggestions: document.getElementById("searchSuggestions"),
  searchBtn: document.getElementById("searchBtn"),
  followBtn: document.getElementById("followBtn"),
  unfollowBtn: document.getElementById("unfollowBtn"),
  resetBtn: document.getElementById("resetBtn"),
  marketScope: document.getElementById("marketScope"),
  hermesMode: document.getElementById("hermesMode"),
  watchlist: document.getElementById("watchlist"),
  systemStatus: document.getElementById("systemStatus"),
  recentSearches: document.getElementById("recentSearches"),
  workflowChecklist: document.getElementById("workflowChecklist"),
  overviewGrid: document.getElementById("overviewGrid"),
  portfolioGrid: document.getElementById("portfolioGrid"),
  portfolioRefreshStatus: document.getElementById("portfolioRefreshStatus"),
  selectedTitle: document.getElementById("selectedTitle"),
  marketStatus: document.getElementById("marketStatus"),
  lastPrice: document.getElementById("lastPrice"),
  priceBadge: document.getElementById("priceBadge"),
  quoteGrid: document.getElementById("quoteGrid"),
  sparkline: document.getElementById("sparkline"),
  intradaySummary: document.getElementById("intradaySummary"),
  signalLabel: document.getElementById("signalLabel"),
  analysisCards: document.getElementById("analysisCards"),
  priorityTable: document.getElementById("priorityTable"),
  newsFeed: document.getElementById("newsFeed"),
  alertCenter: document.getElementById("alertCenter"),
  klinePanel: document.getElementById("klinePanel"),
  positionPanel: document.getElementById("positionPanel"),
  decisionPanel: document.getElementById("decisionPanel"),
  riskChecklist: document.getElementById("riskChecklist"),
  strategyPanel: document.getElementById("strategyPanel"),
  hermesInput: document.getElementById("hermesInput"),
  hermesAskBtn: document.getElementById("hermesAskBtn"),
  hermesPresetBtn: document.getElementById("hermesPresetBtn"),
  hermesResponse: document.getElementById("hermesResponse"),
};

const state = {
  selectedSymbol: DEFAULT_FOLLOWED[0],
  marketScope: "mixed",
  hermesMode: "normal",
  streamTick: 0,
  lastUpdateAt: new Date(),
  followedSymbols: loadFollowed(),
  recentSearches: loadRecentSearches(),
  alertHistory: [],
  apiReady: false,
  searchSuggestions: [],
  searchHighlightIndex: -1,
  decisionState: null,
  decisionBySymbol: {},
  decisionLoading: {},
  portfolioLastRefreshedAt: null,
};

let streamTimer = null;
let searchTimer = null;

async function apiRequest(path) {
  const response = await fetch(path);
  if (!response.ok) {
    let message = `HTTP ${response.status}`;
    try {
      const payload = await response.json();
      message = payload.detail || payload.message || message;
    } catch {}
    throw new Error(message);
  }
  return response.json();
}

function loadFollowed() {
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return [...DEFAULT_FOLLOWED];
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed) || !parsed.length) return [...DEFAULT_FOLLOWED];
    return parsed;
  } catch {
    return [...DEFAULT_FOLLOWED];
  }
}

function saveFollowed() {
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(state.followedSymbols));
}

function loadRecentSearches() {
  try {
    const raw = window.localStorage.getItem(SEARCH_HISTORY_KEY);
    const parsed = raw ? JSON.parse(raw) : [];
    return Array.isArray(parsed) ? parsed.slice(0, 8) : [];
  } catch {
    return [];
  }
}

function saveRecentSearches() {
  window.localStorage.setItem(SEARCH_HISTORY_KEY, JSON.stringify(state.recentSearches.slice(0, 8)));
}

function hideSuggestions() {
  state.searchSuggestions = [];
  state.searchHighlightIndex = -1;
  els.searchSuggestions.innerHTML = "";
  els.searchSuggestions.classList.add("hidden");
}

function renderSuggestions(items) {
  state.searchSuggestions = items;
  state.searchHighlightIndex = items.length ? 0 : -1;
  if (!items.length) {
    hideSuggestions();
    return;
  }

  els.searchSuggestions.innerHTML = items.map((item, index) => `
    <button
      class="suggestion-item ${index === state.searchHighlightIndex ? "active" : ""}"
      type="button"
      data-suggestion-index="${index}"
    >
      <div>
        <div class="suggestion-code">${item.symbol}</div>
        <div class="suggestion-meta">${item.name}</div>
      </div>
      <div class="suggestion-market">${item.market}</div>
    </button>
  `).join("");
  els.searchSuggestions.classList.remove("hidden");
}

function updateSuggestionHighlight() {
  const items = els.searchSuggestions.querySelectorAll(".suggestion-item");
  items.forEach((item, index) => {
    item.classList.toggle("active", index === state.searchHighlightIndex);
  });
}

function formatNumber(value) {
  return new Intl.NumberFormat("en-US", { maximumFractionDigits: 2 }).format(value);
}

function formatCompact(value) {
  return new Intl.NumberFormat("en-US", { notation: "compact", maximumFractionDigits: 2 }).format(value);
}

function formatTime(date) {
  return new Intl.DateTimeFormat("zh-CN", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  }).format(date);
}

function classBySign(value) {
  if (value > 0) return "positive";
  if (value < 0) return "negative";
  return "neutral";
}

function bareSymbol(symbol) {
  return symbol.includes(".") ? symbol.split(".")[0] : symbol;
}

function inferCnSymbol(code) {
  if (!/^\d{6}$/.test(code)) return code;
  if (code.startsWith("6") || code.startsWith("9")) return `${code}.SH`;
  return `${code}.SZ`;
}

function normalizeSearchInput(raw) {
  const normalized = raw.trim().toUpperCase();
  if (/^\d{6}$/.test(normalized)) {
    return {
      raw: normalized,
      exactSymbol: inferCnSymbol(normalized),
      bareCode: normalized,
    };
  }
  if (/^\d{6}\.(SH|SZ)$/.test(normalized)) {
    return {
      raw: normalized,
      exactSymbol: normalized,
      bareCode: normalized.slice(0, 6),
    };
  }
  return {
    raw: normalized,
    exactSymbol: normalized,
    bareCode: normalized,
  };
}

function seededValue(seed) {
  let hash = 2166136261;
  for (const char of seed) {
    hash ^= char.charCodeAt(0);
    hash = Math.imul(hash, 16777619);
  }
  return (hash >>> 0) / 4294967295;
}

function sparklineFromSeed(seed, trend) {
  const base = 36 + Math.round(seededValue(`${seed}-base`) * 24);
  const direction = trend === "down" ? -1 : trend === "neutral" ? 0 : 1;
  const spark = [];
  let current = base;
  for (let index = 0; index < 12; index += 1) {
    const noise = Math.round((seededValue(`${seed}-spark-${index}`) - 0.5) * 6);
    current = Math.max(18, Math.min(98, current + noise + direction));
    spark.push(current);
  }
  return spark;
}

function createRecordFromCatalog(entry) {
  const trend = entry.trend === "neutral" ? (seededValue(`${entry.symbol}-trend`) > 0.5 ? "up" : "down") : entry.trend;
  const drift = (seededValue(`${entry.symbol}-change`) - 0.5) * 6;
  const changePct = Number((trend === "down" ? -Math.abs(drift) : trend === "up" ? Math.abs(drift) : drift).toFixed(2));
  const prevClose = Number(entry.basePrice.toFixed(2));
  const last = Number((prevClose * (1 + changePct / 100)).toFixed(2));
  const open = Number((prevClose * (1 + (seededValue(`${entry.symbol}-open`) - 0.5) * 0.02)).toFixed(2));
  const intradayHigh = Math.max(open, last) * (1 + 0.004 + seededValue(`${entry.symbol}-high`) * 0.02);
  const intradayLow = Math.min(open, last) * (1 - 0.004 - seededValue(`${entry.symbol}-low`) * 0.02);
  const volumeRatio = Number((0.82 + seededValue(`${entry.symbol}-vr`) * 1.9).toFixed(2));
  const volume = Math.round(entry.baseVolume * (0.8 + seededValue(`${entry.symbol}-vol`) * 0.9));
  const turnover = Math.round(volume * last);
  const spreadBps = entry.market === "US" ? 1.2 + seededValue(`${entry.symbol}-spread`) * 2 : 1 + seededValue(`${entry.symbol}-spread`) * 1.4;
  const spreadValue = last * (spreadBps / 10000);
  const bid = Number((last - spreadValue / 2).toFixed(2));
  const ask = Number((last + spreadValue / 2).toFixed(2));
  return {
    symbol: entry.symbol,
    name: entry.name,
    market: entry.market,
    last,
    changePct,
    changeAbs: Number((last - prevClose).toFixed(2)),
    open,
    high: Number(intradayHigh.toFixed(2)),
    low: Number(intradayLow.toFixed(2)),
    prevClose,
    volume,
    turnover,
    bid,
    ask,
    volumeRatio,
    volatilityPct: Number((1.1 + seededValue(`${entry.symbol}-volatility`) * 3.1).toFixed(2)),
    sector: entry.sector,
    trend,
    spark: sparklineFromSeed(entry.symbol, trend),
  };
}

function createRecordFromSearchResult(entry) {
  const catalogEntry = stockCatalog.find(item => item.symbol === entry.symbol);
  if (catalogEntry) {
    return createRecordFromCatalog(catalogEntry);
  }
  return {
    symbol: entry.symbol,
    name: entry.name,
    market: entry.market || "CN",
    last: 0,
    changePct: 0,
    changeAbs: 0,
    open: 0,
    high: 0,
    low: 0,
    prevClose: 0,
    volume: 0,
    turnover: 0,
    bid: 0,
    ask: 0,
    volumeRatio: 1,
    volatilityPct: 0,
    sector: entry.market === "US" ? "US" : "A股",
    trend: "neutral",
    spark: sparklineFromSeed(entry.symbol, "neutral"),
    provider: "catalog",
  };
}

function ensureRecordFromSearchResult(entry) {
  let record = findRecord(entry.symbol);
  if (!record) {
    record = createRecordFromSearchResult(entry);
    symbols.push(record);
  }
  record.name = entry.name || record.name;
  record.market = entry.market || record.market;
  return record;
}

function ensureRecordLoaded(symbolOrEntry) {
  const symbol = typeof symbolOrEntry === "string" ? symbolOrEntry : symbolOrEntry.symbol;
  const existing = findRecord(symbol);
  if (existing) return existing;

  const entry = typeof symbolOrEntry === "string"
    ? stockCatalog.find(item => item.symbol === symbol)
    : symbolOrEntry;
  if (!entry) return null;

  const record = createRecordFromCatalog(entry);
  symbols.push(record);
  return record;
}

function resolveSearchTarget(raw) {
  const query = normalizeSearchInput(raw);
  const loadedMatch = symbols.find(item => (
    item.symbol.toUpperCase() === query.exactSymbol ||
    bareSymbol(item.symbol).toUpperCase() === query.bareCode ||
    item.name.toUpperCase().includes(query.raw)
  ));
  if (loadedMatch) return loadedMatch;

  const catalogMatch = stockCatalog.find(item => (
    item.symbol.toUpperCase() === query.exactSymbol ||
    item.code.toUpperCase() === query.bareCode ||
    item.name.toUpperCase().includes(query.raw)
  ));
  if (catalogMatch) return ensureRecordLoaded(catalogMatch);

  return null;
}

async function fetchSearchSuggestions(raw) {
  const query = raw.trim();
  if (!query) {
    hideSuggestions();
    return;
  }

  try {
    const remote = await apiRequest(`/api/search?q=${encodeURIComponent(query)}&limit=8`);
    if (remote.matches?.length) {
      renderSuggestions(remote.matches);
      return;
    }
  } catch (error) {
    console.warn("remote suggestion unavailable", error);
  }

  const normalized = normalizeSearchInput(query);
  const localMatches = stockCatalog.filter(item => (
    item.symbol.toUpperCase() === normalized.exactSymbol ||
    item.code.toUpperCase().startsWith(normalized.bareCode) ||
    item.name.toUpperCase().includes(normalized.raw)
  )).slice(0, 8);
  renderSuggestions(localMatches);
}

function findRecord(symbol) {
  return symbols.find(item => item.symbol === symbol);
}

function updateRecordFromQuote(quote) {
  let record = findRecord(quote.symbol);
  if (!record) {
    record = {
      symbol: quote.symbol,
      name: quote.name,
      market: quote.market || "CN",
      last: quote.last_price,
      changePct: quote.change_pct,
      changeAbs: quote.change_abs,
      open: quote.open,
      high: quote.high,
      low: quote.low,
      prevClose: quote.prev_close,
      volume: quote.volume,
      turnover: quote.turnover,
      bid: quote.bid,
      ask: quote.ask,
      volumeRatio: quote.volume_ratio || 1,
      volatilityPct: 1.8,
      sector: "A股",
      trend: quote.change_pct >= 0 ? "up" : "down",
      spark: sparklineFromSeed(quote.symbol, quote.change_pct >= 0 ? "up" : "down"),
    };
    symbols.push(record);
  }

  record.name = quote.name || record.name;
  record.market = quote.market || record.market;
  record.last = Number(quote.last_price || record.last || 0);
  record.changePct = Number(quote.change_pct || 0);
  record.changeAbs = Number(quote.change_abs || 0);
  record.open = Number(quote.open || record.open || record.last || 0);
  record.high = Number(quote.high || record.high || record.last || 0);
  record.low = Number(quote.low || record.low || record.last || 0);
  record.prevClose = Number(quote.prev_close || record.prevClose || 0);
  record.volume = Number(quote.volume || record.volume || 0);
  record.turnover = Number(quote.turnover || record.turnover || 0);
  record.bid = Number(quote.bid || record.bid || record.last || 0);
  record.ask = Number(quote.ask || record.ask || record.last || 0);
  record.volumeRatio = Number(quote.volume_ratio || record.volumeRatio || 1);
  record.volatilityPct = Number(Math.max(0.8, Math.min(6, Math.abs(record.high - record.low) / (record.prevClose || record.last || 1) * 100)).toFixed(2));
  record.trend = record.changePct >= 0 ? "up" : "down";
  record.spark = [...record.spark.slice(1), Math.max(18, Math.min(98, (record.spark.at(-1) || 50) + (record.changePct >= 0 ? 2 : -2)))];
  record.provider = quote.provider || "tencent_quote";
  return record;
}

async function fetchLiveQuotes(symbolList) {
  if (!symbolList.length) return [];
  const payload = await apiRequest(`/api/quotes?symbols=${encodeURIComponent(symbolList.join(","))}`);
  const quotes = payload.quotes || [];
  quotes.forEach(updateRecordFromQuote);
  return quotes;
}

function currentRecord() {
  return findRecord(state.selectedSymbol) || symbols[0];
}

function getScopedSymbols() {
  return symbols.filter(item => {
    if (state.marketScope === "mixed") return true;
    return state.marketScope === "us" ? item.market === "US" : item.market === "CN";
  });
}

function getFollowedRecords() {
  const followed = state.followedSymbols.map(findRecord).filter(Boolean);
  return followed.filter(item => {
    if (state.marketScope === "mixed") return true;
    return state.marketScope === "us" ? item.market === "US" : item.market === "CN";
  });
}

function getLiveFollowedRecords() {
  return getFollowedRecords().filter(item => item.provider === "tencent_quote");
}

function ensureSelectionVisible() {
  const records = getFollowedRecords();
  if (!records.length) {
    const fallback = getScopedSymbols()[0] || symbols[0];
    state.selectedSymbol = fallback.symbol;
    return;
  }
  if (!records.some(item => item.symbol === state.selectedSymbol)) {
    state.selectedSymbol = records[0].symbol;
  }
}

function deriveSignal(record) {
  const spreadBps = ((record.ask - record.bid) / record.last) * 10000;
  const modeBias = hermesModes[state.hermesMode].riskBias;
  const momentum = Math.round(Math.max(0, Math.min(100, 50 + record.changePct * 10 + (record.volumeRatio - 1) * 12)));
  const liquidity = Math.round(Math.max(0, Math.min(100, 100 - spreadBps * 12 + record.volumeRatio * 5)));
  const volatility = Math.round(Math.max(0, Math.min(100, 100 - Math.abs(record.volatilityPct - 2.2) * 18 - modeBias)));
  const protection = Math.round(Math.max(0, Math.min(100, 58 + record.changePct * 12 + (record.volumeRatio - 1) * 14 - Math.max(record.volatilityPct - 3.1, 0) * 14 - Math.max(spreadBps - 3, 0) * 8 - modeBias)));

  let bias = "继续观察";
  if (protection >= 78) bias = "趋势确认";
  else if (protection >= 62) bias = "偏强跟踪";
  else if (protection <= 28) bias = "崩坏警戒";
  else if (protection <= 42) bias = "防守优先";

  let alertLevel = "low";
  if (protection <= 35 || record.changePct <= -3 || record.volatilityPct >= 4.2) alertLevel = "high";
  else if (protection <= 55 || spreadBps >= 4 || record.volumeRatio >= 1.8) alertLevel = "medium";

  return {
    spreadBps,
    momentum,
    liquidity,
    volatility,
    protection,
    bias,
    alertLevel,
  };
}

function priorityRecords() {
  return getLiveFollowedRecords()
    .map(record => ({ record, signal: deriveSignal(record) }))
    .sort((left, right) => {
      const leftRisk = (100 - left.signal.protection) + Math.max(0, -left.record.changePct * 8);
      const rightRisk = (100 - right.signal.protection) + Math.max(0, -right.record.changePct * 8);
      return rightRisk - leftRisk;
    });
}

function registerRecentSearch(symbol) {
  state.recentSearches = [symbol, ...state.recentSearches.filter(item => item !== symbol)].slice(0, 8);
  saveRecentSearches();
}

function pushAlert(item) {
  const id = `${item.title}|${item.detail}`;
  if (state.alertHistory[0]?.id === id) {
    state.alertHistory[0].time = formatTime(state.lastUpdateAt);
    return;
  }
  state.alertHistory.unshift({
    id,
    time: formatTime(state.lastUpdateAt),
    ...item,
  });
  state.alertHistory = state.alertHistory.slice(0, 12);
}

function marketPulse() {
  const scoped = getScopedSymbols().filter(item => item.provider === "tencent_quote");
  if (!scoped.length) {
    return { label: "等待真实行情", detail: "当前没有真实行情股票参与 Hermes 分析。", klass: "neutral" };
  }
  const negatives = scoped.filter(item => item.changePct < 0).length;
  const averageChange = scoped.reduce((sum, item) => sum + item.changePct, 0) / scoped.length;
  const crashCount = scoped.filter(item => item.changePct <= -2 || item.volatilityPct >= 3.8).length;

  if (crashCount >= Math.max(2, Math.ceil(scoped.length / 2)) || averageChange <= -1.4) {
    return { label: "紧急崩坏", detail: "大盘或观察池进入高压状态，Hermes 应优先保护利润与本金。", klass: "negative" };
  }
  if (negatives >= Math.ceil(scoped.length / 2) || averageChange <= -0.5) {
    return { label: "防守区间", detail: "下跌家数增多，优先关注回撤扩张和流动性恶化。", klass: "neutral" };
  }
  return { label: "可控状态", detail: "市场暂无系统性崩坏，但仍需盯住异动和放量拐点。", klass: "positive" };
}

function buildNewsFeed() {
  const records = priorityRecords();
  const pulse = marketPulse();
  const items = [
    {
      title: `Hermes 市场播报：${pulse.label}`,
      detail: pulse.detail,
      priority: pulse.klass === "negative" ? "high" : pulse.klass === "neutral" ? "medium" : "low",
    },
  ];

  records.slice(0, 3).forEach(({ record, signal }, index) => {
    let title = `优先级 ${index + 1} · ${record.symbol}`;
    let detail = `${record.name} 当前保护分 ${signal.protection}/100，状态为 ${signal.bias}。`;
    if (record.changePct <= -2) {
      title = `${record.symbol} 回撤扩张`;
      detail = `跌幅 ${record.changePct.toFixed(2)}%，Hermes 建议立即复核支撑位与仓位风险。`;
    } else if (record.changePct >= 2 && record.volumeRatio >= 1.5) {
      title = `${record.symbol} 放量拉升`;
      detail = `涨幅 ${record.changePct.toFixed(2)}%，量比 ${record.volumeRatio.toFixed(2)}，需要防止冲高回落。`;
    } else if (signal.spreadBps >= 4) {
      title = `${record.symbol} 流动性恶化`;
      detail = `点差约 ${signal.spreadBps.toFixed(2)} bps，执行滑点风险抬升。`;
    }

    items.push({
      title,
      detail,
      priority: signal.alertLevel,
    });
  });

  return items.slice(0, 4);
}

function strategyItems(record, signal) {
  const mode = hermesModes[state.hermesMode];
  return [
    {
      title: "急跌守卫",
      detail: `${record.symbol} 单日跌幅接近 -2% 到 -3% 时，Hermes 优先升级提醒并要求人工复核。`,
    },
    {
      title: "保收益优先",
      detail: `${mode.label} 下，保护分低于 ${state.hermesMode === "crash" ? "42" : "50"} 将优先触发防守建议。`,
    },
    {
      title: "放量异动筛查",
      detail: "量比放大但波动过热时，只提示关注，不直接当成机会确认。",
    },
    {
      title: "崩坏响应",
      detail: "若观察池半数以上进入高压状态，Hermes 将把市场态势切到紧急崩坏。 ",
    },
  ];
}

function renderWorkflow() {
  els.workflowChecklist.innerHTML = workflowSteps
    .map(item => `<div class="pipeline-item compact-item"><strong>${item}</strong></div>`)
    .join("");
}

function renderRecentSearches() {
  if (!state.recentSearches.length) {
    els.recentSearches.innerHTML = `<div class="provider-card"><strong>还没有搜索记录</strong><p>搜索过的股票会出现在这里，便于快速回看。</p></div>`;
    return;
  }

  els.recentSearches.innerHTML = state.recentSearches
    .map(symbol => `<button class="pill-button" data-recent-symbol="${symbol}" type="button">${symbol}</button>`)
    .join("");
}

function renderSystemStatus() {
  const mode = hermesModes[state.hermesMode];
  const pulse = marketPulse();
  const followed = getFollowedRecords();
  const liveCount = followed.filter(item => item.provider === "tencent_quote").length;
  els.systemStatus.innerHTML = `
    <p>当前档位：${mode.label}</p>
    <p>Hermes 目标：${mode.summary}</p>
    <p>市场态势：${pulse.label}</p>
    <p>关注数量：${followed.length}</p>
    <p>真实行情：${liveCount}/${followed.length || 0}</p>
    <p>随机波动：已关闭</p>
    <p>最近刷新：${formatTime(state.lastUpdateAt)}</p>
  `;
}

function renderWatchlist() {
  const records = getFollowedRecords();
  if (!records.length) {
    els.watchlist.innerHTML = `<div class="provider-card"><strong>当前范围内没有关注股</strong><p>先搜索股票，再点击“加入关注”。</p></div>`;
    return;
  }

  els.watchlist.innerHTML = records.map(item => {
    const signal = deriveSignal(item);
    const sourceLabel = item.provider === "tencent_quote" ? "真实" : "静态";
    return `
      <button class="watch-item ${item.symbol === state.selectedSymbol ? "active" : ""}" data-symbol="${item.symbol}" type="button">
        <div>
          <div class="watch-symbol">${item.symbol}</div>
          <div class="watch-meta">${item.name} · ${item.sector} · ${sourceLabel} · 保护分 ${signal.protection}</div>
        </div>
        <div class="watch-change ${classBySign(item.changePct)}">${item.changePct > 0 ? "+" : ""}${item.changePct.toFixed(2)}%</div>
      </button>
    `;
  }).join("");
}

function renderOverview() {
  const scoped = getScopedSymbols().filter(item => item.provider === "tencent_quote");
  const priorities = priorityRecords();
  const pulse = marketPulse();
  if (!scoped.length) {
    els.overviewGrid.innerHTML = `
      <article class="overview-card neutral">
        <p class="meta-label">数据状态</p>
        <h3>等待真实行情</h3>
        <p class="muted">当前没有真实行情股票参与 Hermes 市场总览和风险排行。</p>
      </article>
    `;
    return;
  }
  const bestMomentum = [...scoped].sort((left, right) => deriveSignal(right).momentum - deriveSignal(left).momentum)[0];
  const danger = priorities[0];
  const breadth = scoped.filter(item => item.changePct > 0).length;

  const cards = [
    {
      label: "市场态势",
      value: pulse.label,
      note: pulse.detail,
      klass: pulse.klass,
    },
    {
      label: "上涨家数",
      value: `${breadth}/${scoped.length}`,
      note: `平均涨跌幅 ${(
        scoped.reduce((sum, item) => sum + item.changePct, 0) / scoped.length
      ).toFixed(2)}%`,
      klass: breadth >= Math.ceil(scoped.length / 2) ? "positive" : "negative",
    },
    {
      label: "当前最危险",
      value: danger ? danger.record.symbol : "-",
      note: danger ? `保护分 ${danger.signal.protection} · ${danger.signal.bias}` : "暂无",
      klass: danger && danger.signal.protection <= 42 ? "negative" : "neutral",
    },
    {
      label: "最强关注股",
      value: bestMomentum ? bestMomentum.symbol : "-",
      note: bestMomentum ? `${bestMomentum.name} · 涨跌幅 ${bestMomentum.changePct.toFixed(2)}%` : "暂无",
      klass: bestMomentum && bestMomentum.changePct > 0 ? "positive" : "neutral",
    },
  ];

  els.overviewGrid.innerHTML = cards.map(card => `
    <article class="overview-card ${card.klass || ""}">
      <p class="meta-label">${card.label}</p>
      <h3>${card.value}</h3>
      <p class="muted">${card.note}</p>
    </article>
  `).join("");
}

function renderMarketStatus(record, signal) {
  const pulse = marketPulse();
  const pills = [
    `代码 ${record.symbol}`,
    `市场 ${record.market}`,
    `Hermes ${signal.bias}`,
    `保护分 ${signal.protection}`,
    `市场态势 ${pulse.label}`,
  ];
  els.marketStatus.innerHTML = pills.map(item => `<div class="status-pill">${item}</div>`).join("");
}

function renderQuote(record, signal) {
  els.selectedTitle.textContent = `${record.symbol} · ${record.name}`;
  els.lastPrice.textContent = formatNumber(record.last);
  els.priceBadge.className = `price-badge ${classBySign(record.changePct)}`;
  els.priceBadge.textContent = `${record.changePct > 0 ? "+" : ""}${record.changePct.toFixed(2)}%`;
  const dataSource = record.provider === "tencent_quote" ? "真实行情" : "静态样本";

  const metrics = [
    ["涨跌额", `${record.changeAbs > 0 ? "+" : ""}${formatNumber(record.changeAbs)}`],
    ["开盘 / 昨收", `${formatNumber(record.open)} / ${formatNumber(record.prevClose)}`],
    ["最高 / 最低", `${formatNumber(record.high)} / ${formatNumber(record.low)}`],
    ["量比", record.volumeRatio.toFixed(2)],
    ["成交量", formatCompact(record.volume)],
    ["成交额", formatCompact(record.turnover)],
    ["买一 / 卖一", `${formatNumber(record.bid)} / ${formatNumber(record.ask)}`],
    ["点差", `${signal.spreadBps.toFixed(2)} bps`],
    ["数据源", dataSource],
    ["板块", record.sector],
  ];

  els.quoteGrid.innerHTML = metrics.map(([label, value]) => `
    <div class="metric-card">
      <span class="meta-label">${label}</span>
      <strong>${value}</strong>
    </div>
  `).join("");

  els.signalLabel.className = `signal-chip ${classBySign(signal.protection - 50)}`;
  els.signalLabel.textContent = `${signal.bias} · ${signal.protection}`;
}

function renderSparkline(record, signal) {
  const highest = Math.max(...record.spark);
  const threshold = Math.max(...record.spark) + Math.min(...record.spark);
  els.sparkline.innerHTML = record.spark.map(value => {
    const normalized = Math.max(16, Math.round((value / highest) * 100));
    const klass = value * 2 < threshold ? "negative" : "";
    return `<div class="spark-bar ${klass}" style="height:${normalized}%"></div>`;
  }).join("");

  els.intradaySummary.textContent = `波动 ${record.volatilityPct.toFixed(2)}%，量比 ${record.volumeRatio.toFixed(2)}，点差 ${signal.spreadBps.toFixed(2)} bps，Hermes 保护分 ${signal.protection}/100。`;
}

function renderAnalysis(record, signal) {
  const cards = [
    { title: "趋势确认", score: signal.momentum, note: "看涨跌幅、量比和趋势延续强度。" },
    { title: "流动性", score: signal.liquidity, note: "看点差、成交确认和执行滑点风险。" },
    { title: "波动稳定度", score: signal.volatility, note: "区分健康波动与噪音或崩坏式波动。" },
    { title: "收益保护", score: signal.protection, note: signal.bias },
  ];

  els.analysisCards.innerHTML = cards.map(card => `
    <div class="analysis-card">
      <h4>${card.title}</h4>
      <div class="analysis-score ${classBySign(card.score - 50)}">${card.score}</div>
      <p class="muted">${card.note}</p>
    </div>
  `).join("");
}

function renderPriorityTable() {
  const rows = priorityRecords();
  if (!rows.length) {
    els.priorityTable.innerHTML = `<div class="provider-card"><strong>暂无真实行情排行</strong><p>只有真实行情股票才会进入 Hermes 风险排行与投资判断。</p></div>`;
    return;
  }
  els.priorityTable.innerHTML = `
    <table>
      <thead>
        <tr>
          <th>优先级</th>
          <th>代码</th>
          <th>保护分</th>
          <th>涨跌幅</th>
          <th>量比</th>
          <th>状态</th>
        </tr>
      </thead>
      <tbody>
        ${rows.map(({ record, signal }, index) => `
          <tr data-priority-symbol="${record.symbol}" class="priority-row">
            <td>${index + 1}</td>
            <td>${record.symbol}</td>
            <td class="${classBySign(signal.protection - 50)}">${signal.protection}</td>
            <td class="${classBySign(record.changePct)}">${record.changePct > 0 ? "+" : ""}${record.changePct.toFixed(2)}%</td>
            <td>${record.volumeRatio.toFixed(2)}</td>
            <td>${signal.bias}</td>
          </tr>
        `).join("")}
      </tbody>
    </table>
  `;
}

function renderNewsFeed() {
  const items = buildNewsFeed();
  items.forEach(pushAlert);
  els.newsFeed.innerHTML = items.map(item => `
    <div class="alert-item priority-${item.priority}">
      <strong class="alert-title">${item.title}</strong>
      <p>${item.detail}</p>
      <div class="alert-meta">Hermes 优先级：${item.priority.toUpperCase()}</div>
    </div>
  `).join("");
}

function renderAlertCenter() {
  if (!state.alertHistory.length) {
    els.alertCenter.innerHTML = `<div class="provider-card"><strong>告警中心为空</strong><p>Hermes 在检测到风险变化后会把事件写到这里。</p></div>`;
    return;
  }

  els.alertCenter.innerHTML = state.alertHistory.map(item => `
    <div class="alert-item priority-${item.priority}">
      <strong class="alert-title">${item.title}</strong>
      <p>${item.detail}</p>
      <div class="alert-meta">${item.time} · ${item.priority.toUpperCase()}</div>
    </div>
  `).join("");
}

function renderRiskChecklist(record, signal) {
  const items = [
    ["回撤风险", record.changePct <= -2 ? "立即复核" : "暂时可控"],
    ["流动性", signal.spreadBps >= 4 ? "点差恶化" : "正常"],
    ["波动状态", record.volatilityPct >= 3.8 ? "过热" : "正常"],
    ["成交确认", record.volumeRatio < 0.9 ? "不足" : "有效"],
    ["Hermes 建议", signal.protection <= 42 ? "防守优先" : "继续跟踪"],
  ];

  els.riskChecklist.innerHTML = items.map(([label, value]) => `
    <div class="risk-item">
      <span>${label}</span>
      <strong>${value}</strong>
    </div>
  `).join("");
}

function renderStrategyPanel(record, signal) {
  els.strategyPanel.innerHTML = strategyItems(record, signal).map(item => `
    <div class="provider-card">
      <strong>${item.title}</strong>
      <p>${item.detail}</p>
    </div>
  `).join("");
}

function toFiniteNumber(value) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function formatShortDate(value) {
  const raw = String(value || "");
  const match = raw.match(/^(\d{4})-(\d{2})-(\d{2})/);
  if (match) {
    return `${match[2]}-${match[3]}`;
  }
  return raw || "-";
}

function classByTechnicalScore(score) {
  if (score >= 56) return "positive";
  if (score <= 34) return "negative";
  return "neutral";
}

function isLiveCnRecord(record) {
  return Boolean(record && record.market === "CN" && record.provider === "tencent_quote");
}

function isCnRecord(record) {
  return Boolean(record && record.market === "CN");
}

function buildSvgPath(points) {
  if (points.length < 2) return "";
  return points.map((point, index) => `${index === 0 ? "M" : "L"}${point.x.toFixed(2)} ${point.y.toFixed(2)}`).join(" ");
}

function buildMovingAveragePath(bars, window, xForIndex, yForPrice) {
  const points = [];
  const closes = [];
  bars.forEach((bar, index) => {
    closes.push(bar.close);
    if (closes.length < window) return;
    const average = closes.slice(-window).reduce((sum, value) => sum + value, 0) / window;
    points.push({ x: xForIndex(index), y: yForPrice(average) });
  });
  return buildSvgPath(points);
}

function renderKlineChart(kline) {
  const bars = (kline?.bars || []).map(bar => {
    const open = toFiniteNumber(bar.open);
    const close = toFiniteNumber(bar.close);
    const high = toFiniteNumber(bar.high);
    const low = toFiniteNumber(bar.low);
    const volume = Math.max(0, toFiniteNumber(bar.volume) ?? 0);
    if (open === null || close === null || high === null || low === null) {
      return null;
    }
    return { ...bar, open, close, high, low, volume };
  }).filter(Boolean);

  if (!bars.length) {
    return `
      <div class="kline-chart-shell">
        <p class="provider-meta">当前 K 线结果里没有可绘制的 bars 数据。</p>
      </div>
    `;
  }

  const width = 760;
  const height = 320;
  const paddingX = 18;
  const drawableWidth = width - paddingX * 2;
  const priceTop = 16;
  const priceHeight = 188;
  const volumeTop = 226;
  const volumeHeight = 52;
  const labelY = 304;

  const highs = bars.map(bar => bar.high);
  const lows = bars.map(bar => bar.low);
  const maxPrice = Math.max(...highs);
  const minPrice = Math.min(...lows);
  const rawSpread = Math.max(maxPrice - minPrice, maxPrice * 0.02, 1);
  const maxScale = maxPrice + rawSpread * 0.08;
  const minScale = Math.max(0, minPrice - rawSpread * 0.08);
  const scaleSpan = Math.max(maxScale - minScale, 1);
  const maxVolume = Math.max(...bars.map(bar => bar.volume), 1);
  const candleGap = drawableWidth / bars.length;
  const candleWidth = Math.max(4, Math.min(10, candleGap * 0.64));
  const xForIndex = index => paddingX + candleGap * index + candleGap / 2;
  const yForPrice = price => priceTop + ((maxScale - price) / scaleSpan) * priceHeight;

  const gridFractions = [0, 0.25, 0.5, 0.75, 1];
  const grid = gridFractions.map(fraction => {
    const y = priceTop + priceHeight * fraction;
    const price = maxScale - scaleSpan * fraction;
    return `
      <line class="kline-grid" x1="${paddingX}" y1="${y.toFixed(2)}" x2="${(width - paddingX).toFixed(2)}" y2="${y.toFixed(2)}"></line>
      <text class="kline-axis-text" x="${(width - 4).toFixed(2)}" y="${(y - 3).toFixed(2)}" text-anchor="end">${formatNumber(price)}</text>
    `;
  }).join("");

  const candles = bars.map((bar, index) => {
    const x = xForIndex(index);
    const direction = bar.close >= bar.open ? "up" : "down";
    const wickTop = yForPrice(bar.high);
    const wickBottom = yForPrice(bar.low);
    const bodyTop = yForPrice(Math.max(bar.open, bar.close));
    const rawBodyHeight = Math.abs(yForPrice(bar.open) - yForPrice(bar.close));
    const bodyHeight = Math.max(2, rawBodyHeight);
    const bodyY = rawBodyHeight < 2 ? bodyTop - 1 : bodyTop;
    const volumeHeightPx = Math.max(1.5, (bar.volume / maxVolume) * volumeHeight);
    const volumeY = volumeTop + volumeHeight - volumeHeightPx;
    return `
      <line class="kline-wick ${direction}" x1="${x.toFixed(2)}" y1="${wickTop.toFixed(2)}" x2="${x.toFixed(2)}" y2="${wickBottom.toFixed(2)}"></line>
      <rect class="kline-body ${direction}" x="${(x - candleWidth / 2).toFixed(2)}" y="${bodyY.toFixed(2)}" width="${candleWidth.toFixed(2)}" height="${bodyHeight.toFixed(2)}" rx="1.5"></rect>
      <rect class="kline-volume ${direction}" x="${(x - candleWidth / 2).toFixed(2)}" y="${volumeY.toFixed(2)}" width="${candleWidth.toFixed(2)}" height="${volumeHeightPx.toFixed(2)}" rx="1.5"></rect>
    `;
  }).join("");

  const ma5Path = buildMovingAveragePath(bars, 5, xForIndex, yForPrice);
  const ma20Path = buildMovingAveragePath(bars, 20, xForIndex, yForPrice);
  const startDate = formatShortDate(bars[0].date);
  const endDate = formatShortDate(bars.at(-1)?.date);

  return `
    <div class="kline-chart-shell">
      <div class="kline-chart-header">
        <div class="kline-legend">
          <span class="kline-legend-item"><span class="legend-dot up"></span>阳线</span>
          <span class="kline-legend-item"><span class="legend-dot down"></span>阴线</span>
          <span class="kline-legend-item"><span class="legend-dot ma5"></span>MA5</span>
          <span class="kline-legend-item"><span class="legend-dot ma20"></span>MA20</span>
        </div>
        <div class="provider-meta">${startDate} 至 ${endDate} · ${bars.length} 根</div>
      </div>
      <svg class="kline-svg" viewBox="0 0 ${width} ${height}" role="img" aria-label="股票 K 线图">
        ${grid}
        <line class="kline-volume-axis" x1="${paddingX}" y1="${(volumeTop - 8).toFixed(2)}" x2="${(width - paddingX).toFixed(2)}" y2="${(volumeTop - 8).toFixed(2)}"></line>
        ${candles}
        ${ma5Path ? `<path class="kline-ma-line ma5" d="${ma5Path}"></path>` : ""}
        ${ma20Path ? `<path class="kline-ma-line ma20" d="${ma20Path}"></path>` : ""}
        <text class="kline-axis-text" x="${paddingX}" y="${labelY}">${startDate}</text>
        <text class="kline-axis-text" x="${(width - paddingX).toFixed(2)}" y="${labelY}" text-anchor="end">${endDate}</text>
        <text class="kline-axis-text" x="${paddingX}" y="${(volumeTop - 12).toFixed(2)}">VOL</text>
      </svg>
    </div>
  `;
}

function renderKlineSummary(kline, klineError) {
  if (!kline) {
    return `
      <div class="portfolio-kline-empty">
        <strong>暂无K线</strong>
        <p>真实 A 股行情刷新后加载。</p>
      </div>
    `;
  }
  if (!kline.bars?.length) {
    return `
      <div class="portfolio-kline-empty">
        <strong>${kline.trend_label || "暂无K线数据"}</strong>
        <p>${kline.volume_price_summary || "当前没有可绘制的 K 线数据。"}</p>
        ${klineError ? `<p class="provider-meta danger-text">${klineError}</p>` : ""}
      </div>
    `;
  }
  const latestBar = kline.latest_bar || kline.bars.at(-1) || {};
  return `
    ${renderKlineChart(kline)}
    <div class="portfolio-kline-stats">
      <span>最新 ${formatShortDate(latestBar.date)}</span>
      <span>技术分 ${kline.technical_score ?? "-"}</span>
      <span>支撑 ${kline.support_price ?? "-"}</span>
      <span>压力 ${kline.resistance_price ?? "-"}</span>
    </div>
  `;
}

function renderPortfolio() {
  const records = getFollowedRecords();
  if (!records.length) {
    els.portfolioGrid.innerHTML = `<div class="provider-card"><strong>暂无关注股</strong><p>搜索股票并加入关注池后，这里会显示每只股票的行情、K 线和分析。</p></div>`;
    els.portfolioRefreshStatus.textContent = "无关注股";
    return;
  }

  const cnCount = records.filter(isCnRecord).length;
  const liveCount = records.filter(isLiveCnRecord).length;
  els.portfolioRefreshStatus.textContent = `${liveCount} 真实行情 · ${cnCount} A股可查K线 · ${formatTime(state.lastUpdateAt)}`;

  els.portfolioGrid.innerHTML = records.map(record => {
    const signal = deriveSignal(record);
    const decisionState = state.decisionBySymbol[record.symbol];
    const loading = state.decisionLoading[record.symbol];
    const dataSource = record.provider === "tencent_quote" ? "真实行情" : "静态样本";
    const decision = decisionState?.decision;
    const kline = decisionState?.kline;
    const klineError = decisionState?.kline_error;
    const selected = record.symbol === state.selectedSymbol ? "active" : "";
    const canLoadKline = isCnRecord(record);
    const live = isLiveCnRecord(record);
    const quoteError = decisionState?.quote_error;
    const analysisText = decision
      ? `${decision.decision} · ${(decision.reasons || []).slice(0, 2).join("；") || "暂无理由"}`
      : live
        ? loading ? "正在加载 K 线与投资判断..." : "等待分析刷新"
        : "静态或非 A 股样本暂不生成真实 K 线分析";

    return `
      <article class="portfolio-card ${selected}" data-portfolio-symbol="${record.symbol}">
        <div class="portfolio-card-head">
          <div>
            <p class="meta-label">${dataSource}</p>
            <h4>${record.symbol} · ${record.name}</h4>
            <p class="provider-meta">${record.sector} · ${record.market}</p>
          </div>
          <div class="portfolio-price-block">
            <strong>${formatNumber(record.last)}</strong>
            <span class="${classBySign(record.changePct)}">${record.changePct > 0 ? "+" : ""}${record.changePct.toFixed(2)}%</span>
          </div>
        </div>
        <div class="portfolio-metrics">
          <div><span>保护分</span><strong class="${classBySign(signal.protection - 50)}">${signal.protection}</strong></div>
          <div><span>状态</span><strong>${signal.bias}</strong></div>
          <div><span>量比</span><strong>${record.volumeRatio.toFixed(2)}</strong></div>
          <div><span>点差</span><strong>${signal.spreadBps.toFixed(2)} bps</strong></div>
          <div><span>成交额</span><strong>${formatCompact(record.turnover)}</strong></div>
          <div><span>波动</span><strong>${record.volatilityPct.toFixed(2)}%</strong></div>
        </div>
        <div class="portfolio-kline">
          ${canLoadKline ? renderKlineSummary(kline, klineError) : `<div class="portfolio-kline-empty"><strong>暂无真实K线</strong><p>当前标的是 ${dataSource}，需要接入对应市场历史行情后才能绘制。</p></div>`}
        </div>
        <div class="portfolio-analysis">
          <strong>Hermes 分析</strong>
          <p>${analysisText}</p>
          ${quoteError && kline?.bars?.length ? `<p class="provider-meta danger-text">实时行情暂不可用，已先显示历史K线：${quoteError}</p>` : ""}
          ${decision ? `<p class="provider-meta">浮盈亏 ${decision.pnl_pct ?? "-"}% · 成本 ${decision.avg_cost ?? "-"} · 止损 ${decision.stop_loss ?? "-"} · 目标 ${decision.target_price ?? "-"}</p>` : ""}
        </div>
      </article>
    `;
  }).join("");
}

function renderKlinePanel() {
  const kline = state.decisionState?.kline;
  const klineError = state.decisionState?.kline_error;
  if (!kline) {
    els.klinePanel.innerHTML = `<div class="provider-card"><strong>暂无K线分析</strong><p>选中一只真实行情 A 股后，系统会加载 K 线与量价分析。</p></div>`;
    return;
  }
  if (!kline.bars?.length) {
    els.klinePanel.innerHTML = `
      <div class="provider-card kline-card">
        <strong>${kline.trend_label || "暂无K线数据"}</strong>
        <p>${kline.volume_price_summary || "当前没有可用于绘图的 K 线数据。"}</p>
        ${klineError ? `<p class="provider-meta danger-text">${klineError}</p>` : ""}
        <p class="provider-meta">如果这里提示获取失败，通常是历史行情数据源暂时不可达；已有缓存时系统会自动回退到缓存。</p>
      </div>
    `;
    return;
  }
  const ma = kline.ma || {};
  const vol = kline.volume_ma || {};
  const latestBar = kline.latest_bar || kline.bars?.at(-1) || {};
  const latestOpen = toFiniteNumber(latestBar.open);
  const latestClose = toFiniteNumber(latestBar.close);
  const latestHigh = toFiniteNumber(latestBar.high);
  const latestLow = toFiniteNumber(latestBar.low);
  const latestVolume = toFiniteNumber(latestBar.volume);
  const technicalScore = Number.isFinite(Number(kline.technical_score)) ? Number(kline.technical_score) : 0;
  els.klinePanel.innerHTML = `
    <div class="provider-card kline-card">
      <div class="kline-header">
        <div>
          <strong>${kline.trend_label}</strong>
          <p>${kline.volume_price_summary}</p>
        </div>
        <div class="kline-badges">
          <span class="signal-chip ${classByTechnicalScore(technicalScore)}">技术分 ${technicalScore}</span>
          <span class="status-pill">${kline.technical_bias || "暂无判断"}</span>
        </div>
      </div>
      ${renderKlineChart(kline)}
      <div class="kline-meta-grid">
        <div class="metric-card kline-metric">
          <span>最新交易日</span>
          <strong>${formatShortDate(latestBar.date)}</strong>
        </div>
        <div class="metric-card kline-metric">
          <span>开 / 收</span>
          <strong>${latestOpen !== null ? formatNumber(latestOpen) : "-"} / ${latestClose !== null ? formatNumber(latestClose) : "-"}</strong>
        </div>
        <div class="metric-card kline-metric">
          <span>高 / 低</span>
          <strong>${latestHigh !== null ? formatNumber(latestHigh) : "-"} / ${latestLow !== null ? formatNumber(latestLow) : "-"}</strong>
        </div>
        <div class="metric-card kline-metric">
          <span>成交量</span>
          <strong>${latestVolume !== null ? formatCompact(latestVolume) : "-"}</strong>
        </div>
      </div>
      <p class="provider-meta">MA5 ${ma.ma5 ?? "-"} · MA10 ${ma.ma10 ?? "-"} · MA20 ${ma.ma20 ?? "-"} · MA60 ${ma.ma60 ?? "-"}</p>
      <p class="provider-meta">量能 MA5 ${vol.ma5 ?? "-"} · MA20 ${vol.ma20 ?? "-"} · 支撑 ${kline.support_price ?? "-"} · 压力 ${kline.resistance_price ?? "-"}</p>
      ${klineError ? `<p class="provider-meta danger-text">${klineError}</p>` : ""}
    </div>
  `;
}

function renderPositionPanel() {
  const position = state.decisionState?.position;
  if (!position) {
    els.positionPanel.innerHTML = `<div class="provider-card"><strong>暂无持仓逻辑</strong><p>后续可通过 /api/positions 写入仓位、成本、止损位、目标位和买入逻辑。</p></div>`;
    return;
  }
  els.positionPanel.innerHTML = `
    <div class="provider-card">
      <strong>${position.symbol}</strong>
      <p>仓位 ${position.quantity ?? "-"} · 成本 ${position.avg_cost ?? "-"} · 止损 ${position.stop_loss ?? "-"} · 目标 ${position.target_price ?? "-"}</p>
      <p class="provider-meta">周期：${position.horizon || "-"} · 逻辑：${position.thesis || "-"}</p>
    </div>
  `;
}

function renderDecisionPanel() {
  const decision = state.decisionState?.decision;
  if (!decision) {
    els.decisionPanel.innerHTML = `<div class="provider-card"><strong>暂无投资判断</strong><p>只有真实行情股票会生成继续持有 / 观察 / 减仓 / 卖出的判断。</p></div>`;
    return;
  }
  els.decisionPanel.innerHTML = `
    <div class="provider-card">
      <strong>${decision.decision}</strong>
      <p>${(decision.reasons || []).join("；") || "暂无理由"}</p>
      <p class="provider-meta">浮盈亏 ${decision.pnl_pct ?? "-"}% · 成本 ${decision.avg_cost ?? "-"} · 止损 ${decision.stop_loss ?? "-"} · 目标 ${decision.target_price ?? "-"}</p>
    </div>
  `;
}

function hermesReply(question) {
  const current = currentRecord();
  const currentSignal = deriveSignal(current);
  const priorities = priorityRecords();
  const top = priorities[0];
  const pulse = marketPulse();
  const lower = question.trim().toLowerCase();

  if (!question.trim()) {
    return `Hermes 当前结论：${current.symbol} 保护分 ${currentSignal.protection}/100，市场态势为 ${pulse.label}。`;
  }

  if (lower.includes("危险") || lower.includes("崩") || lower.includes("风险")) {
    return `当前最需要先看的是 ${top.record.symbol}，保护分 ${top.signal.protection}/100，状态 ${top.signal.bias}。Hermes 判断市场为 ${pulse.label}，建议优先处理高回撤和流动性恶化标的。`;
  }

  if (lower.includes("为什么") || lower.includes("原因")) {
    return `${current.symbol} 当前被 Hermes 标记为“${currentSignal.bias}”，主要因为涨跌幅 ${current.changePct.toFixed(2)}%、量比 ${current.volumeRatio.toFixed(2)}、点差 ${currentSignal.spreadBps.toFixed(2)} bps、波动 ${current.volatilityPct.toFixed(2)}%。`;
  }

  if (lower.includes("关注") || lower.includes("观察")) {
    return `当前关注池共 ${getFollowedRecords().length} 只，优先级前二是 ${priorities.slice(0, 2).map(item => item.record.symbol).join("、")}。建议先看保护分最低的标的。`;
  }

  return `Hermes 回应：当前聚焦 ${current.symbol}，保护分 ${currentSignal.protection}/100，信号为 ${currentSignal.bias}。如果你要保收益，先检查回撤风险、点差和量比是否同步恶化。`;
}

function renderHermesResponse(message) {
  els.hermesResponse.innerHTML = `
    <p class="response-tag">Hermes</p>
    <p>${message}</p>
  `;
}

function renderSelected() {
  const record = currentRecord();
  state.decisionState = state.decisionBySymbol[record.symbol] || null;
  const signal = deriveSignal(record);
  renderOverview();
  renderPortfolio();
  renderMarketStatus(record, signal);
  renderQuote(record, signal);
  renderSparkline(record, signal);
  renderAnalysis(record, signal);
  renderPriorityTable();
  renderNewsFeed();
  renderAlertCenter();
  renderKlinePanel();
  renderPositionPanel();
  renderDecisionPanel();
  renderRiskChecklist(record, signal);
  renderStrategyPanel(record, signal);
}

async function refreshDecisionState() {
  const record = currentRecord();
  state.decisionState = state.decisionBySymbol[record.symbol] || null;
  if (!isCnRecord(record)) {
    state.decisionState = null;
    renderKlinePanel();
    renderPositionPanel();
    renderDecisionPanel();
    renderPortfolio();
    return;
  }
  if (state.decisionState?.loadedAt && Date.now() - state.decisionState.loadedAt < 60 * 1000) {
    renderKlinePanel();
    renderPositionPanel();
    renderDecisionPanel();
    renderPortfolio();
    return;
  }
  try {
    state.decisionLoading[record.symbol] = true;
    renderPortfolio();
    state.decisionState = {
      ...(await apiRequest(`/api/analysis/decision?symbol=${encodeURIComponent(record.symbol)}&hermes_mode=${encodeURIComponent(state.hermesMode)}`)),
      loadedAt: Date.now(),
    };
    state.decisionBySymbol[record.symbol] = state.decisionState;
  } catch (error) {
    console.warn("decision analysis unavailable", error);
    try {
      const payload = await apiRequest(`/api/analysis/kline?symbol=${encodeURIComponent(record.symbol)}`);
      state.decisionState = {
        quote: null,
        kline: payload.kline,
        kline_error: null,
        position: null,
        decision: null,
        loadedAt: Date.now(),
        quote_error: error.message,
      };
      state.decisionBySymbol[record.symbol] = state.decisionState;
    } catch (klineError) {
      console.warn("kline analysis unavailable", klineError);
      state.decisionState = {
        quote: null,
        kline: null,
        kline_error: klineError.message,
        position: null,
        decision: null,
        loadedAt: Date.now(),
        quote_error: error.message,
      };
      state.decisionBySymbol[record.symbol] = state.decisionState;
    }
  } finally {
    state.decisionLoading[record.symbol] = false;
  }
  renderKlinePanel();
  renderPositionPanel();
  renderDecisionPanel();
  renderPortfolio();
}

async function refreshPortfolioAnalysis(options = {}) {
  const force = Boolean(options.force);
  const records = getFollowedRecords().filter(isCnRecord);
  if (!records.length) {
    renderPortfolio();
    return;
  }

  const now = Date.now();
  const staleAfterMs = 60 * 1000;
  for (const record of records) {
    if (!force && state.decisionBySymbol[record.symbol] && now - state.decisionBySymbol[record.symbol].loadedAt < staleAfterMs) {
      continue;
    }
    if (state.decisionLoading[record.symbol]) {
      continue;
    }
    state.decisionLoading[record.symbol] = true;
    renderPortfolio();
    try {
      const payload = await apiRequest(`/api/analysis/decision?symbol=${encodeURIComponent(record.symbol)}&hermes_mode=${encodeURIComponent(state.hermesMode)}`);
      state.decisionBySymbol[record.symbol] = { ...payload, loadedAt: Date.now() };
      if (record.symbol === state.selectedSymbol) {
        state.decisionState = state.decisionBySymbol[record.symbol];
      }
    } catch (error) {
      console.warn(`portfolio analysis unavailable for ${record.symbol}`, error);
      try {
        const payload = await apiRequest(`/api/analysis/kline?symbol=${encodeURIComponent(record.symbol)}`);
        state.decisionBySymbol[record.symbol] = {
          loadedAt: Date.now(),
          quote: null,
          quote_error: error.message,
          kline: payload.kline,
          kline_error: null,
          position: null,
          decision: null,
        };
      } catch (klineError) {
        console.warn(`portfolio kline unavailable for ${record.symbol}`, klineError);
        state.decisionBySymbol[record.symbol] = {
          loadedAt: Date.now(),
          quote: null,
          quote_error: error.message,
          kline_error: klineError.message,
          decision: null,
          kline: null,
        };
      }
    } finally {
      state.decisionLoading[record.symbol] = false;
      state.portfolioLastRefreshedAt = new Date();
      renderPortfolio();
    }
  }
  renderKlinePanel();
  renderPositionPanel();
  renderDecisionPanel();
}

function addFollowed(symbol) {
  if (state.followedSymbols.includes(symbol)) return false;
  state.followedSymbols.push(symbol);
  saveFollowed();
  return true;
}

function removeFollowed(symbol) {
  if (!state.followedSymbols.includes(symbol)) return false;
  state.followedSymbols = state.followedSymbols.filter(item => item !== symbol);
  if (!state.followedSymbols.length) {
    state.followedSymbols = [...DEFAULT_FOLLOWED];
  }
  saveFollowed();
  ensureSelectionVisible();
  return true;
}

async function handleSearch() {
  const raw = els.symbolInput.value.trim();
  if (!raw) return;

  try {
    const remote = await apiRequest(`/api/search?q=${encodeURIComponent(raw)}&limit=8`);
    const first = remote.matches?.[0];
    if (first) {
      ensureRecordFromSearchResult(first);
      try {
        await fetchLiveQuotes([first.symbol]);
        state.apiReady = true;
      } catch (quoteError) {
        console.warn("live quote unavailable after search", quoteError);
      }
      state.selectedSymbol = first.symbol;
      const added = addFollowed(first.symbol);
      registerRecentSearch(first.symbol);
      state.lastUpdateAt = new Date();
      renderRecentSearches();
      renderWatchlist();
      renderSelected();
      renderSystemStatus();
      await refreshDecisionState();
      await refreshPortfolioAnalysis({ force: true });
      renderHermesResponse(
        added
          ? `已搜索到并自动加入关注：${first.symbol} · ${first.name}。Hermes 将持续刷新其实时行情。`
          : `已搜索到 ${first.symbol} · ${first.name}，该股票已在关注池中。Hermes 将持续刷新其实时行情。`
      );
      return;
    }
  } catch (error) {
    console.warn("remote search unavailable", error);
  }

  const matched = resolveSearchTarget(raw);

  if (!matched) {
    window.alert(`当前 v1.0.0 原型中未收录 ${raw}。下一阶段会通过 Hermes 数据网关动态拉取全市场股票。`);
    return;
  }

  state.selectedSymbol = matched.symbol;
  const added = addFollowed(matched.symbol);
  registerRecentSearch(matched.symbol);
  state.lastUpdateAt = new Date();
  renderRecentSearches();
  renderWatchlist();
  renderSelected();
  renderSystemStatus();
  await refreshDecisionState();
  await refreshPortfolioAnalysis({ force: true });
  renderHermesResponse(
    added
      ? `已搜索到并自动加入关注：${matched.symbol}。Hermes 将优先监控这只股票的急跌、放量和崩坏风险。`
      : `已聚焦 ${matched.symbol}，该股票已在关注池中。Hermes 将继续盯盘。`
  );
}

async function selectSuggestion(item) {
  if (!item) return;
  els.symbolInput.value = item.symbol;
  hideSuggestions();
  await handleSearch();
}

function simulateStreamTick() {
  state.streamTick += 1;
  state.lastUpdateAt = new Date();

  renderWatchlist();
  renderSelected();
  renderSystemStatus();
  renderPortfolio();
}

function ensureStream() {
  if (streamTimer) return;
  streamTimer = window.setInterval(async () => {
    const liveSymbols = [...new Set(getFollowedRecords().filter(item => item.market === "CN").map(item => item.symbol))];
    if (liveSymbols.length) {
      try {
        await fetchLiveQuotes(liveSymbols);
        state.apiReady = true;
      } catch (error) {
        console.warn("live quote refresh failed", error);
      }
    }
    simulateStreamTick();
    await refreshDecisionState();
    refreshPortfolioAnalysis();
  }, 5000);
}

els.searchBtn.addEventListener("click", () => handleSearch());
els.symbolInput.addEventListener("keydown", event => {
  if (event.key === "ArrowDown" && state.searchSuggestions.length) {
    event.preventDefault();
    state.searchHighlightIndex = Math.min(state.searchHighlightIndex + 1, state.searchSuggestions.length - 1);
    updateSuggestionHighlight();
    return;
  }
  if (event.key === "ArrowUp" && state.searchSuggestions.length) {
    event.preventDefault();
    state.searchHighlightIndex = Math.max(state.searchHighlightIndex - 1, 0);
    updateSuggestionHighlight();
    return;
  }
  if (event.key === "Escape") {
    hideSuggestions();
    return;
  }
  if (event.key === "Enter") {
    event.preventDefault();
    if (state.searchSuggestions.length && state.searchHighlightIndex >= 0) {
      selectSuggestion(state.searchSuggestions[state.searchHighlightIndex]);
      return;
    }
    handleSearch();
  }
});
els.symbolInput.addEventListener("input", event => {
  const value = event.target.value;
  if (searchTimer) clearTimeout(searchTimer);
  searchTimer = window.setTimeout(() => {
    fetchSearchSuggestions(value);
  }, 180);
});
els.symbolInput.addEventListener("focus", event => {
  if (event.target.value.trim()) {
    fetchSearchSuggestions(event.target.value);
  }
});
els.searchSuggestions.addEventListener("click", event => {
  const button = event.target.closest("[data-suggestion-index]");
  if (!button) return;
  const index = Number(button.dataset.suggestionIndex);
  const item = state.searchSuggestions[index];
  selectSuggestion(item);
});
document.addEventListener("click", event => {
  if (event.target === els.symbolInput || event.target.closest("#searchSuggestions")) {
    return;
  }
  hideSuggestions();
});

els.followBtn.addEventListener("click", () => {
  const record = currentRecord();
  const added = addFollowed(record.symbol);
  renderWatchlist();
  renderSystemStatus();
  renderHermesResponse(added ? `${record.symbol} 已加入关注池，Hermes 将持续跟踪其异动。` : `${record.symbol} 已经在关注池中。`);
  refreshPortfolioAnalysis();
});

els.unfollowBtn.addEventListener("click", () => {
  const record = currentRecord();
  const removed = removeFollowed(record.symbol);
  renderWatchlist();
  renderSelected();
  renderSystemStatus();
  renderHermesResponse(removed ? `${record.symbol} 已移出关注池。` : `${record.symbol} 当前不在关注池中。`);
  refreshPortfolioAnalysis();
});

els.resetBtn.addEventListener("click", () => {
  state.followedSymbols = [...DEFAULT_FOLLOWED];
  state.selectedSymbol = DEFAULT_FOLLOWED[0];
  saveFollowed();
  els.symbolInput.value = "";
  state.lastUpdateAt = new Date();
  renderWatchlist();
  renderSelected();
  renderSystemStatus();
  refreshDecisionState();
  refreshPortfolioAnalysis({ force: true });
  renderHermesResponse("关注池已重置到 v1.0.0 默认配置。");
});

els.marketScope.addEventListener("change", event => {
  state.marketScope = event.target.value;
  ensureSelectionVisible();
  state.lastUpdateAt = new Date();
  renderWatchlist();
  renderSelected();
  renderSystemStatus();
  refreshDecisionState();
  refreshPortfolioAnalysis();
});

els.hermesMode.addEventListener("change", event => {
  state.hermesMode = event.target.value;
  state.lastUpdateAt = new Date();
  renderSelected();
  renderSystemStatus();
  refreshDecisionState();
  refreshPortfolioAnalysis({ force: true });
  renderHermesResponse(`Hermes 已切换到 ${hermesModes[state.hermesMode].label}。`);
});

els.watchlist.addEventListener("click", event => {
  const button = event.target.closest("[data-symbol]");
  if (!button) return;
  state.selectedSymbol = button.dataset.symbol;
  state.lastUpdateAt = new Date();
  renderWatchlist();
  renderSelected();
  renderSystemStatus();
  refreshDecisionState();
});

els.recentSearches.addEventListener("click", event => {
  const button = event.target.closest("[data-recent-symbol]");
  if (!button) return;
  const symbol = button.dataset.recentSymbol;
  if (!symbol) return;
  state.selectedSymbol = symbol;
  registerRecentSearch(symbol);
  state.lastUpdateAt = new Date();
  renderRecentSearches();
  renderWatchlist();
  renderSelected();
  renderSystemStatus();
  refreshDecisionState();
  renderHermesResponse(`已从最近搜索切换到 ${symbol}。`);
});

els.priorityTable.addEventListener("click", event => {
  const row = event.target.closest("[data-priority-symbol]");
  if (!row) return;
  state.selectedSymbol = row.dataset.prioritySymbol;
  state.lastUpdateAt = new Date();
  renderWatchlist();
  renderSelected();
  renderSystemStatus();
  refreshDecisionState();
  renderHermesResponse(`已切到优先级标的 ${state.selectedSymbol}，Hermes 将继续跟踪。`);
});

els.portfolioGrid.addEventListener("click", event => {
  const card = event.target.closest("[data-portfolio-symbol]");
  if (!card) return;
  state.selectedSymbol = card.dataset.portfolioSymbol;
  state.lastUpdateAt = new Date();
  renderWatchlist();
  renderSelected();
  renderSystemStatus();
  refreshDecisionState();
});

els.hermesAskBtn.addEventListener("click", () => {
  renderHermesResponse(hermesReply(els.hermesInput.value));
});

els.hermesPresetBtn.addEventListener("click", () => {
  els.hermesInput.value = "当前最危险的股票是谁？";
  renderHermesResponse(hermesReply(els.hermesInput.value));
});

els.hermesInput.addEventListener("keydown", event => {
  if (event.key === "Enter") {
    renderHermesResponse(hermesReply(els.hermesInput.value));
  }
});

ensureSelectionVisible();
renderWorkflow();
renderSystemStatus();
renderRecentSearches();
renderWatchlist();
renderSelected();
refreshDecisionState();
refreshPortfolioAnalysis();
renderHermesResponse("Hermes 已上线。先搜索股票并加入关注池，再由我负责盯风险和发提醒。");
ensureStream();
