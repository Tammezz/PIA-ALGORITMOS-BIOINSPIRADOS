"""
test_aco.py - Validación del algoritmo ACO contra Solución Exacta por Fuerza Bruta

Prueba el algoritmo con matrices de 7 y 8 puntos generadas aleatoriamente
y comprueba que el costo mínimo obtenido por ACO coincide exactamente con el óptimo
global determinado por fuerza bruta (todas las permutaciones posibles).
"""

import sys
import os
import itertools
import numpy as np

# Permitir importar módulos desde el directorio raíz
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from aco import resolver_tsp_aco, calcular_costo_ruta


def resolver_tsp_fuerza_bruta(matriz_costos: np.ndarray, regresar_al_origen: bool = True):
    """
    Calcula la solución óptima exacta evaluando todas las permutaciones de los nodos restantes.
    Complejidad: O((N-1)!)
    """
    n = matriz_costos.shape[0]
    nodos_restantes = list(range(1, n))
    mejor_ruta = None
    mejor_costo = float("inf")

    # Evaluamos todas las permutaciones que comienzan en el nodo 0
    for perm in itertools.permutations(nodos_restantes):
        ruta_candidata = [0] + list(perm)
        if regresar_al_origen:
            ruta_candidata.append(0)

        costo = calcular_costo_ruta(ruta_candidata, matriz_costos)
        if costo < mejor_costo:
            mejor_costo = costo
            mejor_ruta = ruta_candidata

    return mejor_ruta, mejor_costo


def generar_matriz_distancias_simetrica(n_puntos: int, semilla: int = 42) -> np.ndarray:
    """Genera una matriz de costos sintética coherente (espacio 2D euclidiano)."""
    rng = np.random.RandomState(semilla)
    # Coordenadas aleatorias en plano 100x100
    puntos = rng.uniform(0, 100, size=(n_puntos, 2))
    # Matriz de distancias euclidianas redondeadas a segundos enteros
    dists = np.zeros((n_puntos, n_puntos), dtype=float)
    for i in range(n_puntos):
        for j in range(n_puntos):
            if i != j:
                dists[i, j] = float(np.linalg.norm(puntos[i] - puntos[j]))
            else:
                dists[i, j] = 0.0
    return dists


def test_aco_vs_fuerza_bruta_7_nodos():
    """Valida que ACO encuentre la solución exacta en 7 nodos con regreso al origen."""
    matriz = generar_matriz_distancias_simetrica(7, semilla=101)
    ruta_fb, costo_fb = resolver_tsp_fuerza_bruta(matriz, regresar_al_origen=True)

    ruta_aco, costo_aco, _ = resolver_tsp_aco(
        matriz,
        n_hormigas=20,
        epocas=80,
        evaporacion=0.4,
        alfa=1.0,
        beta=2.0,
        q=100.0,
        regresar_al_origen=True,
        semilla=42,
    )

    print(f"\n[Test 7 nodos] Costo Fuerza Bruta: {costo_fb:.3f} | Costo ACO: {costo_aco:.3f}")
    assert np.isclose(costo_aco, costo_fb, atol=1e-3), (
        f"El costo de ACO ({costo_aco}) no coincide con la Fuerza Bruta ({costo_fb})"
    )


def test_aco_vs_fuerza_bruta_8_nodos():
    """Valida que ACO encuentre la solución exacta en 8 nodos con regreso al origen."""
    matriz = generar_matriz_distancias_simetrica(8, semilla=202)
    ruta_fb, costo_fb = resolver_tsp_fuerza_bruta(matriz, regresar_al_origen=True)

    ruta_aco, costo_aco, _ = resolver_tsp_aco(
        matriz,
        n_hormigas=25,
        epocas=100,
        evaporacion=0.4,
        alfa=1.0,
        beta=2.0,
        q=100.0,
        regresar_al_origen=True,
        semilla=42,
    )

    print(f"\n[Test 8 nodos] Costo Fuerza Bruta: {costo_fb:.3f} | Costo ACO: {costo_aco:.3f}")
    assert np.isclose(costo_aco, costo_fb, atol=1e-3), (
        f"El costo de ACO ({costo_aco}) no coincide con la Fuerza Bruta ({costo_fb})"
    )


def test_aco_sin_regreso_al_origen():
    """Valida TSP abierto (sin regresar al origen) en 7 nodos."""
    matriz = generar_matriz_distancias_simetrica(7, semilla=303)
    ruta_fb, costo_fb = resolver_tsp_fuerza_bruta(matriz, regresar_al_origen=False)

    ruta_aco, costo_aco, _ = resolver_tsp_aco(
        matriz,
        n_hormigas=20,
        epocas=80,
        evaporacion=0.4,
        alfa=1.0,
        beta=2.0,
        q=100.0,
        regresar_al_origen=False,
        semilla=42,
    )

    print(f"\n[Test sin regreso] Costo Fuerza Bruta: {costo_fb:.3f} | Costo ACO: {costo_aco:.3f}")
    assert np.isclose(costo_aco, costo_fb, atol=1e-3), (
        f"El costo de ACO ({costo_aco}) no coincide con la Fuerza Bruta ({costo_fb})"
    )


if __name__ == "__main__":
    test_aco_vs_fuerza_bruta_7_nodos()
    test_aco_vs_fuerza_bruta_8_nodos()
    test_aco_sin_regreso_al_origen()
    print("\n¡Todos los tests pasaron exitosamente!")
