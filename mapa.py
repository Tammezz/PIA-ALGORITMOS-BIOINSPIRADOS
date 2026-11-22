"""
mapa.py - Generación y visualización del mapa interactivo con Folium

Renderiza la ruta óptima sobre las calles reales, añade marcadores numerados
para cada parada y aplica una estética moderna acorde al estilo Liquid Glass Black.
"""

from typing import List, Dict, Any, Tuple
import folium


def crear_mapa_ruta(
    puntos_ordenados: List[Dict[str, Any]],
    coordenadas_geometria_folium: List[List[float]],
    regresar_al_origen: bool = True,
    estilo_oscuro: bool = True,
) -> folium.Map:
    """
    Construye un mapa Folium interactivo centrado en los puntos de la ruta.

    Parámetros:
    -----------
    puntos_ordenados : List[Dict[str, Any]]
        Lista de lugares en el orden óptimo de visita determinado por ACO.
        Cada elemento contiene 'nombre', 'lat', 'lon'.
    coordenadas_geometria_folium : List[List[float]]
        Secuencia de coordenadas [lat, lon] que componen el trazo real por calles de ORS.
    regresar_al_origen : bool
        Indica si la ruta regresa al inicio.
    estilo_oscuro : bool
        Si es True, el tema oscuro se aplica con filtros CSS sobre OpenStreetMap.
        La fuente cartográfica es siempre OSM: sin llaves ni marcas de agua.

    Retorna:
    --------
    folium.Map : Objeto de mapa interactivo listo para renderizar en Streamlit.
    """
    if not puntos_ordenados:
        # Mapa por defecto centrado en Monterrey
        return folium.Map(location=[25.67, -100.31], zoom_start=12)

    # Calcular centro geográfico promedio
    centro_lat = sum(p["lat"] for p in puntos_ordenados) / len(puntos_ordenados)
    centro_lon = sum(p["lon"] for p in puntos_ordenados) / len(puntos_ordenados)

    # OpenStreetMap: 100% libre, sin cuentas ni marcas de agua.
    mapa = folium.Map(
        location=[centro_lat, centro_lon],
        zoom_start=12,
        tiles="OpenStreetMap",
        attr="© OpenStreetMap contributors",
        control_scale=True,
    )

    # 1. Trazar la polilínea con la geometría real de las calles
    if coordenadas_geometria_folium:
        # Línea de brillo exterior (glow effect para liquid glass)
        folium.PolyLine(
            locations=coordenadas_geometria_folium,
            color="#38bdf8",
            weight=8,
            opacity=0.35,
        ).add_to(mapa)

        # Línea central nítida (cyan eléctrico neón)
        folium.PolyLine(
            locations=coordenadas_geometria_folium,
            color="#00f2fe",
            weight=4,
            opacity=0.95,
            tooltip="Ruta óptima calculada (calles reales)",
        ).add_to(mapa)

    # 2. Agregar marcadores numerados para cada punto en el orden óptimo
    total_puntos = len(puntos_ordenados)
    for idx, punto in enumerate(puntos_ordenados):
        es_origen = (idx == 0)
        es_destino_final = (idx == total_puntos - 1) and not regresar_al_origen

        # Colores y estilo de marcador
        if es_origen:
            color_fondo = "#10b981"  # Verde esmeralda para inicio
            borde_color = "#34d399"
            icono_texto = "1"
            rol = "Origen / Inicio"
        elif es_destino_final:
            color_fondo = "#f43f5e"  # Rojo carmín para final en ruta abierta
            borde_color = "#fb7185"
            icono_texto = str(idx + 1)
            rol = "Destino Final"
        else:
            color_fondo = "#6366f1"  # Azul índigo para paradas intermedias
            borde_color = "#818cf8"
            icono_texto = str(idx + 1)
            rol = f"Parada #{idx + 1}"

        html_popup = f"""
        <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    background: #11141d; color: #f8fafc; padding: 10px; border-radius: 10px;
                    border: 1px solid rgba(255,255,255,0.15); min-width: 170px;">
            <div style="font-size: 11px; text-transform: uppercase; letter-spacing: 1px; color: #94a3b8;">
                {rol}
            </div>
            <div style="font-size: 14px; font-weight: 600; margin-top: 3px; color: #38bdf8;">
                {punto['nombre']}
            </div>
            <div style="font-size: 11px; color: #cbd5e1; margin-top: 6px;">
                Coordenadas: {punto['lat']:.4f}, {punto['lon']:.4f}
            </div>
        </div>
        """

        # Marcador circular personalizado tipo Liquid Glass
        folium.CircleMarker(
            location=[punto["lat"], punto["lon"]],
            radius=12,
            color=borde_color,
            weight=2,
            fill=True,
            fill_color=color_fondo,
            fill_opacity=0.9,
            tooltip=f"{idx + 1}. {punto['nombre']}",
            popup=folium.Popup(html_popup, max_width=280),
        ).add_to(mapa)

        # Añadimos el número dentro del marcador usando un DivIcon
        folium.Marker(
            location=[punto["lat"], punto["lon"]],
            icon=folium.DivIcon(
                icon_size=(24, 24),
                icon_anchor=(12, 12),
                html=f"""
                <div style="
                    font-size: 11px;
                    font-weight: 700;
                    color: white;
                    text-align: center;
                    line-height: 24px;
                    text-shadow: 0 1px 2px rgba(0,0,0,0.8);
                    pointer-events: none;
                ">
                    {icono_texto}
                </div>
                """,
            ),
        ).add_to(mapa)

    # Ajustar vista a los límites de los puntos o geometría
    if coordenadas_geometria_folium:
        mapa.fit_bounds(coordenadas_geometria_folium)
    elif puntos_ordenados:
        bounds = [[p["lat"], p["lon"]] for p in puntos_ordenados]
        mapa.fit_bounds(bounds)

    return mapa
