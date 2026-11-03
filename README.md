# BioOrbit-UTH / Astronaut Health & Dev 🚀
**NASA Space Apps Challenge 2026 — Sede Hermosillo, Sonora, México**  
**Desafío Oficial:** *Create Health Monitoring Software for Astronauts on Space Missions*  
**Equipo:** BioOrbit UTH (`yovani28`, líder mecatrónico)

---

## 🛰️ Resumen del Proyecto

Durante misiones de espacio profundo hacia la Luna y Marte, las tripulaciones enfrentan ambientes hostiles caracterizados por microgravedad constante, radiación ionizante acumulada, confinamiento y estrés fisiológico. Debido a los retrasos en las comunicaciones tierra-espacio (hasta 20 minutos en Marte), los astronautas requieren autonomía médica inmediata para monitorear, diagnosticar y responder a riesgos de salud sin asistencia en tiempo real de los cirujanos de vuelo.

**BioOrbit-UTH** es una plataforma de software distribuida y predictiva que integra:
1. **Pipeline de Telemetría Fisiológica:** Ingesta de bioseñales clave (Frecuencia Cardíaca, Variabilidad de Frecuencia Cardíaca - HRV RMSSD, SpO2, Temperatura y Dosimetría de Radiación).
2. **Motor de Inferencia de Riesgo Multivariable:** Algoritmos que calculan índices compuestos de estrés cardiovascular, recuperación autonómica y amenaza ambiental.
3. **Monitor Óptico en Cabina (OpenCV):** Detección sin contacto de fatiga visual, microexpresiones de estrés y desalineación postural durante ejercicios en microgravedad.
4. **Consola Táctica de Cabina:** Dashboard interactivo optimizado para alta visibilidad y toma de decisiones preventiva.

---

## 📊 Fuentes de Datos Abiertas de la NASA Utilizadas

- **[NASA Open Science Data Repository (OSDR)](https://science.nasa.gov/biological-physical/data/osdr/):** Parámetros de referencia omicos y biomarcadores de astronautas en misiones de larga duración.
- **[NASA Life Sciences Portal (NLSP / LSDA)](https://www.nasa.gov/hrp/nlsp/):** Datos fisiológicos de misiones análogas de reposo en cama (*bedrest studies*) y telemetría histórica de la ISS.
- **[NASA Open APIs](https://api.nasa.gov/):** Variables de radiación y clima espacial para correlación ambiental.

---

## 🛠️ Arquitectura de Software y Stack Tecnológico

El proyecto sigue las directrices técnicas de ingeniería y digitalización de `@gemini-spark-instructions`:
- **Entorno de Programación:** Python 3.10+ en VS Code.
- **Procesamiento de Bioseñales:** `pandas`, `numpy`, `scipy`.
- **Visión Computacional:** `OpenCV` (detección óptica de fatiga y monitoreo biomecánico).
- **Consola / UI:** Streamlit / Plotly con interfaz táctil en modo nocturno de baja luminancia para cabina espacial.

---

## 📁 Estructura del Repositorio

```text
BioOrbit-UTH-HealthMonitor/
├── data/
│   └── sample_astronaut_telemetry.csv   # Dataset de bioseñales calibrado con rangos NASA
├── src/
│   ├── data_pipeline.py                 # Pipeline de ingesta, cálculo de HRV y alertas
│   └── vision_monitor.py                # Módulo OpenCV de análisis de fatiga y postura
├── docs/
│   └── pitch_script_30s.md              # Guion oficial de pitch de 30 segundos en inglés
├── requirements.txt                     # Dependencias de Python
└── README.md                            # Documentación técnica del proyecto
```

---

## 🚀 Guía de Instalación y Ejecución Rápida

### 1. Clonar y preparar entorno
```bash
git clone https://github.com/yovani28/BioOrbit-UTH-HealthMonitor.git
cd BioOrbit-UTH-HealthMonitor
python3 -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Ejecutar el Pipeline de Telemetría Biomédica
```bash
python src/data_pipeline.py data/sample_astronaut_telemetry.csv
```

### 3. Ejecutar el Monitor de Visión Computacional
```bash
python src/vision_monitor.py
```

---

## 🏆 Alineación con los Criterios de Evaluación de la NASA

- **Impacto (Impact):** Reduce la dependencia de telemedicina terrestre y mitiga riesgos de arritmias, pérdida ósea y fatiga crónica en misiones interplanetarias.
- **Creatividad (Creativity):** Fusión única de datos biomédicos tradicionales con visión artificial embebida en cabina para evaluación ergonómica y cognitiva sin contacto.
- **Validez (Validity):** Rangos normales y umbrales de alerta calibrados con literatura médica de la NASA y el *Human Research Program* (HRP).
- **Relevancia (Relevance):** Cumple con todos los lineamientos del desafío oficial de salud de astronautas 2026.
- **Presentación (Presentation):** Código modular y documentado, arquitectura reproducible y video pitch de 30 segundos estructurado en inglés.