/* ==========================================================================
   ACO MAPS · JAVASCRIPT CLIENT (SPA)
   Integración con Leaflet.js, Chart.js y API REST de Optimización con ACO
   ========================================================================== */

// Lista de lugares por defecto (Monterrey, N.L.)
const DEFAULT_MTY_PLACES = [
    "Macroplaza, Monterrey",
    "Parque Fundidora, Monterrey",
    "El Obispado, Monterrey",
    "Tecnologico de Monterrey, Monterrey",
    "San Pedro Garza Garcia, Nuevo Leon",
    "Basilica de Guadalupe, Monterrey"
];

// Estado global de la aplicación
const state = {
    lugares: [...DEFAULT_MTY_PLACES],
    map: null,
    markersLayer: null,
    routesLayer: null,
    chart: null,
    isCalculating: false
};

// Inicialización cuando carga el DOM
document.addEventListener("DOMContentLoaded", () => {
    initMap();
    initChart();
    initEventListeners();
    renderLugaresList();
    checkApiStatus();
});

/* ==========================================================================
   INICIALIZACIÓN DEL MAPA LEAFLET
   ========================================================================== */
function initMap() {
    // Coordenadas iniciales: Monterrey, México
    state.map = L.map("map", {
        zoomControl: false,
        attributionControl: false
    }).setView([25.67, -100.31], 12);

    // Mosaicos gratuitos de OpenStreetMap con estilo Liquid Glass Dark (100% libre, sin marca de agua ni API Key requerida)
    L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 19,
        attribution: '&copy; OpenStreetMap contributors'
    }).addTo(state.map);

    // Controles de zoom abajo a la izquierda para no estorbar con el top nav
    L.control.zoom({ position: "bottomleft" }).addTo(state.map);

    // Capas separadas para marcadores y líneas
    state.routesLayer = L.layerGroup().addTo(state.map);
    state.markersLayer = L.layerGroup().addTo(state.map);
}

/* ==========================================================================
   INICIALIZACIÓN DE LA GRÁFICA DE CONVERGENCIA (CHART.JS)
   ========================================================================== */
function initChart() {
    const ctx = document.getElementById("chartConvergencia").getContext("2d");
    
    // Gradiente sutil para el área bajo la curva
    const gradient = ctx.createLinearGradient(0, 0, 0, 140);
    gradient.addColorStop(0, "rgba(0, 242, 254, 0.25)");
    gradient.addColorStop(1, "rgba(0, 242, 254, 0.0)");

    state.chart = new Chart(ctx, {
        type: "line",
        data: {
            labels: [],
            datasets: [{
                label: "Tiempo (min)",
                data: [],
                borderColor: "#00f2fe",
                borderWidth: 2,
                backgroundColor: gradient,
                fill: true,
                tension: 0.35,
                pointRadius: 0,
                pointHoverRadius: 4,
                pointHoverBackgroundColor: "#ffffff",
                pointHoverBorderColor: "#00f2fe"
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: "rgba(18, 22, 32, 0.9)",
                    titleColor: "#94a3b8",
                    bodyColor: "#ffffff",
                    borderColor: "rgba(255, 255, 255, 0.15)",
                    borderWidth: 1,
                    displayColors: false,
                    callbacks: {
                        title: (items) => `Época ${items[0].label}`,
                        label: (item) => `Mejor: ${item.formattedValue} min`
                    }
                }
            },
            scales: {
                x: {
                    grid: { color: "rgba(255, 255, 255, 0.04)" },
                    ticks: { color: "#64748b", font: { size: 9 }, maxTicksLimit: 6 }
                },
                y: {
                    grid: { color: "rgba(255, 255, 255, 0.04)" },
                    ticks: { color: "#64748b", font: { size: 9 } }
                }
            }
        }
    });
}

/* ==========================================================================
   EVENT LISTENERS Y VINCULACIÓN DE CONTROLES
   ========================================================================== */
function initEventListeners() {
    const inputLugar = document.getElementById("inputLugar");
    const btnAgregar = document.getElementById("btnAgregarLugar");
    const suggestionsBox = document.getElementById("suggestionsBox");

    // Autocompletado en tiempo real con debounce
    let debounceTimer = null;
    inputLugar.addEventListener("input", () => {
        clearTimeout(debounceTimer);
        const query = inputLugar.value.trim();

        if (query.length < 2) {
            suggestionsBox.innerHTML = "";
            suggestionsBox.classList.remove("show");
            return;
        }

        debounceTimer = setTimeout(async () => {
            try {
                const resp = await fetch(`/api/autocompletar?q=${encodeURIComponent(query)}`);
                const data = await resp.json();
                renderSuggestions(data.sugerencias || []);
            } catch (_) {}
        }, 250);
    });

    function renderSuggestions(sugerencias) {
        suggestionsBox.innerHTML = "";
        if (!sugerencias || sugerencias.length === 0) {
            suggestionsBox.classList.remove("show");
            return;
        }

        sugerencias.forEach((sug) => {
            const div = document.createElement("div");
            div.className = "suggestion-item";
            div.innerHTML = `
                <span class="suggestion-icon">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>
                </span>
                <span class="suggestion-text">${sug.nombre}</span>
            `;

            div.addEventListener("click", () => {
                agregarLugarDirecto(sug.nombre, sug.lat, sug.lon);
                inputLugar.value = "";
                suggestionsBox.innerHTML = "";
                suggestionsBox.classList.remove("show");
            });

            suggestionsBox.appendChild(div);
        });

        suggestionsBox.classList.add("show");
    }

    // Cerrar sugerencias al hacer clic fuera
    document.addEventListener("click", (e) => {
        if (!e.target.closest(".search-wrapper")) {
            suggestionsBox.classList.remove("show");
        }
    });

    // Agregar lugar manual (Enter o botón +)
    const agregarAccion = async () => {
        const val = inputLugar.value.trim();
        if (!val) return;

        if (state.lugares.length >= 25) {
            showToast("Máximo 25 lugares permitidos.", "⚠️");
            return;
        }

        suggestionsBox.classList.remove("show");
        showToast("Verificando ubicación...", "🔍");

        try {
            const res = await fetch(`/api/buscar?q=${encodeURIComponent(val)}`);
            const data = await res.json();
            if (data.ok && data.lugar) {
                agregarLugarDirecto(data.lugar.nombre, data.lugar.lat, data.lugar.lon);
            } else {
                agregarLugarDirecto(val);
            }
        } catch (_) {
            agregarLugarDirecto(val);
        }

        inputLugar.value = "";
    };

    btnAgregar.addEventListener("click", agregarAccion);
    inputLugar.addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
            // Si hay sugerencias visibles, tomar la primera
            const primeraSugerencia = suggestionsBox.querySelector(".suggestion-item");
            if (primeraSugerencia) {
                primeraSugerencia.click();
            } else {
                agregarAccion();
            }
        }
    });

    // Clic en el mapa para añadir cualquier punto con detección inversa
    state.map.on("click", async (e) => {
        if (state.lugares.length >= 25) {
            showToast("Máximo 25 lugares permitidos.", "⚠️");
            return;
        }

        const { lat, lng } = e.latlng;
        showToast("Detectando dirección del punto...", "📍");

        try {
            const resp = await fetch(`/api/reverso?lat=${lat}&lon=${lng}`);
            const data = await resp.json();
            const nombre = data.lugar ? data.lugar.nombre : `Punto (${lat.toFixed(4)}, ${lng.toFixed(4)})`;
            agregarLugarDirecto(nombre, lat, lng);
            showToast(`Añadido: ${nombre}`, "✓");
        } catch (_) {
            const coordStr = `${lat.toFixed(4)}, ${lng.toFixed(4)}`;
            agregarLugarDirecto(coordStr, lat, lng);
            showToast(`Añadido: ${coordStr}`, "✓");
        }
    });

    // Botones de presets
    document.getElementById("btnPresetMty").addEventListener("click", () => {
        state.lugares = [...DEFAULT_MTY_PLACES];
        renderLugaresList();
        showToast("Plantilla de Monterrey cargada.", "📍");
    });

    document.getElementById("btnLimpiar").addEventListener("click", () => {
        state.lugares = [];
        renderLugaresList();
        clearMap();
        resetStats();
        showToast("Lista de lugares vaciada.", "🗑️");
    });

    // Sliders de parámetros
    bindSlider("paramHormigas", "valHormigas");
    bindSlider("paramEpocas", "valEpocas");
    bindSlider("paramEvaporacion", "valEvaporacion");
    bindSlider("paramAlfa", "valAlfa");
    bindSlider("paramBeta", "valBeta");
    bindSlider("paramQ", "valQ");

    // Botón de cálculo de ruta
    document.getElementById("btnCalcular").addEventListener("click", ejecutarOptimizacion);
}

function agregarLugarDirecto(nombre, lat = null, lon = null) {
    state.lugares.push(nombre);
    renderLugaresList();

    if (lat !== null && lon !== null) {
        // Colocar un marcador de confirmación y centrar
        const marker = L.circleMarker([lat, lon], {
            radius: 8,
            color: "#00f2fe",
            weight: 2,
            fillColor: "#00f2fe",
            fillOpacity: 0.8
        }).bindPopup(nombre).addTo(state.markersLayer);
        
        state.map.setView([lat, lon], Math.max(state.map.getZoom(), 13), { animate: true });
    }
}

function bindSlider(sliderId, labelId) {
    const slider = document.getElementById(sliderId);
    const label = document.getElementById(labelId);
    slider.addEventListener("input", () => {
        label.textContent = slider.value;
    });
}

/* ==========================================================================
   RENDERIZAR LISTA DE LUGARES
   ========================================================================== */
function renderLugaresList() {
    const contenedor = document.getElementById("listaLugares");
    const contador = document.getElementById("countLugares");
    
    contador.textContent = `${state.lugares.length} / 25`;
    contenedor.innerHTML = "";

    if (state.lugares.length === 0) {
        contenedor.innerHTML = `<div class="empty-state">No hay lugares en la ruta. Escribe arriba para agregar.</div>`;
        return;
    }

    state.lugares.forEach((lugar, idx) => {
        const item = document.createElement("div");
        item.className = `lugar-item ${idx === 0 ? "origen" : ""}`;
        item.innerHTML = `
            <div class="lugar-info">
                <span class="lugar-num">${idx + 1}</span>
                <span class="lugar-nombre" title="${lugar}">${lugar}</span>
            </div>
            <button class="lugar-delete-btn" data-index="${idx}" title="Eliminar">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
            </button>
        `;

        item.querySelector(".lugar-delete-btn").addEventListener("click", (e) => {
            const i = parseInt(e.currentTarget.getAttribute("data-index"));
            state.lugares.splice(i, 1);
            renderLugaresList();
        });

        contenedor.appendChild(item);
    });
}

/* ==========================================================================
   EJECUTAR OPTIMIZACIÓN VÍA API REST
   ========================================================================== */
async function ejecutarOptimizacion() {
    if (state.isCalculating) return;

    if (state.lugares.length < 2) {
        showToast("Agrega al menos 2 ubicaciones para trazar una ruta.", "⚠️");
        return;
    }

    state.isCalculating = true;
    showLoader(true, "Geocodificando y consultando matriz de tiempos...");

    const payload = {
        lugares: state.lugares,
        regresar_inicio: document.getElementById("checkRegresar").checked,
        n_hormigas: parseInt(document.getElementById("paramHormigas").value),
        epocas: parseInt(document.getElementById("paramEpocas").value),
        evaporacion: parseFloat(document.getElementById("paramEvaporacion").value),
        alfa: parseFloat(document.getElementById("paramAlfa").value),
        beta: parseFloat(document.getElementById("paramBeta").value),
        q: parseFloat(document.getElementById("paramQ").value),
        semilla: document.getElementById("checkSemilla").checked ? 42 : null
    };

    try {
        const resp = await fetch("/api/optimizar", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        const data = await resp.json();

        if (!resp.ok) {
            throw new Error(data.detail || "Error al calcular la ruta.");
        }

        renderResultados(data);
        showToast("¡Ruta óptima calculada exitosamente!", "🚀");

    } catch (err) {
        showToast(err.message, "❌");
    } finally {
        showLoader(false);
        state.isCalculating = false;
    }
}

/* ==========================================================================
   RENDERIZAR RESULTADOS Y MAPA
   ========================================================================== */
function renderResultados(data) {
    const { metricas, secuencia, geometria_ruta, historial_convergencia } = data;

    // 1. Actualizar métricas numéricas
    document.getElementById("statTiempoAco").innerHTML = `${metricas.tiempo_aco_min} <small>min</small>`;
    document.getElementById("statTiempoOrig").innerHTML = `${metricas.tiempo_original_min} <small>min</small>`;
    document.getElementById("statMejoraPct").textContent = `${metricas.mejora_porcentaje}%`;
    document.getElementById("statAhorroMin").textContent = `-${metricas.ahorro_min} min ahorrados`;
    document.getElementById("statDistancia").innerHTML = `${metricas.distancia_km} <small>km</small>`;

    // 2. Actualizar lista de itinerario
    const containerItinerary = document.getElementById("itineraryList");
    containerItinerary.innerHTML = "";

    secuencia.forEach((item) => {
        const div = document.createElement("div");
        div.className = "itinerary-step";

        let badgeClass = "parada";
        let badgeText = `${item.paso}. Parada`;

        if (item.es_origen) {
            badgeClass = "origen";
            badgeText = "1. Origen";
        } else if (item.es_retorno) {
            badgeClass = "retorno";
            badgeText = `${item.paso}. Fin`;
        }

        div.innerHTML = `
            <span class="step-badge ${badgeClass}">${badgeText}</span>
            <span class="step-name" title="${item.nombre}">${item.nombre}</span>
        `;
        containerItinerary.appendChild(div);
    });

    // 3. Actualizar gráfica Chart.js
    state.chart.data.labels = historial_convergencia.map((_, i) => i + 1);
    state.chart.data.datasets[0].data = historial_convergencia;
    state.chart.update();

    // 4. Dibujar en el mapa Leaflet
    clearMap();

    // Trazar polilínea con efecto resplandor
    // Capa exterior de glow
    L.polyline(geometria_ruta, {
        color: "#38bdf8",
        weight: 8,
        opacity: 0.35,
        lineCap: "round",
        lineJoin: "round"
    }).addTo(state.routesLayer);

    // Capa interior nítida
    const mainLine = L.polyline(geometria_ruta, {
        color: "#00f2fe",
        weight: 4,
        opacity: 0.95,
        lineCap: "round",
        lineJoin: "round"
    }).addTo(state.routesLayer);

    // Ajustar el mapa al trazado completo
    state.map.fitBounds(mainLine.getBounds(), { padding: [50, 50] });

    // Agregar marcadores numerados estilo Liquid Glass
    secuencia.forEach((item) => {
        let colorFondo = "#6366f1";
        let colorBorde = "#818cf8";

        if (item.es_origen) {
            colorFondo = "#10b981";
            colorBorde = "#34d399";
        } else if (item.es_retorno) {
            return; // Ya dibujamos el origen
        }

        const iconHtml = `
            <div style="
                width: 26px;
                height: 26px;
                border-radius: 50%;
                background: ${colorFondo};
                border: 2px solid ${colorBorde};
                box-shadow: 0 4px 12px rgba(0,0,0,0.6);
                display: flex;
                align-items: center;
                justify-content: center;
                color: #ffffff;
                font-weight: 800;
                font-size: 11px;
                letter-spacing: -0.5px;
            ">
                ${item.paso}
            </div>
        `;

        const customIcon = L.divIcon({
            html: iconHtml,
            className: "liquid-marker",
            iconSize: [26, 26],
            iconAnchor: [13, 13]
        });

        const popupHtml = `
            <div style="font-family: inherit; font-size: 12px; color: #f8fafc; background: #0f131d; padding: 6px 10px; border-radius: 8px;">
                <div style="font-size: 10px; text-transform: uppercase; color: #94a3b8; font-weight: 700;">
                    ${item.es_origen ? "Punto de Partida" : `Parada #${item.paso}`}
                </div>
                <div style="font-weight: 600; color: #38bdf8; margin-top: 2px;">
                    ${item.nombre}
                </div>
            </div>
        `;

        L.marker([item.lat, item.lon], { icon: customIcon })
            .bindPopup(popupHtml, { closeButton: false, className: "glass-popup" })
            .addTo(state.markersLayer);
    });
}

function clearMap() {
    state.routesLayer.clearLayers();
    state.markersLayer.clearLayers();
}

function resetStats() {
    document.getElementById("statTiempoAco").innerHTML = `-- <small>min</small>`;
    document.getElementById("statTiempoOrig").innerHTML = `-- <small>min</small>`;
    document.getElementById("statMejoraPct").textContent = `--%`;
    document.getElementById("statAhorroMin").textContent = `-- min ahorrados`;
    document.getElementById("statDistancia").innerHTML = `-- <small>km</small>`;
    document.getElementById("itineraryList").innerHTML = `<div class="empty-state">Presiona "Calcular Ruta Óptima" para visualizar el orden y trazado.</div>`;
    
    if (state.chart) {
        state.chart.data.labels = [];
        state.chart.data.datasets[0].data = [];
        state.chart.update();
    }
}

/* ==========================================================================
   UTILIDADES: LOADER, TOAST Y STATUS
   ========================================================================== */
function showLoader(show, text = "") {
    const overlay = document.getElementById("loaderOverlay");
    const desc = document.getElementById("loaderStatusText");
    if (text) desc.textContent = text;
    overlay.style.display = show ? "flex" : "none";
}

let toastTimer = null;
function showToast(msg, icon = "ℹ️") {
    const toast = document.getElementById("glassToast");
    const msgEl = document.getElementById("toastMessage");
    const iconEl = toast.querySelector(".toast-icon");

    iconEl.textContent = icon;
    msgEl.textContent = msg;

    toast.classList.add("show");
    if (toastTimer) clearTimeout(toastTimer);
    toastTimer = setTimeout(() => {
        toast.classList.remove("show");
    }, 4000);
}

async function checkApiStatus() {
    try {
        const res = await fetch("/api/status");
        const data = await res.json();
        const badge = document.getElementById("apiStatusBadge");
        if (data.api_key_configurada) {
            badge.style.background = "rgba(16, 185, 129, 0.12)";
            badge.style.color = "#34d399";
            badge.querySelector(".status-text").textContent = "ORS Conectado";
        } else {
            badge.style.background = "rgba(244, 63, 94, 0.12)";
            badge.style.color = "#fb7185";
            badge.querySelector(".status-text").textContent = "Sin API Key en .env";
        }
    } catch (_) {}
}
