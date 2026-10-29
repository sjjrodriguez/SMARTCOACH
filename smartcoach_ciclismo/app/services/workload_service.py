from datetime import datetime, timedelta
from app import db
from app.models.workout import Workout

class WorkloadService:
    @staticmethod
    def calculate_7_day_tss(user_id):
        """
        Calcula el TSS acumulado del usuario en los últimos 7 días.
        Si no hay entrenamientos, asume 0.
        """
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        
        recent_workouts = Workout.query.filter(
            Workout.user_id == user_id,
            Workout.fecha >= seven_days_ago
        ).all()

        total_tss = sum(workout.tss for workout in recent_workouts if workout.tss)
        return total_tss

# Instancia para exportar
workload_calculator = WorkloadService()