"""
aco.py - Algoritmo de Optimización por Colonia de Hormigas (Ant Colony Optimization - ACO)

Implementación pura con NumPy para resolver el Problema del Agente Viajero (TSP).
No utiliza librerías externas de optimización.
"""

from typing import List, Tuple, Optional
import numpy as np


def resolver_tsp_aco(
    matriz_costos: np.ndarray,
    n_hormigas: int = 15,
    epocas: int = 100,
    evaporacion: float = 0.4,
    alfa: float = 1.0,
    beta: float = 2.0,
    q: float = 100.0,
    regresar_al_origen: bool = True,
    semilla: Optional[int] = None,
) -> Tuple[List[int], float, List[float]]:
    """
    Resuelve el problema de encontrar la ruta óptima usando ACO.

    Parámetros:
    -----------
    matriz_costos : np.ndarray
        Matriz cuadrada (N x N) con los tiempos o costos entre cada par de nodos.
    n_hormigas : int
        Número de hormigas exploradoras por época (por defecto 15).
    epocas : int
        Número de iteraciones o épocas del algoritmo (por defecto 100).
    evaporacion : float
        Tasa de evaporación de feromonas rho en [0, 1] (por defecto 0.4).
    alfa : float
        Peso de la feromona en la decisión de la hormiga (por defecto 1.0).
    beta : float
        Peso de la heurística de visibilidad (1 / costo) (por defecto 2.0).
    q : float
        Factor constante de depósito de feromonas (por defecto 100.0).
    regresar_al_origen : bool
        Si es True, la ruta debe volver al punto de partida (nodo 0).
    semilla : Optional[int]
        Semilla para el generador pseudoaleatorio para reproducibilidad.

    Retorna:
    --------
    mejor_ruta : List[int]
        Secuencia de índices de nodos que conforman la mejor ruta encontrada.
    mejor_costo : float
        Costo total (tiempo en segundos) de la mejor ruta.
    historial_convergencia : List[float]
        El mejor costo global registrado al final de cada época.
    """
    if semilla is not None:
        np.random.seed(semilla)

    n_nodos = matriz_costos.shape[0]
    if n_nodos <= 1:
        # Caso trivial con 0 o 1 nodo
        ruta = [0] if n_nodos == 1 else []
        if n_nodos == 1 and regresar_al_origen:
            ruta = [0, 0]
        return ruta, 0.0, [0.0] * epocas

    # 1. Matriz de visibilidad (heurística: 1 / costo)
    # Evitamos división entre cero en la diagonal (o tramos con costo 0)
    visibilidad = np.zeros_like(matriz_costos, dtype=float)
    with np.errstate(divide="ignore"):
        # Donde el costo sea mayor a cero, calculamos la inversa
        mascara_positiva = matriz_costos > 0
        visibilidad[mascara_positiva] = 1.0 / matriz_costos[mascara_positiva]
        # La diagonal y ceros permanecen en 0 para no seleccionarse indebidamente
        np.fill_diagonal(visibilidad, 0.0)

    # 2. Inicialización de la matriz de feromonas
    # Iniciamos con un valor uniforme positivo en todas las conexiones
    feromona = np.ones((n_nodos, n_nodos), dtype=float)
    np.fill_diagonal(feromona, 0.0)

    mejor_ruta_global: Optional[List[int]] = None
    mejor_costo_global = float("inf")
    historial_convergencia: List[float] = []

    # 3. Bucle principal de épocas
    for _ in range(epocas):
        rutas_hormigas: List[List[int]] = []
        costos_hormigas: List[float] = []

        # Cada hormiga construye una solución completa
        for _ in range(n_hormigas):
            # El punto 1 es el origen (nodo 0)
            nodo_actual = 0
            nodos_no_visitados = set(range(1, n_nodos))
            ruta_hormiga = [nodo_actual]
            costo_hormiga = 0.0

            # Visitar el resto de los nodos sin repetir
            while nodos_no_visitados:
                candidatos = list(nodos_no_visitados)

                # Cálculo de la probabilidad de transición para cada candidato:
                # P(j) proporcional a [tau(actual, j)]^alfa * [eta(actual, j)]^beta
                tau = feromona[nodo_actual, candidatos] ** alfa
                eta = visibilidad[nodo_actual, candidatos] ** beta
                atractivo = tau * eta

                suma_atractivo = np.sum(atractivo)
                if suma_atractivo > 0 and not np.isnan(suma_atractivo):
                    probabilidades = atractivo / suma_atractivo
                else:
                    # En caso extremo de que todos sean 0, distribución uniforme
                    probabilidades = np.ones(len(candidatos)) / len(candidatos)

                # Selección estocástica del siguiente nodo según las probabilidades
                siguiente_nodo = np.random.choice(candidatos, p=probabilidades)
                costo_hormiga += float(matriz_costos[nodo_actual, siguiente_nodo])

                ruta_hormiga.append(siguiente_nodo)
                nodos_no_visitados.remove(siguiente_nodo)
                nodo_actual = siguiente_nodo

            # Si se requiere regresar al origen, agregamos el retorno al nodo 0
            if regresar_al_origen:
                costo_hormiga += float(matriz_costos[nodo_actual, 0])
                ruta_hormiga.append(0)

            rutas_hormigas.append(ruta_hormiga)
            costos_hormigas.append(costo_hormiga)

            # Actualización del mejor resultado global
            if costo_hormiga < mejor_costo_global:
                mejor_costo_global = float(costo_hormiga)
                mejor_ruta_global = [int(x) for x in ruta_hormiga]

        # 4. Actualización de Feromonas
        # a) Evaporación en toda la matriz: tau = (1 - rho) * tau
        feromona = (1.0 - evaporacion) * feromona
        # Mantener un piso mínimo para evitar que se anulen caminos
        feromona = np.clip(feromona, a_min=1e-6, a_max=None)

        # b) Depósito de feromona por cada hormiga: delta_tau = Q / costo_total
        for ruta, costo in zip(rutas_hormigas, costos_hormigas):
            if costo > 0:
                deposito = q / costo
                for i in range(len(ruta) - 1):
                    u = ruta[i]
                    v = ruta[i + 1]
                    # Se deposita de forma simétrica como pide el enunciado
                    feromona[u, v] += deposito
                    feromona[v, u] += deposito

        # Registro para la gráfica de convergencia
        historial_convergencia.append(float(mejor_costo_global))

    assert mejor_ruta_global is not None
    return mejor_ruta_global, float(mejor_costo_global), historial_convergencia


def calcular_costo_ruta(ruta: List[int], matriz_costos: np.ndarray) -> float:
    """Calcula el costo total de recorrer una secuencia de nodos."""
    costo = 0.0
    for i in range(len(ruta) - 1):
        costo += float(matriz_costos[ruta[i], ruta[i + 1]])
    return costo
