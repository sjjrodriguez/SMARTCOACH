"""
Prepara los datos del dashboard: KPIs de la semana, series para Chart.js
y el semaforo de riesgo.

Es una funcion pura (no consulta la BD): recibe la lista de sesiones
(objetos Workout) y devuelve un diccionario listo para la plantilla.

NOTA: el semaforo usa, por ahora, la relacion entre la carga de los ultimos
7 dias y el promedio semanal de las 4 semanas anteriores. Cuando
ml_service.py entregue el riesgo del modelo (Low / Medium / High), basta con
reemplazar la llamada a `risk_from_workload` por esa prediccion: la plantilla
solo necesita el diccionario con las claves level, label y message.
"""
from datetime import date, datetime, timedelta

DAY_LABELS = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]

RISK_TEXT = {
    "low": ("Riesgo bajo",
            "Tu carga de esta semana está dentro de lo que tu cuerpo ya tolera. "
            "Mantén tu plan."),
    "medium": ("Riesgo medio",
               "Tu carga de esta semana subió más de lo habitual. "
               "Prioriza el descanso y el sueño."),
    "high": ("Riesgo alto",
             "Tu carga de esta semana es muy superior a la de las últimas semanas. "
             "Baja la intensidad y descansa antes de tu próxima sesión fuerte."),
    "none": ("Sin datos suficientes",
             "Registra al menos una semana de entrenamientos anteriores "
             "para estimar tu riesgo."),
}


def _as_date(value):
    return value.date() if isinstance(value, datetime) else value


def session_load(w):
    """Carga de una sesion: TSS estimado o, si no existe, RPE x minutos (sRPE)."""
    if w.estimated_tss is not None:
        return float(w.estimated_tss)
    return float((w.rpe or 0) * (w.duration_min or 0))


def _load_between(workouts, start, end):
    return sum(session_load(w) for w in workouts if start <= _as_date(w.date) <= end)


def risk_from_workload(acute, chronic_weekly):
    """Devuelve (nivel, ratio). Nivel: low / medium / high / none."""
    if chronic_weekly <= 0:
        return "none", None
    ratio = acute / chronic_weekly
    if ratio <= 1.3:
        return "low", ratio
    if ratio <= 1.5:
        return "medium", ratio
    return "high", ratio


def build_dashboard_data(workouts, today=None):
    today = today or date.today()
    week_start = today - timedelta(days=6)
    week = [w for w in workouts if week_start <= _as_date(w.date) <= today]

    # --- KPIs de los ultimos 7 dias ---
    fatigues = [w.perceived_fatigue for w in week if w.perceived_fatigue is not None]
    kpis = {
        "sessions": len(week),
        "hours": round(sum(w.duration_min or 0 for w in week) / 60, 1),
        "km": round(sum(w.distance_km or 0 for w in week), 1),
        "load": round(sum(session_load(w) for w in week)),
        "fatigue": round(sum(fatigues) / len(fatigues), 1) if fatigues else None,
    }

    # --- Serie diaria (ultimos 7 dias) ---
    days = [week_start + timedelta(days=i) for i in range(7)]
    daily = {
        "labels": [f"{DAY_LABELS[d.weekday()]} {d.day}" for d in days],
        "values": [round(_load_between(workouts, d, d)) for d in days],
    }

    # --- Serie semanal (ultimas 8 ventanas de 7 dias, de la mas antigua a la actual) ---
    weekly = {"labels": [], "values": []}
    for k in range(7, -1, -1):
        end = today - timedelta(days=7 * k)
        start = end - timedelta(days=6)
        weekly["labels"].append(f"{start.day:02d}/{start.month:02d}")
        weekly["values"].append(round(_load_between(workouts, start, end)))

    # --- Semaforo ---
    acute = _load_between(workouts, week_start, today)
    chronic_total = _load_between(workouts, today - timedelta(days=34), today - timedelta(days=7))
    chronic_weekly = chronic_total / 4
    level, ratio = risk_from_workload(acute, chronic_weekly)
    label, message = RISK_TEXT[level]
    risk = {
        "level": level,
        "label": label,
        "message": message,
        "ratio": round(ratio, 2) if ratio is not None else None,
        "acute": round(acute),
        "chronic_weekly": round(chronic_weekly),
    }

    return {
        "has_data": len(workouts) > 0,
        "kpis": kpis,
        "risk": risk,
        "chart": {"daily": daily, "weekly": weekly},
    }