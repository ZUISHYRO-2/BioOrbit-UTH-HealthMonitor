"""
BioOrbit-UTH Health Monitor - Pipeline de Telemetría Biomédica y Motor de Acción
NASA Space Apps Challenge 2026 - Hermosillo, Sonora, México.
Recopila indicadores fisiológicos, ambientales y conductuales, evalúa riesgos
(cardiovascular, inmunológico, pérdida ósea, radiación y salud mental) y genera
protocolos de acción autónomos para el astronauta.
"""

import pandas as pd
import numpy as np


def load_telemetry(filepath: str) -> pd.DataFrame:
    """Carga y parsea el archivo de telemetría de tripulación."""
    df = pd.read_csv(filepath)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df


def calculate_health_scores(df: pd.DataFrame) -> pd.DataFrame:
    """
    Evalúa los 5 ejes críticos del desafío de espacio profundo:
    1. Riesgo Cardiovascular (FC, SpO2)
    2. Salud Mental y Fatiga Autonómica (HRV RMSSD, Eficiencia de sueño)
    3. Riesgo de Pérdida Ósea / Gravedad Alterada (carga de ejercicio resistivo ARED)
    4. Estado Inmunológico (marcador de reactivación viral / estrés sistémico)
    5. Amenaza de Entorno Cerrado y Radiación (CO2 en cabina y radiación uSv/h)
    """
    df = df.copy()

    # 1. Riesgo Cardiovascular
    hr_penalty = np.maximum(0, (df["heart_rate_bpm"] - 90) / 10) + np.maximum(0, (60 - df["heart_rate_bpm"]) / 10)
    spo2_penalty = np.maximum(0, (96 - df["spo2_pct"]) * 2)
    df["cardiovascular_stress_index"] = (hr_penalty + spo2_penalty).round(2)

    # 2. Salud Mental, Aislamiento y Recuperación Autonómica
    # Combina HRV RMSSD (<25 ms = estrés elevado) y eficiencia de sueño (<70% = alerta)
    sleep_penalty = np.maximum(0, (75 - df["sleep_efficiency_pct"]) / 10)
    hrv_penalty = np.maximum(0, (35 - df["hrv_rmssd_ms"]) / 10)
    df["mental_fatigue_score"] = (sleep_penalty + hrv_penalty).round(2)
    df["autonomic_fatigue_index"] = np.where(
        (df["hrv_rmssd_ms"] < 25) | (df["sleep_efficiency_pct"] < 68),
        "Estrés / Fatiga Alta",
        np.where(df["hrv_rmssd_ms"] < 40, "Fatiga Moderada", "Óptimo")
    )

    # 3. Riesgo de Pérdida Ósea (si no existe columna en CSV, se estima por carga de ejercicio/tiempo)
    if "ared_exercise_min" in df.columns:
        df["bone_loss_risk"] = np.where(df["ared_exercise_min"] < 45, "ALTO", "BAJO")
    else:
        # Estimación basada en sedentarismo simulado (FC baja sostenida + sueño bajo)
        df["bone_loss_risk"] = np.where(df["heart_rate_bpm"] < 65, "MODERADO", "BAJO")

    # 4. Indicador de Cambios Inmunológicos (correlación de estrés crónico + radiación + falta de sueño)
    if "immune_cortisol_index" in df.columns:
        immune_score = df["immune_cortisol_index"]
    else:
        immune_score = (
            np.maximum(0, (40 - df["hrv_rmssd_ms"]) / 15)
            + np.maximum(0, (df["radiation_rate_usv_h"] - 25) / 20)
        )
    df["immune_alert"] = np.where(immune_score > 1.8, "SUPRESIÓN LEVE", "ESTABLE")

    # 5. Entorno Cerrado y Radiación Espacial
    co2_risk = np.maximum(0, (df["cabin_co2_ppm"] - 4000) / 500)
    rad_risk = np.maximum(0, (df["radiation_rate_usv_h"] - 35) / 10)
    df["environmental_risk_score"] = (co2_risk + rad_risk).round(2)

    # 6. Nivel de Alerta Compuesto
    conditions = [
        (df["cardiovascular_stress_index"] > 4.0) | (df["environmental_risk_score"] > 3.0) | (df["spo2_pct"] < 93.0),
        (df["cardiovascular_stress_index"] > 2.0) | (df["environmental_risk_score"] > 1.5) | (df["mental_fatigue_score"] > 1.5) | (df["immune_alert"] != "ESTABLE")
    ]
    choices = ["CRÍTICO", "PRECAUCIÓN"]
    df["alert_level"] = np.select(conditions, choices, default="NORMAL")

    # 7. Motor de Acción Autónoma ("Evaluar y Actuar")
    df["recommended_action"] = df.apply(_recommend_action, axis=1)

    return df


def _recommend_action(row: pd.Series) -> str:
    """Genera una contramedida inmediata para que el astronauta actúe de forma autónoma."""
    actions = []
    if row["cardiovascular_stress_index"] > 2.5 or row["spo2_pct"] < 94.0:
        actions.append("Protocolo Cardiovascular: Reposo + chequeo de presión y oxígeno")
    if row["environmental_risk_score"] > 1.5:
        actions.append("Alerta Ambiental: Moverse a zona blindada (radiación) / revisar depurador CO2")
    if row["mental_fatigue_score"] > 1.5:
        actions.append("Salud Mental/Sueño: Aplicar respiración guiada 10 min + ajustar ciclo de luz")
    if row["bone_loss_risk"] != "BAJO":
        actions.append("Contramedida Ósea: Completar rutina resistiva ARED (45 min)")
    if row["immune_alert"] != "ESTABLE":
        actions.append("Soporte Inmunológico: Hidratación, suplemento Vit-D y monitoreo de biomarcadores")

    if not actions:
        return "Mantener protocolo nominal de misión"
    return " | ".join(actions)


def generate_crew_summary(df: pd.DataFrame) -> dict:
    """Genera métricas consolidadas y la acción prioritaria actual por astronauta."""
    summary = {}
    for crew_id, group in df.groupby("crew_id"):
        latest = group.iloc[-1]
        summary[crew_id] = {
            "registros_totales": len(group),
            "fc_promedio_bpm": round(group["heart_rate_bpm"].mean(), 1),
            "spo2_promedio_pct": round(group["spo2_pct"].mean(), 1),
            "hrv_promedio_ms": round(group["hrv_rmssd_ms"].mean(), 1),
            "sueno_promedio_pct": round(group["sleep_efficiency_pct"].mean(), 1),
            "alertas_criticas": int((group["alert_level"] == "CRÍTICO").sum()),
            "alertas_precaucion": int((group["alert_level"] == "PRECAUCIÓN").sum()),
            "dosis_radiacion_usv": round(group["radiation_rate_usv_h"].sum() * 0.25, 1),
            "estado_inmune_actual": latest["immune_alert"],
            "riesgo_oseo_actual": latest["bone_loss_risk"],
            "accion_recomendada_actual": latest["recommended_action"],
        }
    return summary


if __name__ == "__main__":
    import sys

    data_file = "data/sample_astronaut_telemetry.csv"
    if len(sys.argv) > 1:
        data_file = sys.argv[1]

    print(f"[BioOrbit Pipeline] Procesando telemetría desde: {data_file}")
    telemetry = load_telemetry(data_file)
    processed = calculate_health_scores(telemetry)
    summary = generate_crew_summary(processed)

    print("\n=== EVALUACIÓN INTEGRAL Y ACCIONES AUTÓNOMAS ===")
    for crew, stats in summary.items():
        print(f"\nAstronauta {crew}:")
        for k, v in stats.items():
            print(f"  - {k}: {v}")
    print("\n[BioOrbit Pipeline] Evaluación y contramedidas generadas con éxito.")