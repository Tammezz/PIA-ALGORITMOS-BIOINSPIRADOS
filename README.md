# 🐜 ACO Maps · Optimizador de Rutas con Colonia de Hormigas

Aplicación interactiva tipo **Google Maps** en Python y **Streamlit** que encuentra el orden más rápido para visitar múltiples destinos vehiculares utilizando el algoritmo metaheurístico de **Optimización por Colonia de Hormigas (ACO)** y la red vial real proporcionada por la API de **OpenRouteService (ORS)**.

Diseñada con una interfaz moderna y estética **Liquid Glass Black** (Dark Glassmorphism con efectos translúcidos, reflejos especulares y paleta oscura inspirada en visionOS e iOS).

---

## 🌟 Características Principales

- **Algoritmo ACO Puro desde Cero**: Implementado en NumPy sin librerías externas de optimización ni sobreingeniería.
- **Datos Viales Reales**: Geocodificación y cálculo de tiempos reales de manejo con la API gratuita de OpenRouteService con sesgo a Monterrey y México.
- **Visualización Cartográfica Interactiva**: Mapa con mosaicos de **OpenStreetMap** (100% libres, sin cuentas ni marcas de agua) y filtro CSS de inversión tonal integrado en el tema Liquid Glass Black. Botón en la barra superior para alternar entre OSM oscuro y OSM claro. Marcadores numerados por orden de visita y trazado exacto de las calles. La única API Key del proyecto es la de OpenRouteService.
- **Comparativa de Rendimiento**: Muestra la mejora porcentual y los minutos ahorrados entre el orden ingresado originalmente por el usuario vs. el orden óptimo de ACO.
- **Gráfica de Convergencia**: Curva de evolución de la mejor solución por época generada con Matplotlib.
- **Caché Local Inteligente**: Guarda las matrices de tiempos en disco (`.cache/`) mediante hash SHA-256 para proteger y no agotar la cuota gratuita de la API.
- **Manejo Robusto de Errores**: Alertas amigables en español ante fallas de conexión, límites de peticiones (código 429), lugares inalcanzables o ausencia de API Key.
- **Validación Matemática**: Pruebas automáticas contra el algoritmo exacto de **Fuerza Bruta** ($O((N-1)!)$) en 7 y 8 nodos.

---

## 📁 Estructura del Proyecto

```text
├── server.py               # Servidor Web FastAPI de alto rendimiento (SPA)
├── static/                 # Frontend Web Optimizado Liquid Glass Black
│   ├── index.html          # Estructura HTML5 moderna con Glassmorphism
│   ├── style.css           # Estilos CSS Liquid Glass Black puros
│   └── app.js              # Lógica en JS, Leaflet.js y Chart.js
├── app.py                  # Interfaz gráfica alternativa en Streamlit
├── aco.py                  # Algoritmo de Colonia de Hormigas (ACO) con NumPy
├── ors_client.py           # Cliente para OpenRouteService, caché y manejo de errores
├── mapa.py                 # Generación y estilizado del mapa interactivo en Folium
├── requirements.txt        # Dependencias de Python
├── .env.example            # Plantilla para la variable de entorno ORS_API_KEY
├── .env                    # Tu clave privada de la API (ignorado por Git)
├── .gitignore              # Archivos y carpetas excluidos del control de versiones
├── README.md               # Documentación completa del proyecto
├── .cache/                 # Caché en disco para no repetir consultas a la API
└── tests/
    ├── test_aco.py         # Test de ACO vs Fuerza Bruta en 7 y 8 nodos
    └── test_ors_errors.py  # Validación del manejo de errores de la API
```

---

## 🚀 Requisitos e Instalación

### 1. Requisitos Previos
- Python 3.10 o superior instalado.

### 2. Clonar o Descargar el Proyecto
Abre tu terminal en la carpeta del proyecto.

### 3. Instalar Dependencias
```bash
pip install -r requirements.txt
```

### 4. Configurar la API Key de OpenRouteService
1. Obtén tu llave gratuita registrándote en [OpenRouteService Dev Center](https://openrouteservice.org/dev/#/signup).
2. Copia el archivo `.env.example` a `.env`:
   ```bash
   cp .env.example .env
   ```
   *(En Windows PowerShell: `Copy-Item .env.example .env`)*
3. Abre el archivo `.env` y pega tu clave:
   ```env
   ORS_API_KEY=tu_api_key_aqui
   ```

*(Nota: si olvidas poner la llave en el `.env`, la aplicación te permitirá ingresarla temporalmente desde la barra lateral sin romperse).*

---

## 🖥️ Cómo Ejecutar la Aplicación

Tienes a tu disposición **dos versiones** que comparten los mismos algoritmos y lógica:

### 1. Aplicación Web Optimizada (Recomendada · SPA Liquid Glass Black)
Página web moderna, fluida y de alto rendimiento basada en **FastAPI + Leaflet.js + Chart.js**, con microinteracciones y diseño fiel a visionOS / iOS Dark Glassmorphism:

```bash
python server.py
```
*(O también: `uvicorn server:app --reload`)*.  
Abre en tu navegador: **`http://127.0.0.1:8000`**.

### 2. Versión en Streamlit
Para una ejecución rápida desde el framework de prototipado:

```bash
streamlit run app.py
```
Abre en tu navegador: **`http://localhost:8501`**.

---

## 🌐 Despliegue público (Render + Vercel)

La arquitectura recomendada separa la API y el frontend, sin exponer la llave:

- **Render** ejecuta `server.py` (FastAPI): sirve la API REST y, de paso, la SPA.
  El archivo `render.yaml` define el servicio; la variable `ORS_API_KEY` se introduce
  en el dashboard de Render (**nunca** en GitHub).
- **Vercel** publica el frontend estático de `static/` y redirige `/api/*` al servicio
  de Render mediante las rewrites de `vercel.json`, así que el navegador no necesita
  saber la URL del backend ni hay problemas de CORS.

### 1. Render (API)
1. Entra en [Render Dashboard](https://dashboard.render.com) → **New → Blueprint**.
2. Conecta el repositorio `Tammezz/PIA-ALGORITMOS-BIOINSPIRADOS` y aplica `render.yaml`.
3. Cuando te pida `ORS_API_KEY`, pega tu clave gratuita de OpenRouteService.
4. Render creará `https://aco-maps.onrender.com`. Comprueba `/api/status`: debe devolver
   `"api_key_configurada": true`.

### 2. Vercel (frontend)
1. Entra en [Vercel](https://vercel.com/new) → **Import Git Repository** y selecciona el mismo repo.
2. Vercel detectará `vercel.json` y publicará `static/` como raíz del sitio.
3. Si el nombre del servicio de Render termina siendo distinto a `aco-maps`, edita la URL en
   `vercel.json` → `rewrites[0].destination`.
4. El sitio público quedará en `https://<tu-proyecto>.vercel.app`.

> La SPA usa rutas relativas (`/api/...`), por lo que funciona igual en local, en Render y en Vercel.

---

## 🧪 Pruebas y Validación (ACO vs. Fuerza Bruta)

Para verificar que el algoritmo de Colonia de Hormigas encuentra la solución global exacta, ejecuta el script de pruebas automatizadas:

```bash
python tests/test_aco.py
```

### Resultados esperados:
- Evalúa todas las permutaciones posibles con fuerza bruta en 7 nodos ($6! = 720$ combinaciones) y 8 nodos ($7! = 5,040$ combinaciones).
- Comprueba que el costo mínimo obtenido por ACO coincide al 100% con el óptimo global calculado por fuerza bruta.

Para probar la robustez del manejo de errores:
```bash
python tests/test_ors_errors.py
```

---

## 🧠 Explicación del Algoritmo ACO (Para la Clase)

El algoritmo de Colonia de Hormigas está inspirado en el comportamiento biológico de las hormigas al buscar caminos más cortos usando feromonas:

1. **Grafo de Costos**: Cada ubicación representa un nodo. El costo $C_{ij}$ entre el nodo $i$ y el nodo $j$ es el tiempo real de viaje en automóvil (en segundos) provisto por OpenRouteService.
2. **Visibilidad / Heurística ($\eta_{ij}$)**:
   $$\eta_{ij} = \frac{1}{C_{ij}} \quad (i \neq j)$$
   Representa la conveniencia inmediata de viajar al nodo $j$ (a menor tiempo, mayor visibilidad).
3. **Probabilidad de Elección**:
   Cada hormiga en el nodo $i$ decide moverse al siguiente nodo no visitado $j$ con la siguiente probabilidad:
   $$P_{ij} = \frac{(\tau_{ij})^\alpha \cdot (\eta_{ij})^\beta}{\sum_{k \in \text{no visitados}} (\tau_{ik})^\alpha \cdot (\eta_{ik})^\beta}$$
   - $\alpha$ (alfa): Ponderación de la experiencia colectiva (feromona).
   - $\beta$ (beta): Ponderación de la información heurística local (visibilidad).
4. **Evaporación**:
   Al terminar cada época, todas las feromonas se evaporan según la tasa $\rho$:
   $$\tau_{ij} \leftarrow (1 - \rho) \cdot \tau_{ij}$$
   Esto evita que el algoritmo quede estancado prematuramente en óptimos locales.
5. **Depósito de Feromona**:
   Cada hormiga deposita feromona inversamente proporcional al costo total de su ruta ($Q / \text{costo total}$), reforzando los caminos más eficientes de forma simétrica ($\tau_{ij} = \tau_{ji}$).

---

## ⚠️ Nota Importante sobre Coordenadas

- **OpenRouteService (ORS)** utiliza estrictamente el estándar GeoJSON: `[longitud, latitud]`.
- **Folium** y la mayoría de librerías cartográficas utilizan: `[latitud, longitud]`.
- En `ors_client.py` y `mapa.py` se realiza la conversión explícita documentada con comentarios en español para garantizar que las líneas y marcadores se ubiquen con precisión milimétrica.
