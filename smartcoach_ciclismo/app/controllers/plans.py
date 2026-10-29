from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from app.services.ml_service import ml_predictor

plans_bp = Blueprint('plans', __name__, url_prefix='/plans')

@plans_bp.route('/generate', methods=['GET', 'POST'])
@login_required
def generate_plan():
    if request.method == 'GET':
        return render_template('plans/generate.html')
        
    if request.method == 'POST':
        datos_usuario = {
            'Edad': f"{current_user.age} años",
            'Peso': f"{current_user.weight_kg} kg",
            'Disponibilidad': f"{current_user.weekly_hours} h/semana",
            'FC Reposo': f"{current_user.resting_heart_rate} lpm",
            'TSS Base': current_user.tss_acumulado
        }
        
        try:
            recomendacion = ml_predictor.predict_training_plan(
                age=current_user.age,
                weight=current_user.weight_kg,
                weekly_hours=current_user.weekly_hours,
                resting_hr=current_user.resting_heart_rate,
                tss=current_user.tss_acumulado
            )
        except Exception as e:
            recomendacion = "Error al ejecutar el modelo"
            descripcion = f"Detalle técnico: {str(e)}"
            return render_template('plans/view.html', recomendacion=recomendacion, descripcion=descripcion, datos=datos_usuario)
        
        if "Avanzado" in recomendacion:
            descripcion = "Estructura de alta carga. Incluye 2 días de intervalos explosivos (VO2 Max) y rodadas de más de 4 horas."
        elif "Moderado" in recomendacion:
            descripcion = "Enfoque en mejorar tu velocidad crucero. Balancea el fondo aeróbico (Zona 2) con estímulos al umbral de lactato."
        else:
            descripcion = "Enfoque en construir base aeróbica. Salidas de 1 a 2 horas a ritmo suave para acostumbrar el cuerpo y prevenir lesiones."

        return render_template('plans/view.html', recomendacion=recomendacion, descripcion=descripcion, datos=datos_usuario)