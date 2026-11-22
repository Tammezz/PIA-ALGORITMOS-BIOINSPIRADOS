"""
ors_client.py - Cliente para la API de OpenRouteService (ORS) con caché en disco

Gestiona la autenticación, geocodificación de lugares, obtención de la matriz de tiempos,
cálculo de la ruta geométrica real y almacenamiento en caché para proteger la cuota gratuita.
"""

import os
import re
import json
import hashlib
from typing import List, Dict, Any, Tuple, Optional
import requests
import numpy as np
from dotenv import load_dotenv

# Cargar variables de entorno desde el archivo .env
load_dotenv()

BASE_URL = "https://api.openrouteservice.org"
CACHE_DIR = ".cache"


class ORSError(Exception):
    """Excepción personalizada para errores amigables de OpenRouteService."""
    pass


def obtener_api_key() -> str:
    """Obtiene y valida la existencia de la API key de OpenRouteService en el entorno."""
    api_key = os.getenv("ORS_API_KEY", "").strip()
    if not api_key or api_key == "tu_api_key_aqui":
        raise ORSError(
            "No se encontró una API Key válida de OpenRouteService. "
            "Por favor crea o edita el archivo .env y asigna tu llave a la variable ORS_API_KEY."
        )
    return api_key


def _manejar_error_respuesta(response: requests.Response, contexto: str = ""):
    """Analiza los códigos de estado HTTP y genera mensajes de error claros en español."""
    status = response.status_code
    if status == 401 or status == 403:
        raise ORSError(
            f"Error de autenticación ({status}): La clave de OpenRouteService es inválida o no tiene permisos. "
            "Revisa tu archivo .env."
        )
    elif status == 429:
        raise ORSError(
            "Límite de solicitudes alcanzado (Error 429: Rate limit exceeded). "
            "Has superado el límite gratuito de OpenRouteService. Espera unos momentos antes de reintentar."
        )
    elif status >= 500:
        raise ORSError(
            f"El servidor de OpenRouteService tuvo un problema interno ({status}). "
            "Por favor inténtalo de nuevo en unos minutos."
        )
    elif status >= 400:
        try:
            detalle = response.json().get("error", {}).get("message", response.text)
        except Exception:
            detalle = response.text
        raise ORSError(f"Error en {contexto} ({status}): {detalle}")


def es_coordenada_numerica(texto: str) -> Optional[Tuple[float, float]]:
    """
    Verifica si el texto ingresado tiene formato 'lat, lon'.
    Retorna (latitud, longitud) como tupla de floats o None si no coincide.
    """
    patron = r"^\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*$"
    match = re.match(patron, texto.strip())
    if match:
        lat = float(match.group(1))
        lon = float(match.group(2))
        # Validar rangos geográficos básicos
        if -90 <= lat <= 90 and -180 <= lon <= 180:
            return lat, lon
    return None


def geocodificar_lugar(texto: str, api_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Convierte el nombre de un lugar o coordenadas en datos geográficos.
    Sesgo configurado hacia Monterrey, México (focus.point.lat=25.67, focus.point.lon=-100.31).

    Retorna un diccionario:
    {
        "nombre": str,
        "lat": float,
        "lon": float,
        "coords_ors": [lon, lat]  # Formato que exige la API de OpenRouteService
    }
    """
    texto = texto.strip()
    if not texto:
        raise ORSError("Se proporcionó una línea vacía como ubicación.")

    # Si el usuario escribió directamente coordenadas "lat, lon", evitamos gastar cuota de la API
    coords_directas = es_coordenada_numerica(texto)
    if coords_directas:
        lat, lon = coords_directas
        return {
            "nombre": f"Punto ({lat:.4f}, {lon:.4f})",
            "lat": lat,
            "lon": lon,
            # IMPORTANTE: OpenRouteService siempre usa [longitud, latitud]
            "coords_ors": [lon, lat],
        }

    if api_key is None:
        api_key = obtener_api_key()

    url = f"{BASE_URL}/geocode/search"
    headers = {"Authorization": api_key}
    params = {
        "text": texto,
        "size": 15,  # Pedimos múltiples candidatos para seleccionar el más relevante geográficamente
        "boundary.country": "MX",
        "focus.point.lat": 25.67,
        "focus.point.lon": -100.31,
    }

    try:
        response = requests.get(url, headers=headers, params=params, timeout=12)
    except requests.exceptions.ConnectionError:
        raise ORSError("Sin conexión a internet. No se pudo conectar con el servicio de geocodificación.")
    except requests.exceptions.Timeout:
        raise ORSError("El servicio de geocodificación tardó demasiado en responder (Tiempo de espera agotado).")

    if response.status_code != 200:
        _manejar_error_respuesta(response, f"geocodificación de '{texto}'")

    data = response.json()
    features = data.get("features", [])
    if not features:
        raise ORSError(f"No se encontró ninguna ubicación para: '{texto}'. Intenta agregar 'Monterrey' o ser más específico.")

    # Selección inteligente del mejor candidato:
    # 1. Si el texto menciona Monterrey / Nuevo León, priorizar candidatos de esa región
    texto_lower = texto.lower()
    es_busqueda_mty = any(palabra in texto_lower for palabra in [
        "monterrey", "mty", "san pedro", "guadalupe", "santa catarina",
        "san nicolas", "escobedo", "apodaca", "nuevo leon", "nle"
    ])

    candidatos = features
    if es_busqueda_mty:
        filtrados_mty = [
            f for f in features
            if any(term in f.get("properties", {}).get("label", "").lower() for term in ["nuevo león", "nle", "monterrey", "garza garcia", "guadalupe", "san nicolas"])
        ]
        if filtrados_mty:
            candidatos = filtrados_mty

    # 2. Elegir el candidato más cercano al foco geográfico (evita enviar a Pachuca o Torreón)
    def dist_foco(f):
        c = f["geometry"]["coordinates"]  # [lon, lat]
        return (c[1] - 25.67) ** 2 + (c[0] - (-100.31)) ** 2

    feat = min(candidatos, key=dist_foco)
    coords = feat["geometry"]["coordinates"]  # [longitud, latitud]
    lon, lat = coords[0], coords[1]
    label = feat.get("properties", {}).get("label", texto)

    return {
        "nombre": label,
        "lat": lat,
        "lon": lon,
        # IMPORTANTE: OpenRouteService siempre usa [longitud, latitud]
        "coords_ors": [lon, lat],
    }


def autocompletar_lugares(texto: str, api_key: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Entrega sugerencias de autocompletado en tiempo real mientras el usuario escribe.
    Sesgo enfocado hacia Monterrey y México.
    """
    texto = texto.strip()
    if not texto or len(texto) < 2:
        return []

    # Si es coordenada directa, no autocompletar en la API
    if es_coordenada_numerica(texto):
        return []

    if api_key is None:
        api_key = obtener_api_key()

    url = f"{BASE_URL}/geocode/autocomplete"
    headers = {"Authorization": api_key}
    params = {
        "text": texto,
        "boundary.country": "MX",
        "focus.point.lat": 25.67,
        "focus.point.lon": -100.31,
    }

    try:
        response = requests.get(url, headers=headers, params=params, timeout=6)
        if response.status_code != 200:
            return []
        data = response.json()
        features = data.get("features", [])
        
        resultados = []
        for feat in features[:6]:
            coords = feat["geometry"]["coordinates"]
            label = feat.get("properties", {}).get("label", texto)
            resultados.append({
                "nombre": label,
                "lat": coords[1],
                "lon": coords[0],
                "coords_ors": [coords[0], coords[1]],
            })
        return resultados
    except Exception:
        return []


def geocodificar_inverso(lat: float, lon: float, api_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Obtiene el nombre de la calle o lugar a partir de coordenadas geográficas (al hacer clic en el mapa).
    """
    if api_key is None:
        api_key = obtener_api_key()

    url = f"{BASE_URL}/geocode/reverse"
    headers = {"Authorization": api_key}
    params = {
        "point.lat": lat,
        "point.lon": lon,
        "size": 1,
    }

    try:
        response = requests.get(url, headers=headers, params=params, timeout=8)
        if response.status_code == 200:
            data = response.json()
            features = data.get("features", [])
            if features:
                label = features[0].get("properties", {}).get("label", f"Punto ({lat:.4f}, {lon:.4f})")
                return {
                    "nombre": label,
                    "lat": lat,
                    "lon": lon,
                    "coords_ors": [lon, lat],
                }
    except Exception:
        pass

    # Fallback si no hay conexión o no hay respuesta
    return {
        "nombre": f"Punto ({lat:.4f}, {lon:.4f})",
        "lat": lat,
        "lon": lon,
        "coords_ors": [lon, lat],
    }


def obtener_matriz_tiempos(coords_ors: List[List[float]], api_key: Optional[str] = None) -> np.ndarray:
    """
    Obtiene la matriz de tiempos de conducción en segundos entre todos los puntos.
    Utiliza caché en disco (.cache/) para evitar consumir la cuota de la API al repetir puntos.

    Parámetros:
    -----------
    coords_ors : List[List[float]]
        Lista de coordenadas en formato [[lon, lat], [lon, lat], ...]
    """
    if len(coords_ors) > 25:
        raise ORSError(
            f"El plan gratuito de OpenRouteService permite un máximo de 25 puntos por consulta. "
            f"Ingresaste {len(coords_ors)} puntos."
        )
    if len(coords_ors) < 2:
        raise ORSError("Se requieren al menos 2 puntos para calcular una ruta.")

    # 1. Comprobar caché local en disco mediante Hash SHA-256
    os.makedirs(CACHE_DIR, exist_ok=True)
    coords_str = json.dumps(coords_ors, sort_keys=True)
    hash_key = hashlib.sha256(coords_str.encode("utf-8")).hexdigest()
    cache_path = os.path.join(CACHE_DIR, f"matrix_{hash_key}.json")

    if os.path.exists(cache_path):
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                matriz = json.load(f)
                return np.array(matriz, dtype=float)
        except Exception:
            # Si el caché se corrompió, continuamos consultando la API
            pass

    # 2. Consultar API OpenRouteService
    if api_key is None:
        api_key = obtener_api_key()

    url = f"{BASE_URL}/v2/matrix/driving-car"
    headers = {
        "Authorization": api_key,
        "Content-Type": "application/json",
    }
    payload = {
        "locations": coords_ors,
        "metrics": ["duration"],
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=20)
    except requests.exceptions.ConnectionError:
        raise ORSError("Sin conexión a internet. No se pudo consultar la matriz de tiempos de OpenRouteService.")
    except requests.exceptions.Timeout:
        raise ORSError("La consulta de la matriz de tiempos tardó demasiado en responder.")

    if response.status_code != 200:
        _manejar_error_respuesta(response, "matriz de tiempos")

    data = response.json()
    duraciones = data.get("durations", [])

    if not duraciones:
        raise ORSError("OpenRouteService no devolvió la matriz de duraciones esperada.")

    # Validar si existen valores nulos (cuando un punto no tiene conexión vial con otro)
    for i, fila in enumerate(duraciones):
        for j, valor in enumerate(fila):
            if valor is None:
                raise ORSError(
                    f"No existe una ruta vial transitable entre el punto {i + 1} y el punto {j + 1}. "
                    "Verifica que ambos lugares sean accesibles para vehículos."
                )

    # 3. Guardar en caché y retornar como array numpy
    try:
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(duraciones, f)
    except Exception:
        pass

    return np.array(duraciones, dtype=float)


def obtener_ruta_real(coords_ordenadas_ors: List[List[float]], api_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Obtiene la geometría real de las calles y el resumen (distancia y duración)
    para la secuencia ordenada de coordenadas.

    Retorna:
    {
        "distancia_km": float,
        "duracion_min": float,
        "duracion_seg": float,
        "folium_coords": List[Tuple[float, float]]  # Formato [(lat, lon), ...] para Folium
    }
    """
    if api_key is None:
        api_key = obtener_api_key()

    url = f"{BASE_URL}/v2/directions/driving-car/geojson"
    headers = {
        "Authorization": api_key,
        "Content-Type": "application/json",
    }
    payload = {
        "coordinates": coords_ordenadas_ors
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=25)
    except requests.exceptions.ConnectionError:
        raise ORSError("Sin conexión a internet. No se pudo obtener la ruta real por calles.")
    except requests.exceptions.Timeout:
        raise ORSError("El servicio de direcciones tardó demasiado en responder.")

    if response.status_code != 200:
        _manejar_error_respuesta(response, "ruta de direcciones")

    data = response.json()
    features = data.get("features", [])
    if not features:
        raise ORSError("OpenRouteService no devolvió el trazado de la ruta.")

    feat = features[0]
    resumen = feat.get("properties", {}).get("summary", {})
    distancia_m = resumen.get("distance", 0.0)
    duracion_s = resumen.get("duration", 0.0)

    # Coordenadas de la geometría de la calle devueltas por ORS: [ [lon, lat], ... ]
    raw_coords = feat.get("geometry", {}).get("coordinates", [])

    # =========================================================================
    # CONVERSIÓN DE COORDENADAS:
    # ORS entrega las coordenadas en formato [longitud, latitud].
    # Folium requiere estrictamente el orden [latitud, longitud] (o tuplas (lat, lon))
    # para renderizar la polilínea sobre el mapa.
    # =========================================================================
    folium_coords = [[pt[1], pt[0]] for pt in raw_coords]

    return {
        "distancia_m": distancia_m,
        "distancia_km": distancia_m / 1000.0,
        "duracion_seg": duracion_s,
        "duracion_min": duracion_s / 60.0,
        "folium_coords": folium_coords,
    }
