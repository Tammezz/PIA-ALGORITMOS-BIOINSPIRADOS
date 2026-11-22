"""
app.py - Interfaz Web en Streamlit con estilo Liquid Glass Black

Optimizador de rutas tipo Google Maps utilizando el algoritmo de Colonia de Hormigas (ACO)
y la API de OpenRouteService con datos viales reales.
"""

import os
import time
import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from streamlit_folium import st_folium
from dotenv import load_dotenv

from ors_client import (
    geocodificar_lugar,
    obtener_matriz_tiempos,
    obtener_ruta_real,
    obtener_api_key,
    ORSError,
)
from aco import resolver_tsp_aco, calcular_costo_ruta
from mapa import crear_mapa_ruta

# Cargar variables del entorno (.env)
load_dotenv()

# Configuración general de la página en Streamlit
st.set_page_config(
    page_title="ACO Maps - Liquid Glass Route Optimizer",
    page_icon="🐜",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =============================================================================
# ESTILOS CSS - TEMA "LIQUID GLASS BLACK"
# =============================================================================
CSS_LIQUID_GLASS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');

/* Fondo general y tipografía */
html, body, [data-testid="stAppViewContainer"] {
    background-color: #07090e !important;
    background-image: 
        radial-gradient(at 0% 0%, rgba(30, 41, 59, 0.5) 0px, transparent 50%),
        radial-gradient(at 100% 100%, rgba(15, 23, 42, 0.6) 0px, transparent 50%);
    font-family: 'Plus Jakarta Sans', -apple-system, sans-serif !important;
    color: #f1f5f9 !important;
}

/* Ocultar barra superior genérica de Streamlit */
header[data-testid="stHeader"] {
    background: transparent !important;
}

/* Sidebar translúcida Liquid Glass */
[data-testid="stSidebar"] {
    background: rgba(13, 17, 26, 0.72) !important;
    backdrop-filter: blur(24px) saturate(160%) !important;
    -webkit-backdrop-filter: blur(24px) saturate(160%) !important;
    border-right: 1px solid rgba(255, 255, 255, 0.08) !important;
    box-shadow: 10px 0 30px rgba(0, 0, 0, 0.6) !important;
}

/* Tarjetas contenedoras Liquid Glass */
.glass-panel {
    background: rgba(18, 23, 34, 0.62) !important;
    backdrop-filter: blur(20px) saturate(180%) !important;
    -webkit-backdrop-filter: blur(20px) saturate(180%) !important;
    border: 1px solid rgba(255, 255, 255, 0.09) !important;
    border-top: 1px solid rgba(255, 255, 255, 0.22) !important;
    border-radius: 20px !important;
    padding: 22px !important;
    box-shadow: 0 12px 36px 0 rgba(0, 0, 0, 0.45), inset 0 1px 0 0 rgba(255, 255, 255, 0.15) !important;
    margin-bottom: 20px !important;
    transition: transform 0.2s ease, border-color 0.2s ease;
}

.glass-panel:hover {
    border-color: rgba(56, 189, 248, 0.35) !important;
}

/* Píldoras y badges */
.glass-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 4px 12px;
    border-radius: 9999px;
    background: rgba(255, 255, 255, 0.06);
    border: 1px solid rgba(255, 255, 255, 0.12);
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 0.5px;
    color: #38bdf8;
}

/* Título principal con brillo de texto */
.brand-title {
    font-size: 28px;
    font-weight: 800;
    letter-spacing: -0.5px;
    background: linear-gradient(135deg, #ffffff 40%, #94a3b8 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 4px;
}

.brand-subtitle {
    font-size: 13px;
    color: #64748b;
    margin-bottom: 16px;
}

/* Métricas en formato Glass Card */
.metric-container {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 14px;
    margin-bottom: 20px;
}

.metric-card {
    background: rgba(18, 23, 34, 0.65);
    backdrop-filter: blur(16px);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-top: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 16px;
    padding: 16px 20px;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.35);
}

.metric-label {
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: #94a3b8;
}

.metric-value {
    font-size: 24px;
    font-weight: 800;
    color: #ffffff;
    margin-top: 4px;
}

.metric-delta {
    font-size: 12px;
    font-weight: 600;
    margin-top: 2px;
}

.delta-good {
    color: #10b981;
}

.delta-neutral {
    color: #38bdf8;
}

/* Botones con estilo Liquid Glass Pill */
.stButton > button {
    width: 100% !important;
    background: linear-gradient(180deg, rgba(255, 255, 255, 0.15) 0%, rgba(255, 255, 255, 0.05) 100%) !important;
    background-color: rgba(30, 41, 59, 0.8) !important;
    color: #f8fafc !important;
    border: 1px solid rgba(255, 255, 255, 0.2) !important;
    border-top: 1px solid rgba(255, 255, 255, 0.4) !important;
    border-radius: 9999px !important;
    padding: 10px 24px !important;
    font-weight: 600 !important;
    letter-spacing: 0.3px !important;
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.3) !important;
    backdrop-filter: blur(12px) !important;
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
}

.stButton > button:hover {
    background-color: rgba(56, 189, 248, 0.25) !important;
    border-color: rgba(56, 189, 248, 0.6) !important;
    box-shadow: 0 8px 25px rgba(56, 189, 248, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.5) !important;
    transform: translateY(-1px) !important;
}

/* Campos de entrada y textarea */
.stTextArea textarea, .stTextInput input {
    background: rgba(13, 17, 26, 0.6) !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    border-radius: 14px !important;
    color: #f1f5f9 !important;
    backdrop-filter: blur(10px) !important;
}

.stTextArea textarea:focus, .stTextInput input:focus {
    border-color: #38bdf8 !important;
    box-shadow: 0 0 0 2px rgba(56, 189, 248, 0.2) !important;
}

/* Contenedor del mapa en Folium */
[data-testid="stCustomComponentV1"] {
    border-radius: 20px !important;
    overflow: hidden !important;
    border: 1px solid rgba(255, 255, 255, 0.12) !important;
    box-shadow: 0 16px 40px rgba(0, 0, 0, 0.6) !important;
}
</style>
"""

st.markdown(CSS_LIQUID_GLASS, unsafe_allow_html=True)


# =============================================================================
# DATOS POR DEFECTO: MONTERREY, N.L.
# =============================================================================
LUGARES_DEFAULT_MTY = """Macroplaza, Monterrey
Parque Fundidora, Monterrey
El Obispado, Monterrey
Tecnologico de Monterrey, Monterrey
San Pedro Garza Garcia, Nuevo Leon
Basilica de Guadalupe, Monterrey"""


# =============================================================================
# BARRA LATERAL (SIDEBAR)
# =============================================================================
with st.sidebar:
    st.markdown('<div class="brand-title">🐜 ACO Maps</div>', unsafe_allow_html=True)
    st.markdown('<div class="brand-subtitle">Optimización por Colonia de Hormigas · Liquid Glass Edition</div>', unsafe_allow_html=True)

    # Verificación de API Key
    api_key_existente = os.getenv("ORS_API_KEY", "").strip()
    if not api_key_existente or api_key_existente == "tu_api_key_aqui":
        st.warning("⚠️ Sin llave en `.env`. Ingresa tu clave temporal abajo:")
        api_key_manual = st.text_input("OpenRouteService API Key", type="password")
        if api_key_manual:
            os.environ["ORS_API_KEY"] = api_key_manual.strip()
            api_key_existente = api_key_manual.strip()
    else:
        st.markdown('<span class="glass-badge">✓ ORS API Key Conectada</span>', unsafe_allow_html=True)

    st.markdown("<hr style='border-color: rgba(255,255,255,0.08); margin: 16px 0;'>", unsafe_allow_html=True)

    st.markdown("### 📍 Puntos de Ruta")
    st.caption("Escribe un lugar por línea (nombre o coordenadas `lat, lon`). El punto 1 es el origen.")

    lugares_texto = st.text_area(
        label="Lista de ubicaciones",
        value=LUGARES_DEFAULT_MTY,
        height=160,
        help="Máximo 25 puntos según el límite de la API gratuita de OpenRouteService.",
    )

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        regresar_inicio = st.checkbox("Regresar al inicio", value=True, help="Si se activa, la ruta forma un circuito cerrado de vuelta al punto 1.")
    with col_btn2:
        usar_semilla = st.checkbox("Fijar semilla", value=True, help="Permite reproducir exactamente los mismos resultados.")

    semilla_val = 42
    if usar_semilla:
        semilla_val = st.number_input("Valor de semilla", min_value=0, max_value=99999, value=42, step=1)

    # Acordeón de Parámetros ACO
    with st.expander("⚙️ Parámetros del Algoritmo ACO", expanded=False):
        n_hormigas = st.slider("Hormigas exploradoras", min_value=5, max_value=50, value=15, step=1)
        epocas = st.slider("Épocas de iteración", min_value=20, max_value=300, value=100, step=10)
        evaporacion = st.slider("Tasa de evaporación (ρ)", min_value=0.05, max_value=0.95, value=0.40, step=0.05)
        alfa = st.slider("Peso de feromona (α)", min_value=0.0, max_value=5.0, value=1.0, step=0.1)
        beta = st.slider("Peso de visibilidad / costo (β)", min_value=0.5, max_value=6.0, value=2.0, step=0.1)
        q = st.slider("Factor de depósito Q", min_value=10.0, max_value=500.0, value=100.0, step=10.0)

    st.markdown("<br>", unsafe_allow_html=True)
    ejecutar = st.button("🚀 Calcular Ruta Óptima")


# =============================================================================
# ÁREA PRINCIPAL
# =============================================================================
st.markdown("""
<div class="glass-panel" style="margin-bottom: 24px;">
    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">
        <div>
            <h1 style="font-size: 24px; font-weight: 700; margin: 0; color: #ffffff;">
                🗺️ Optimizador de Rutas Vehiculares con ACO
            </h1>
            <p style="color: #94a3b8; font-size: 13px; margin: 4px 0 0 0;">
                Datos viales en tiempo real vía OpenRouteService · Monterrey y México
            </p>
        </div>
        <div>
            <span class="glass-badge">Metaheurística Bioinspirada</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)


# Parsear las líneas de lugares
lineas_raw = [line.strip() for line in lugares_texto.split("\n") if line.strip()]

if len(lineas_raw) > 25:
    st.error(
        f"🚨 Límite excedido: Ingresaste {len(lineas_raw)} lugares. "
        "El plan gratuito de OpenRouteService permite hasta 25 puntos para evitar sobrecostos o bloqueos."
    )
elif len(lineas_raw) < 2:
    st.info("👋 Por favor ingresa al menos 2 ubicaciones en la barra lateral para trazar una ruta.")
else:
    # Si el usuario presiona el botón o ya tenemos resultados en sesión
    if ejecutar or "ultimo_resultado" in st.session_state:
        if ejecutar:
            # Limpiar estado previo
            st.session_state.pop("ultimo_resultado", None)

            with st.spinner("⏳ Conectando con OpenRouteService: geocodificando y calculando matriz de tiempos..."):
                try:
                    # 1. Geocodificación de cada punto
                    lugares_info = []
                    coords_ors = []
                    for lin in lineas_raw:
                        info = geocodificar_lugar(lin)
                        lugares_info.append(info)
                        coords_ors.append(info["coords_ors"])

                    # 2. Matriz de tiempos con caché
                    matriz_duraciones = obtener_matriz_tiempos(coords_ors)

                    # 3. Costo del orden original (sin optimizar)
                    n_nodos = len(lugares_info)
                    ruta_original_indices = list(range(n_nodos))
                    if regresar_inicio:
                        ruta_original_indices.append(0)
                    costo_seg_original = calcular_costo_ruta(ruta_original_indices, matriz_duraciones)

                    # 4. Ejecución del Algoritmo de Colonia de Hormigas (ACO)
                    mejor_ruta_indices, mejor_costo_seg, historial_conv = resolver_tsp_aco(
                        matriz_costos=matriz_duraciones,
                        n_hormigas=n_hormigas,
                        epocas=epocas,
                        evaporacion=evaporacion,
                        alfa=alfa,
                        beta=beta,
                        q=q,
                        regresar_al_origen=regresar_inicio,
                        semilla=semilla_val if usar_semilla else None,
                    )

                    # 5. Obtención de la ruta real trazada por calles de ORS
                    coords_ordenadas_ors = [coords_ors[idx] for idx in mejor_ruta_indices]
                    ruta_real_geojson = obtener_ruta_real(coords_ordenadas_ors)

                    # Guardar resultados en el session_state
                    st.session_state["ultimo_resultado"] = {
                        "lugares_info": lugares_info,
                        "mejor_ruta_indices": mejor_ruta_indices,
                        "costo_seg_original": costo_seg_original,
                        "mejor_costo_seg": mejor_costo_seg,
                        "historial_conv": historial_conv,
                        "ruta_real": ruta_real_geojson,
                        "regresar_inicio": regresar_inicio,
                    }

                except ORSError as err:
                    st.error(f"❌ {str(err)}")
                except Exception as ex:
                    st.error(f"❌ Ocurrió un error inesperado: {str(ex)}")

        # Renderizar resultados si existen
        if "ultimo_resultado" in st.session_state:
            res = st.session_state["ultimo_resultado"]
            lugares_info = res["lugares_info"]
            mejor_ruta_indices = res["mejor_ruta_indices"]
            costo_seg_original = res["costo_seg_original"]
            mejor_costo_seg = res["mejor_costo_seg"]
            historial_conv = res["historial_conv"]
            ruta_real = res["ruta_real"]
            regresar_inicio_val = res["regresar_inicio"]

            # Cálculos de comparación
            min_original = costo_seg_original / 60.0
            min_aco = mejor_costo_seg / 60.0
            ahorro_min = max(0.0, min_original - min_aco)
            porcentaje_mejora = (ahorro_min / min_original * 100.0) if min_original > 0 else 0.0

            distancia_km = ruta_real["distancia_km"]
            duracion_real_min = ruta_real["duracion_min"]

            # Puntos ordenados para el mapa
            puntos_ordenados = []
            for idx in mejor_ruta_indices:
                puntos_ordenados.append(lugares_info[idx])

            # Métricas en Glass Cards
            st.markdown(f"""
            <div class="metric-container">
                <div class="metric-card">
                    <div class="metric-label">Tiempo ACO (Optimizado)</div>
                    <div class="metric-value">{min_aco:.1f} <span style="font-size:14px; font-weight:400; color:#94a3b8;">min</span></div>
                    <div class="metric-delta delta-good">✓ Ruta más rápida</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Tiempo Original (Usuario)</div>
                    <div class="metric-value">{min_original:.1f} <span style="font-size:14px; font-weight:400; color:#94a3b8;">min</span></div>
                    <div class="metric-delta delta-neutral">Sin optimizar</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Mejora / Ahorro</div>
                    <div class="metric-value">{porcentaje_mejora:.1f}%</div>
                    <div class="metric-delta delta-good">-{ahorro_min:.1f} min ahorrados</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Distancia Real por Calles</div>
                    <div class="metric-value">{distancia_km:.1f} <span style="font-size:14px; font-weight:400; color:#94a3b8;">km</span></div>
                    <div class="metric-delta delta-neutral">Tráfico y sentidos reales</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Columnas: Mapa interactivo (izquierda) y Secuencia + Gráfica (derecha)
            col_mapa, col_info = st.columns([1.5, 1.0])

            with col_mapa:
                st.markdown("""
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 8px;">
                    <span style="font-weight:700; font-size:15px; color:#f8fafc;">📍 Mapa Interactivo de Rutas Reales</span>
                    <span class="glass-badge">Folium + OpenRouteService</span>
                </div>
                """, unsafe_allow_html=True)

                # Generar mapa con folium
                mapa_obj = crear_mapa_ruta(
                    puntos_ordenados=puntos_ordenados,
                    coordenadas_geometria_folium=ruta_real["folium_coords"],
                    regresar_al_origen=regresar_inicio_val,
                    estilo_oscuro=True,
                )
                st_folium(mapa_obj, width="100%", height=500, returned_objects=[])

            with col_info:
                # Tarjeta de Orden Óptimo
                st.markdown("""
                <div class="glass-panel" style="padding: 16px; margin-bottom: 16px;">
                    <div style="font-weight:700; font-size:14px; color:#38bdf8; margin-bottom: 10px;">
                        🎯 Secuencia de Visita Óptima:
                    </div>
                """, unsafe_allow_html=True)

                for step_num, idx in enumerate(mejor_ruta_indices, start=1):
                    nombre = lugares_info[idx]["nombre"]
                    es_retorno = (step_num == len(mejor_ruta_indices) and regresar_inicio_val and step_num > 1)
                    
                    if step_num == 1:
                        badge_color = "#10b981"
                        texto_badge = "1. Origen"
                    elif es_retorno:
                        badge_color = "#38bdf8"
                        texto_badge = f"{step_num}. Fin (Regreso)"
                    else:
                        badge_color = "#818cf8"
                        texto_badge = f"{step_num}. Parada"

                    st.markdown(f"""
                    <div style="display:flex; align-items:center; gap:10px; margin-bottom:6px; font-size:13px;">
                        <span style="background:{badge_color}; color:#ffffff; padding:2px 8px; border-radius:999px; font-weight:700; font-size:11px;">
                            {texto_badge}
                        </span>
                        <span style="color:#e2e8f0; font-weight:500; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">
                            {nombre}
                        </span>
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown("</div>", unsafe_allow_html=True)

                # Gráfica de Convergencia con Matplotlib estilizada para Liquid Glass
                st.markdown("""
                <div class="glass-panel" style="padding: 16px;">
                    <div style="font-weight:700; font-size:14px; color:#f8fafc; margin-bottom: 6px;">
                        📉 Convergencia del Algoritmo ACO
                    </div>
                    <div style="font-size:11px; color:#94a3b8; margin-bottom: 12px;">
                        Evolución del mejor tiempo encontrado a lo largo de las épocas
                    </div>
                """, unsafe_allow_html=True)

                fig, ax = plt.subplots(figsize=(5, 3), dpi=150)
                fig.patch.set_facecolor("#0b0e14")
                ax.set_facecolor("#111520")

                tiempos_minutos = [c / 60.0 for c in historial_conv]
                ax.plot(
                    range(1, len(tiempos_minutos) + 1),
                    tiempos_minutos,
                    color="#00f2fe",
                    linewidth=2.2,
                    label="Mejor Costo (min)",
                )

                ax.set_xlabel("Época", color="#94a3b8", fontsize=9)
                ax.set_ylabel("Duración (minutos)", color="#94a3b8", fontsize=9)
                ax.tick_params(colors="#64748b", labelsize=8)
                ax.grid(True, linestyle="--", alpha=0.15, color="#cbd5e1")
                for spine in ax.spines.values():
                    spine.set_color("#1e293b")

                ax.legend(facecolor="#111520", edgecolor="#1e293b", labelcolor="#cbd5e1", fontsize=8)
                plt.tight_layout()

                st.pyplot(fig)
                plt.close(fig)
                st.markdown("</div>", unsafe_allow_html=True)
