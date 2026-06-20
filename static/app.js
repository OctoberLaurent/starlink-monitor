const $ = (s) => document.querySelector(s);
const fmt = (n, d = 1) => (n == null || isNaN(n) ? "—" : Number(n).toFixed(d));
const escapeHtml = (value) =>
  String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");

// =========================================================================
//  Internationalization (EN / FR / ES) — English is the default.
// =========================================================================
const I18N = {
  fr: {
    subtitle_live: "Surveillance live · cible {target}",
    subtitle_demo: "Mode démo — données simulées (parabole non détectée)",
    conn_connecting: "Connexion…",
    conn_online: "EN LIGNE",
    conn_offline: "HORS LIGNE",
    demo_badge: "MODE DÉMO",
    err_unreachable: "parabole injoignable",
    k_download: "Download",
    k_upload: "Upload",
    k_latency: "Latence",
    k_drop: "Perte paquets",
    k_obstruction: "Obstruction",
    k_uptime: "Uptime",
    sub_flux_nominal: "flux nominal",
    sub_obs_active: "⚠ obstruction active",
    sub_state: "état {state}",
    sub_lat_high: "🔴 élevée",
    sub_lat_nominal: "nominal",
    sub_drop_high: "🔴 perte élevée",
    sub_obs_active_s: "⚠ active",
    sub_obs_partial: "partielle",
    sub_obs_clear: "clair",
    panel_perf: "Débit & latence en temps réel",
    panel_obstruction: "Carte d'obstruction",
    panel_loss: "Perte de paquets & latence",
    panel_incidents: "Journal d'incidents",
    radar_cap: "Vue polaire — azimut/élévation",
    radar_fmt: "Az {az}° · Él {el}° · Obstrué {obs} %",
    empty_loading: "Chargement…",
    empty_none: "✨ Aucun incident détecté",
    chip_target: "Cible",
    chip_polls: "Sondes",
    chip_open: "Incidents ouverts",
    chip_total: "Total incidents",
    chip_th_drop: "Seuil perte",
    chip_th_lat: "Seuil latence",
    ongoing: "EN COURS",
    active_count: "● {n} actif(s)",
    chart_download: "Download",
    chart_upload: "Upload",
    chart_latency: "Latence",
    chart_loss: "Perte %",
    title_outage: "Parabole injoignable",
    title_packet_loss: "Perte de paquets élevée",
    title_latency: "Pic de latence",
    title_obstruction: "Obstruction du signal",
    title_snr: "SNR faible",
    title_alert: "Alerte : {label}",
    detail_outage: "Impossible de joindre la parabole : {error}",
    detail_packet_loss: "Taux de perte : {drop} % (latence {latency} ms)",
    detail_latency: "Latence : {latency} ms",
    detail_obstruction: "Obstrué : {obs} % du temps",
    detail_snr: "SNR sous le seuil de bruit",
    detail_alert: "La parabole signale « {label} »",
    tag_outage: "Coupure",
    tag_packet_loss: "Perte paquets",
    tag_latency: "Latence",
    tag_obstruction: "Obstruction",
    tag_snr: "SNR",
    tag_alert: "Alerte",
    alert_motorsStuck: "Moteurs bloqués",
    alert_thermalThrottle: "Étranglement thermique",
    alert_thermalShutdown: "Arrêt thermique",
    alert_mastNotNearVertical: "Mât non vertical",
    alert_slowEthernetSpeeds: "Ethernet lent",
    alert_snrPersistentlyLow: "SNR faible",
    locale: "fr-FR",
  },
  en: {
    subtitle_live: "Live monitoring · target {target}",
    subtitle_demo: "Demo mode — simulated data (dish not detected)",
    conn_connecting: "Connecting…",
    conn_online: "ONLINE",
    conn_offline: "OFFLINE",
    demo_badge: "DEMO MODE",
    err_unreachable: "dish unreachable",
    k_download: "Download",
    k_upload: "Upload",
    k_latency: "Latency",
    k_drop: "Packet loss",
    k_obstruction: "Obstruction",
    k_uptime: "Uptime",
    sub_flux_nominal: "nominal flow",
    sub_obs_active: "⚠ active obstruction",
    sub_state: "state {state}",
    sub_lat_high: "🔴 high",
    sub_lat_nominal: "nominal",
    sub_drop_high: "🔴 high loss",
    sub_obs_active_s: "⚠ active",
    sub_obs_partial: "partial",
    sub_obs_clear: "clear",
    panel_perf: "Throughput & latency in real time",
    panel_obstruction: "Obstruction map",
    panel_loss: "Packet loss & latency",
    panel_incidents: "Incident log",
    radar_cap: "Polar view — azimuth/elevation",
    radar_fmt: "Az {az}° · El {el}° · Obstructed {obs} %",
    empty_loading: "Loading…",
    empty_none: "✨ No incident detected",
    chip_target: "Target",
    chip_polls: "Polls",
    chip_open: "Open incidents",
    chip_total: "Total incidents",
    chip_th_drop: "Loss threshold",
    chip_th_lat: "Latency threshold",
    ongoing: "ONGOING",
    active_count: "● {n} active",
    chart_download: "Download",
    chart_upload: "Upload",
    chart_latency: "Latency",
    chart_loss: "Loss %",
    title_outage: "Dish unreachable",
    title_packet_loss: "High packet loss",
    title_latency: "Latency spike",
    title_obstruction: "Signal obstruction",
    title_snr: "Low SNR",
    title_alert: "Alert: {label}",
    detail_outage: "Could not reach the dish: {error}",
    detail_packet_loss: "Loss rate: {drop}% (latency {latency} ms)",
    detail_latency: "Latency: {latency} ms",
    detail_obstruction: "Obstructed: {obs}% of the time",
    detail_snr: "SNR below noise floor",
    detail_alert: 'The dish reports "{label}"',
    tag_outage: "Outage",
    tag_packet_loss: "Packet loss",
    tag_latency: "Latency",
    tag_obstruction: "Obstruction",
    tag_snr: "SNR",
    tag_alert: "Alert",
    alert_motorsStuck: "Motors stuck",
    alert_thermalThrottle: "Thermal throttle",
    alert_thermalShutdown: "Thermal shutdown",
    alert_mastNotNearVertical: "Mast not vertical",
    alert_slowEthernetSpeeds: "Slow ethernet",
    alert_snrPersistentlyLow: "Low SNR",
    locale: "en-GB",
  },
  es: {
    subtitle_live: "Supervisión en vivo · destino {target}",
    subtitle_demo: "Modo demo — datos simulados (antena no detectada)",
    conn_connecting: "Conectando…",
    conn_online: "EN LÍNEA",
    conn_offline: "FUERA DE LÍNEA",
    demo_badge: "MODO DEMO",
    err_unreachable: "antena inaccesible",
    k_download: "Descarga",
    k_upload: "Subida",
    k_latency: "Latencia",
    k_drop: "Pérdida paq.",
    k_obstruction: "Obstrucción",
    k_uptime: "Tiempo activo",
    sub_flux_nominal: "flujo nominal",
    sub_obs_active: "⚠ obstrucción activa",
    sub_state: "estado {state}",
    sub_lat_high: "🔴 alta",
    sub_lat_nominal: "nominal",
    sub_drop_high: "🔴 pérdida alta",
    sub_obs_active_s: "⚠ activa",
    sub_obs_partial: "parcial",
    sub_obs_clear: "despejado",
    panel_perf: "Throughput y latencia en tiempo real",
    panel_obstruction: "Mapa de obstrucción",
    panel_loss: "Pérdida de paquetes y latencia",
    panel_incidents: "Registro de incidentes",
    radar_cap: "Vista polar — azimut/elevación",
    radar_fmt: "Az {az}° · El {el}° · Obstruido {obs} %",
    empty_loading: "Cargando…",
    empty_none: "✨ Ningún incidente detectado",
    chip_target: "Destino",
    chip_polls: "Sondeos",
    chip_open: "Incidentes abiertos",
    chip_total: "Total incidentes",
    chip_th_drop: "Umbral pérdida",
    chip_th_lat: "Umbral latencia",
    ongoing: "EN CURSO",
    active_count: "● {n} activo(s)",
    chart_download: "Descarga",
    chart_upload: "Subida",
    chart_latency: "Latencia",
    chart_loss: "Pérdida %",
    title_outage: "Antena inaccesible",
    title_packet_loss: "Pérdida de paquetes elevada",
    title_latency: "Pico de latencia",
    title_obstruction: "Obstrucción de la señal",
    title_snr: "SNR bajo",
    title_alert: "Alerta: {label}",
    detail_outage: "No se pudo acceder a la antena: {error}",
    detail_packet_loss: "Tasa de pérdida: {drop}% (latencia {latency} ms)",
    detail_latency: "Latencia: {latency} ms",
    detail_obstruction: "Obstruido: {obs}% del tiempo",
    detail_snr: "SNR por debajo del umbral de ruido",
    detail_alert: "La antena reporta « {label} »",
    tag_outage: "Corte",
    tag_packet_loss: "Pérdida paq.",
    tag_latency: "Latencia",
    tag_obstruction: "Obstrucción",
    tag_snr: "SNR",
    tag_alert: "Alerta",
    alert_motorsStuck: "Motores bloqueados",
    alert_thermalThrottle: "Limitación térmica",
    alert_thermalShutdown: "Apagado térmico",
    alert_mastNotNearVertical: "Mástil no vertical",
    alert_slowEthernetSpeeds: "Ethernet lento",
    alert_snrPersistentlyLow: "SNR bajo",
    locale: "es-ES",
  },
};

// Default language is English (falls back to English if unknown/saved value).
let lang =
  localStorage.getItem("starlink_lang") ||
  (I18N[(navigator.language || "en").slice(0, 2)]
    ? navigator.language.slice(0, 2)
    : "en");
if (!I18N[lang]) lang = "en";

function t(key, params) {
  let s = (I18N[lang] && I18N[lang][key]) || I18N.en[key] || key;
  if (params) for (const k in params) s = s.split("{" + k + "}").join(params[k]);
  return s;
}

function applyStatic() {
  document.documentElement.lang = lang;
  document.querySelectorAll("[data-i18n]").forEach((el) => {
    el.textContent = t(el.getAttribute("data-i18n"));
  });
  document.querySelectorAll("#lang button").forEach((b) => {
    b.classList.toggle("active", b.dataset.lang === lang);
  });
  applyChartsLang();
  // re-render radar caption + timeline with the new language
  drawRadar(lastRadar.obs, lastRadar.cur, lastRadar.az, lastRadar.el);
  renderTimeline(lastIncidents);
}

document.querySelectorAll("#lang button").forEach((b) => {
  b.addEventListener("click", () => {
    lang = b.dataset.lang;
    localStorage.setItem("starlink_lang", lang);
    applyStatic();
    refresh();
  });
});

// =========================================================================
//  Starfield
// =========================================================================
const cv = $("#starfield"),
  ctx = cv.getContext("2d");
let stars = [];
function resize() {
  cv.width = innerWidth;
  cv.height = innerHeight;
  stars = Array.from(
    { length: Math.min(260, Math.floor((innerWidth * innerHeight) / 9000)) },
    () => ({
      x: Math.random() * cv.width,
      y: Math.random() * cv.height,
      r: Math.random() * 1.4 + 0.2,
      s: Math.random() * 0.4 + 0.05,
      tw: Math.random() * Math.PI * 2,
    })
  );
}
addEventListener("resize", resize);
resize();
function drawSky() {
  ctx.clearRect(0, 0, cv.width, cv.height);
  for (const s of stars) {
    s.tw += 0.03;
    const a = 0.4 + 0.6 * (0.5 + 0.5 * Math.sin(s.tw));
    ctx.beginPath();
    ctx.arc(s.x, s.y, s.r, 0, 7);
    ctx.fillStyle = `rgba(180,200,255,${a * 0.7})`;
    ctx.fill();
    s.y += s.s;
    if (s.y > cv.height) {
      s.y = 0;
      s.x = Math.random() * cv.width;
    }
  }
  requestAnimationFrame(drawSky);
}
drawSky();

// =========================================================================
//  Charts
// =========================================================================
const grid = { color: "rgba(120,150,255,.07)" };
const ticks = { color: "#8b94c2", font: { size: 10 } };
const commonOpts = {
  responsive: true,
  maintainAspectRatio: false,
  animation: { duration: 300 },
  interaction: { intersect: false, mode: "index" },
  plugins: {
    legend: { display: false },
    tooltip: {
      backgroundColor: "rgba(10,14,31,.95)",
      borderColor: "rgba(120,150,255,.25)",
      borderWidth: 1,
      padding: 10,
      titleColor: "#e8ecff",
      bodyColor: "#e8ecff",
    },
  },
};
const xLin = { ticks: { color: "#8b94c2", font: { size: 9 }, maxTicksLimit: 6 }, grid };
const perfChart = new Chart($("#perfChart"), {
  type: "line",
  data: {
    labels: [],
    datasets: [
      {
        label: "Download",
        data: [],
        borderColor: "#34e7ff",
        backgroundColor: "rgba(52,231,255,.08)",
        fill: true,
        tension: 0.35,
        borderWidth: 2,
        pointRadius: 0,
        yAxisID: "y",
      },
      {
        label: "Upload",
        data: [],
        borderColor: "#a872ff",
        backgroundColor: "rgba(168,114,255,.08)",
        fill: true,
        tension: 0.35,
        borderWidth: 2,
        pointRadius: 0,
        yAxisID: "y",
      },
      {
        label: "Latency",
        data: [],
        borderColor: "#5b8cff",
        backgroundColor: "transparent",
        tension: 0.35,
        borderWidth: 2,
        pointRadius: 0,
        borderDash: [5, 4],
        yAxisID: "y1",
      },
    ],
  },
  options: {
    ...commonOpts,
    scales: {
      x: xLin,
      y: {
        position: "left",
        ticks,
        grid,
        title: { display: true, text: "Mbps", color: "#8b94c2" },
      },
      y1: {
        position: "right",
        ticks,
        grid: { drawOnChartArea: false },
        title: { display: true, text: "ms", color: "#8b94c2" },
      },
    },
  },
});

const lossChart = new Chart($("#lossChart"), {
  type: "line",
  data: {
    labels: [],
    datasets: [
      {
        label: "Loss %",
        data: [],
        borderColor: "#ff4d6d",
        backgroundColor: "rgba(255,77,109,.12)",
        fill: true,
        tension: 0.35,
        borderWidth: 2,
        pointRadius: 0,
        yAxisID: "y",
      },
      {
        label: "Latency",
        data: [],
        borderColor: "#ffcb47",
        backgroundColor: "transparent",
        tension: 0.35,
        borderWidth: 2,
        pointRadius: 0,
        yAxisID: "y1",
      },
    ],
  },
  options: {
    ...commonOpts,
    scales: {
      x: xLin,
      y: {
        position: "left",
        ticks,
        grid,
        beginAtZero: true,
        min: 0,
        max: 100,
        title: { display: true, text: "%", color: "#8b94c2" },
      },
      y1: {
        position: "right",
        ticks,
        grid: { drawOnChartArea: false },
        title: { display: true, text: "ms", color: "#8b94c2" },
      },
    },
  },
});

function applyChartsLang() {
  perfChart.data.datasets[0].label = t("chart_download");
  perfChart.data.datasets[1].label = t("chart_upload");
  perfChart.data.datasets[2].label = t("chart_latency");
  lossChart.data.datasets[0].label = t("chart_loss");
  lossChart.data.datasets[1].label = t("chart_latency");
  perfChart.update("none");
  lossChart.update("none");
}

// =========================================================================
//  Radar / obstruction
// =========================================================================
const lastRadar = { obs: 0, cur: false, az: 145, el: 32 };
function drawRadar(obspct, cur, az, el) {
  lastRadar.obs = obspct;
  lastRadar.cur = cur;
  lastRadar.az = az;
  lastRadar.el = el;
  const s = $("#radar");
  s.innerHTML = "";
  const ring = (r, c) => {
    const c1 = document.createElementNS("http://www.w3.org/2000/svg", "circle");
    c1.setAttribute("cx", 0);
    c1.setAttribute("cy", 0);
    c1.setAttribute("r", r);
    c1.setAttribute("fill", "none");
    c1.setAttribute("stroke", c);
    c1.setAttribute("stroke-width", ".6");
    s.appendChild(c1);
  };
  [18, 36, 54, 72, 90].forEach((r, i) =>
    ring(r, `rgba(120,150,255,${0.18 - i * 0.03})`)
  );
  for (let a = 0; a < 360; a += 30) {
    const rad = (a * Math.PI) / 180;
    const l = document.createElementNS("http://www.w3.org/2000/svg", "line");
    l.setAttribute("x1", 0);
    l.setAttribute("y1", 0);
    l.setAttribute("x2", Math.sin(rad) * 90);
    l.setAttribute("y2", -Math.cos(rad) * 90);
    l.setAttribute("stroke", "rgba(120,150,255,.08)");
    l.setAttribute("stroke-width", ".5");
    s.appendChild(l);
  }
  const elR = 90 - (el / 90) * 90;
  const ea = document.createElementNS("http://www.w3.org/2000/svg", "circle");
  ea.setAttribute("cx", 0);
  ea.setAttribute("cy", 0);
  ea.setAttribute("r", elR);
  ea.setAttribute("fill", "none");
  ea.setAttribute("stroke", "rgba(52,231,255,.4)");
  ea.setAttribute("stroke-dasharray", "3 3");
  s.appendChild(ea);
  const obsR = Math.min(90, 18 + obspct * 2.2);
  const col = cur ? "#ff4d6d" : "#ff9b3d";
  const of = document.createElementNS("http://www.w3.org/2000/svg", "circle");
  of.setAttribute("cx", 0);
  of.setAttribute("cy", 0);
  of.setAttribute("r", obsR);
  of.setAttribute("fill", col);
  of.setAttribute("opacity", ".18");
  s.appendChild(of);
  const rad = (az * Math.PI) / 180;
  const px = Math.sin(rad) * 90,
    py = -Math.cos(rad) * 90;
  const ln = document.createElementNS("http://www.w3.org/2000/svg", "line");
  ln.setAttribute("x1", 0);
  ln.setAttribute("y1", 0);
  ln.setAttribute("x2", px);
  ln.setAttribute("y2", py);
  ln.setAttribute("stroke", "#34e7ff");
  ln.setAttribute("stroke-width", "1.8");
  ln.setAttribute("opacity", ".8");
  s.appendChild(ln);
  const dot = document.createElementNS("http://www.w3.org/2000/svg", "circle");
  dot.setAttribute("cx", px);
  dot.setAttribute("cy", py);
  dot.setAttribute("r", 3.5);
  dot.setAttribute("fill", "#34e7ff");
  s.appendChild(dot);
  const ctr = document.createElementNS("http://www.w3.org/2000/svg", "circle");
  ctr.setAttribute("cx", 0);
  ctr.setAttribute("cy", 0);
  ctr.setAttribute("r", 3);
  ctr.setAttribute("fill", "#a872ff");
  s.appendChild(ctr);
  $("#radarCap").textContent = t("radar_fmt", {
    az: fmt(az, 0),
    el: fmt(el, 0),
    obs: fmt(obspct, 1),
  });
}

// =========================================================================
//  Incident rendering (localized)
// =========================================================================
let lastIncidents = [];
function alertLabel(kind, params) {
  const key = kind.startsWith("alert_") ? kind.slice(6) : null;
  if (!key) return (params && params.label) || "";
  return t("alert_" + key, {}) || (params && params.label) || key;
}
function incidentTitle(kind, params) {
  if (kind.startsWith("alert_"))
    return t("title_alert", { label: alertLabel(kind, params) });
  return t("title_" + kind, params || {}) || kind;
}
function incidentDetail(kind, params) {
  if (kind.startsWith("alert_"))
    return t("detail_alert", { label: alertLabel(kind, params) });
  return t("detail_" + kind, params || {}) || "";
}
function incidentTag(kind) {
  if (kind.startsWith("alert_")) return t("tag_alert");
  return t("tag_" + kind) || kind;
}

function renderTimeline(incidents) {
  const tl = $("#timeline");
  if (!incidents.length) {
    tl.innerHTML = '<div class="empty">' + t("empty_none") + "</div>";
    return;
  }
  tl.innerHTML = incidents
    .slice(0, 40)
    .map((i) => {
      const sev = ["info", "warning", "critical"].includes(i.severity)
        ? i.severity
        : "info";
      const p = i.params || {};
      const dur = i.ts_end ? "· " + durStr(i.ts_end - i.ts_start) : "";
      return `<div class="inc ${sev}">
      <div class="bar"></div>
      <div class="body">
        <div class="ti"><b>${escapeHtml(incidentTitle(i.kind, p))}</b><span class="when">${escapeHtml(timeStr(i.ts_start))} ${escapeHtml(dur)}</span></div>
        <div class="det">${escapeHtml(incidentDetail(i.kind, p))}</div>
        <span class="tag">${escapeHtml(incidentTag(i.kind).toUpperCase())}</span>
        ${i.ongoing ? '<div class="ongoing"><i></i>' + t("ongoing") + "</div>" : ""}
      </div>
    </div>`;
    })
    .join("");
}

// =========================================================================
//  UI update
// =========================================================================
const MAX = 120;
function timeStr(ts) {
  const d = new Date(ts * 1000);
  return d.toLocaleTimeString(I18N[lang].locale, {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}
function durStr(s) {
  s = Math.floor(s || 0);
  const h = Math.floor(s / 3600),
    m = Math.floor((s % 3600) / 60),
    sec = s % 60;
  if (h > 0) return `${h}h${m.toString().padStart(2, "0")}`;
  return `${m}m${sec.toString().padStart(2, "0")}s`;
}

let refreshInProgress = false;
async function refresh() {
  if (refreshInProgress) return;
  refreshInProgress = true;
  try {
    const r = await fetch("/api/state");
    if (!r.ok) throw new Error(`API returned HTTP ${r.status}`);
    const d = await r.json();
    lastIncidents = d.incidents;

    const ok = d.connected;
    const dot = $("#dot");
    dot.className = "dot " + (ok ? "ok" : "bad");
    $("#connState").innerHTML = ok
      ? `<b>${t("conn_online")}</b> · ${escapeHtml(d.last_sample ? d.last_sample.state : "CONNECTED")}`
      : `<b style="color:var(--red)">${t("conn_offline")}</b>`;
    $("#connInfo").textContent = ok
      ? d.dish_info
        ? `${d.dish_info.id} · ${d.dish_info.software}`
        : ""
      : d.last_error || t("err_unreachable");
    $("#demoBadge").style.display = d.demo ? "block" : "none";
    $("#subtitle").textContent = d.demo
      ? t("subtitle_demo")
      : t("subtitle_live", { target: d.target });
    $("#cTarget").textContent = d.target;

    const s = d.last_sample;
    if (s) {
      $("#kDown").innerHTML = `${fmt(s.down_mbps, 1)}<span class="u">Mbps</span>`;
      $("#kUp").innerHTML = `${fmt(s.up_mbps, 1)}<span class="u">Mbps</span>`;
      $("#kLat").innerHTML = `${fmt(s.latency_ms, 0)}<span class="u">ms</span>`;
      $("#kDrop").innerHTML = `${fmt(s.drop_rate * 100, 1)}<span class="u">%</span>`;
      $("#kObs").innerHTML = `${fmt(s.obstruction_pct, 1)}<span class="u">%</span>`;
      $("#kUpk").innerHTML = `${fmt(s.uptime_s / 3600, 1)}<span class="u">h</span>`;
      $("#kDownSub").textContent = s.currently_obstructed
        ? t("sub_obs_active")
        : t("sub_flux_nominal");
      $("#kUpkSub").textContent = t("sub_state", { state: s.state });
      $("#kLatSub").textContent =
        s.latency_ms > d.thresholds.latency_ms
          ? t("sub_lat_high")
          : t("sub_lat_nominal");
      $("#kDropSub").textContent =
        s.drop_rate > d.thresholds.drop_rate
          ? t("sub_drop_high")
          : t("sub_lat_nominal");
      $("#kObsSub").textContent = s.currently_obstructed
        ? t("sub_obs_active_s")
        : s.obstruction_pct > d.thresholds.obstruction_pct
          ? t("sub_obs_partial")
          : t("sub_obs_clear");
    }

    $("#cPoll").textContent = d.poll_count;
    $("#cOpen").textContent = d.open_incidents;
    $("#cTotal").textContent = d.total_incidents;
    $("#cThDrop").textContent = d.thresholds.drop_rate * 100 + " %";
    $("#cThLat").textContent = d.thresholds.latency_ms + " ms";

    const samples = d.samples.slice(-MAX);
    const labels = samples.map((x) => timeStr(x.ts));
    perfChart.data.labels = labels;
    perfChart.data.datasets[0].data = samples.map((x) => +x.down_mbps.toFixed(2));
    perfChart.data.datasets[1].data = samples.map((x) => +x.up_mbps.toFixed(2));
    perfChart.data.datasets[2].data = samples.map((x) => +x.latency_ms.toFixed(1));
    perfChart.update("none");
    lossChart.data.labels = labels;
    lossChart.data.datasets[0].data = samples.map(
      (x) => +(x.drop_rate * 100).toFixed(2)
    );
    lossChart.data.datasets[1].data = samples.map((x) => +x.latency_ms.toFixed(1));
    lossChart.update("none");

    const az = d.dish_info?.boresight_az || 145,
      el = d.dish_info?.boresight_el || 32;
    const obs = s ? s.obstruction_pct : 0,
      cur = s ? s.currently_obstructed : false;
    drawRadar(obs, cur, az, el);

    renderTimeline(d.incidents);
    $("#incCount").innerHTML = d.open_incidents
      ? `<span style="color:var(--red);font-weight:700">${t("active_count", { n: d.open_incidents })}</span>`
      : "";

    document.querySelector(".stat-grid").classList.toggle(
      "glow-red",
      d.incidents.some((i) => i.ongoing && i.severity === "critical")
    );
  } catch (e) {
    console.error(e);
  } finally {
    refreshInProgress = false;
  }
}

// init
applyStatic();
refresh();
setInterval(refresh, 1000);
