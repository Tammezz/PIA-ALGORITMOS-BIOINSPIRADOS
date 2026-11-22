"""
test_ors_errors.py - Validación del manejo de errores sin llave o con parámetros inválidos
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ors_client import (
    obtener_api_key,
    geocodificar_lugar,
    obtener_matriz_tiempos,
    ORSError,
    es_coordenada_numerica,
)


def test_sin_llave():
    """Valida que si no hay llave se lance un error entendible."""
    os.environ["ORS_API_KEY"] = ""
    try:
        obtener_api_key()
        assert False, "Debió lanzar ORSError"
    except ORSError as e:
        print(f"✓ Error de llave faltante capturado correctamente:\n  {e}\n")


def test_coordenadas_directas():
    """Valida la detección de coordenadas numéricas sin consumir API."""
    res = es_coordenada_numerica("25.6700, -100.3100")
    assert res == (25.67, -100.31), f"Fallo al parsear: {res}"
    geo = geocodificar_lugar("25.6700, -100.3100", api_key="dummy")
    assert geo["coords_ors"] == [-100.31, 25.67], f"Coords ORS invertidas: {geo}"
    print("✓ Parser de coordenadas numéricas funciona y mantiene [lon, lat] para ORS.")


def test_limite_25_puntos():
    """Valida que se rechace una matriz de más de 25 puntos."""
    puntos_excedidos = [[-100.3, 25.6]] * 26
    try:
        obtener_matriz_tiempos(puntos_excedidos, api_key="dummy")
        assert False, "Debió rechazar más de 25 puntos"
    except ORSError as e:
        print(f"✓ Límite de 25 puntos validado:\n  {e}\n")


if __name__ == "__main__":
    test_sin_llave()
    test_coordenadas_directas()
    test_limite_25_puntos()
    print("¡Todas las validaciones de manejo de errores pasaron con éxito!")
