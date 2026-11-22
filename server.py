"""
server.py - Servidor Web FastAPI de alto rendimiento para ACO Maps

Expone una API REST moderna y sirve la aplicación web optimizada estilo Liquid Glass Black.
"""

import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from ors_client import (
    geocodificar_lugar,
    obtener_matriz_tiempos,
    obtener_ruta_real,
    obtener_api_key,
    ORSError,
)
from aco import resolver_tsp_aco, calcular_costo_ruta

app = FastAPI(title="ACO Maps - Liquid Glass Web API", version="2.0.0")

# Esquemas de entrada y salida
class PeticionOptimizacion(BaseModel):
    lugares: List[str] = Field(..., description="Lista de nombres o coordenadas 'lat, lon'")
    regresar_inicio: bool = Field(True, description="Si la ruta debe regresar al punto de partida")
    n_hormigas: int = Field(15, ge=2, le=100)
    epocas: int = Field(100, ge=5, le=500)
    evaporacion: float = Field(0.4, ge=0.01, le=0.99)
    alfa: float = Field(1.0, ge=0.0, le=10.0)
    beta: float = Field(2.0, ge=0.1, le=10.0)
    q: float = Field(100.0, ge=1.0, le=1000.0)
    semilla: Optional[int] = Field(None, description="Semilla para reproducibilidad")


# Rutas API
@app.get("/api/status")
def status_api():
    """Verifica si la API key de OpenRouteService está configurada."""
    api_key = os.getenv("ORS_API_KEY", "").strip()
    configurada = bool(api_key and api_key != "tu_api_key_aqui")
    return {
        "ok": True,
        "api_key_configurada": configurada
    }


@app.get("/api/autocompletar")
def autocompletar(q: str = ""):
    """Devuelve sugerencias de lugares en tiempo real para autocompletado."""
    from ors_client import autocompletar_lugares
    sugerencias = autocompletar_lugares(q)
    return {"sugerencias": sugerencias}


@app.get("/api/reverso")
def reverso(lat: float, lon: float):
    """Obtiene el nombre de un lugar al hacer clic en el mapa."""
    from ors_client import geocodificar_inverso
    lugar = geocodificar_inverso(lat, lon)
    return {"lugar": lugar}


@app.get("/api/buscar")
def buscar_punto(q: str = ""):
    """Resuelve un lugar a sus coordenadas exactas."""
    try:
        info = geocodificar_lugar(q)
        return {"ok": True, "lugar": info}
    except ORSError as err:
        raise HTTPException(status_code=400, detail=str(err))


@app.post("/api/optimizar")
def optimizar_ruta(req: PeticionOptimizacion):
    """
    Geocodifica los lugares, obtiene la matriz de tiempos vial, ejecuta ACO
    y entrega el trazado por calles con métricas comparativas.
    """
    lineas_limpias = [l.strip() for l in req.lugares if l.strip()]

    if len(lineas_limpias) < 2:
        raise HTTPException(
            status_code=400,
            detail="Se requieren al menos 2 ubicaciones para trazar una ruta."
        )

    if len(lineas_limpias) > 25:
        raise HTTPException(
            status_code=400,
            detail=f"Límite excedido: se ingresaron {len(lineas_limpias)} lugares (máximo 25 permitidos en el plan gratuito)."
        )

    try:
        # 1. Geocodificación
        lugares_info = []
        coords_ors = []
        for texto in lineas_limpias:
            info = geocodificar_lugar(texto)
            lugares_info.append(info)
            coords_ors.append(info["coords_ors"])

        # 2. Matriz de duraciones (con caché local)
        matriz_duraciones = obtener_matriz_tiempos(coords_ors)

        # 3. Costo original sin optimizar
        n_nodos = len(lugares_info)
        indices_original = list(range(n_nodos))
        if req.regresar_inicio:
            indices_original.append(0)
        costo_original_seg = calcular_costo_ruta(indices_original, matriz_duraciones)

        # 4. Algoritmo de Colonia de Hormigas (ACO)
        mejor_ruta_indices, mejor_costo_seg, historial_conv = resolver_tsp_aco(
            matriz_costos=matriz_duraciones,
            n_hormigas=req.n_hormigas,
            epocas=req.epocas,
            evaporacion=req.evaporacion,
            alfa=req.alfa,
            beta=req.beta,
            q=req.q,
            regresar_al_origen=req.regresar_inicio,
            semilla=req.semilla,
        )

        # 5. Geometría real por calles de ORS
        coords_ordenadas_ors = [coords_ors[idx] for idx in mejor_ruta_indices]
        ruta_real = obtener_ruta_real(coords_ordenadas_ors)

        # 6. Métricas de comparación
        min_original = float(costo_original_seg / 60.0)
        min_aco = float(mejor_costo_seg / 60.0)
        ahorro_min = float(max(0.0, min_original - min_aco))
        mejora_pct = float(ahorro_min / min_original * 100.0) if min_original > 0 else 0.0

        # Formatear secuencia detallada convirtiendo tipos de numpy a tipos nativos de Python
        secuencia_visita = []
        total_pasos = len(mejor_ruta_indices)
        for paso, idx in enumerate(mejor_ruta_indices, start=1):
            idx_int = int(idx)
            es_origen = bool(paso == 1)
            es_retorno = bool(paso == total_pasos and req.regresar_inicio and paso > 1)
            secuencia_visita.append({
                "paso": int(paso),
                "indice": idx_int,
                "nombre": str(lugares_info[idx_int]["nombre"]),
                "lat": float(lugares_info[idx_int]["lat"]),
                "lon": float(lugares_info[idx_int]["lon"]),
                "es_origen": es_origen,
                "es_retorno": es_retorno,
            })

        return {
            "ok": True,
            "metricas": {
                "tiempo_aco_min": round(min_aco, 1),
                "tiempo_original_min": round(min_original, 1),
                "ahorro_min": round(ahorro_min, 1),
                "mejora_porcentaje": round(mejora_pct, 1),
                "distancia_km": round(float(ruta_real["distancia_km"]), 2),
                "duracion_real_min": round(float(ruta_real["duracion_min"]), 1),
            },
            "secuencia": secuencia_visita,
            "geometria_ruta": [[float(pt[0]), float(pt[1])] for pt in ruta_real["folium_coords"]],
            "historial_convergencia": [round(float(c) / 60.0, 2) for c in historial_conv],
        }

    except ORSError as err:
        raise HTTPException(status_code=400, detail=str(err))
    except Exception as ex:
        raise HTTPException(status_code=500, detail=f"Error en servidor: {str(ex)}")


# Servir la aplicación web estática
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
def raiz():
    """Entrega la página web principal optimizada."""
    return FileResponse("static/index.html")


if __name__ == "__main__":
    import uvicorn
    print("Iniciando ACO Maps Web Server en http://127.0.0.1:8000 ...")
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)
