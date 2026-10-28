import os
import pandas as pd
from app import db, create_app
from app.models.user import User

def seed_cyclists():
    """Reads the Colombian cycling dataset and seeds initial athletes into the database."""
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
    csv_path = os.path.join(base_dir, 'ml_engine', 'data', 'datos_gov_ciclismo.csv')
    
    if not os.path.exists(csv_path):
        print(f"Error: Dataset file not found at: {csv_path}")
        return

    print("Reading dataset from datos_gov_ciclismo.csv...")
    df = pd.read_csv(csv_path)

    # Filter unique athletes by ID to avoid duplicate months
    df_unique = df.drop_duplicates(subset=['ID']).head(30)
    print(f"Seeding {len(df_unique)} unique cyclists into the database...")

    inserted_count = 0
    for _, row in df_unique.iterrows():
        athlete_id = str(row['ID'])
        email = f"cyclist_{athlete_id}@smartcoach.co"

        # Check if the user already exists
        if not User.query.filter_by(email=email).first():
            # Parse age from range string (e.g., '15-19' -> 18)
            age_range = str(row.get('Rango_Edad', '18'))
            try:
                if '-' in age_range:
                    age = int(age_range.split('-')[1]) - 1
                else:
                    age = int(age_range)
            except (ValueError, TypeError):
                age = 22

            # Map discipline from Deporte column (BMX, Track, Road, or MTB)
            sport_name = str(row.get('Deporte', 'Road')).upper()
            if 'BMX' in sport_name:
                discipline = 'BMX'
            elif 'PISTA' in sport_name:
                discipline = 'Track'
            elif 'RUTA' in sport_name:
                discipline = 'Road'
            else:
                discipline = 'MTB'

            new_cyclist = User(
                full_name=f"Cyclist Antioquia {athlete_id}",
                email=email,
                age=age,
                weight_kg=65.0,
                height_cm=172.0,
                discipline=discipline,
                level=str(row.get('Tipo_Atleta', 'Amateur'))
            )
            new_cyclist.set_password('SmartCoach2026*')

            db.session.add(new_cyclist)
            inserted_count += 1

    db.session.commit()
    print(f"Seeding completed successfully: {inserted_count} cyclists added.")

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        seed_cyclists()