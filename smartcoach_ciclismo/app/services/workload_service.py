from datetime import date, timedelta
from app.models.workout import Workout


class WorkloadService:
    @staticmethod
    def calculate_7_day_tss(user_id):
        """TSS estimado acumulado del usuario en los últimos 7 días (0 si no hay)."""
        since = date.today() - timedelta(days=7)
        recent = Workout.query.filter(Workout.user_id == user_id, Workout.date >= since).all()
        return sum(w.estimated_tss for w in recent if w.estimated_tss)


workload_calculator = WorkloadService()
