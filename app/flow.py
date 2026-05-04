from prefect import flow, task
import subprocess
from datetime import timedelta

@task(retries=1, retry_delay_seconds=30)
def ingest_data():
    """Charger les données brutes depuis la source"""
    print("LOG: Démarrage Ingestion")
    result = subprocess.run(['python3', 'app/ingest.py'], capture_output=True, text=True)
    print(f"STDOUT: {result.stdout}")
    if result.returncode != 0:
        print(f"STDERR: {result.stderr}")
        raise Exception(f"Erreur Ingestion: {result.stderr}")
    print("LOG: Ingestion terminée ✓")



@task(retries=1, retry_delay_seconds=30)
def prepare_data():
    """Exécuter les transformations dbt"""
    print("LOG: Démarrage dbt run")
    result = subprocess.run(
        ["dbt", "run", "--project-dir", "dbt_hr_project", "--profiles-dir", "dbt_hr_project"],
        capture_output=True,
        text=True
    )
    print(f"STDOUT: {result.stdout}")
    if result.returncode != 0:
        print(f"STDERR: {result.stderr}")
        raise Exception(f"Erreur dbt: {result.stderr}")
    print("LOG: dbt run terminé ✓")

@task(retries=1, retry_delay_seconds=30)
def data_quality_check():
    """Vérifier la qualité des données ML-ready"""
    print("LOG: Démarrage Data Quality Check")
    result = subprocess.run(['python3', 'app/dataquality.py'], capture_output=True, text=True)
    print(f"STDOUT: {result.stdout}")
    if result.returncode != 0:
        print(f"STDERR: {result.stderr}")
        raise Exception(f"Erreur Data Quality: {result.stderr}")
    print("LOG: Data Quality validée ✓")

@task(retries=1, retry_delay_seconds=30)
def train_model():
    """Entraîner le modèle ML et le promouvoir en Production"""
    print("LOG: Démarrage Training du modèle")
    result = subprocess.run(['python3', 'app/train.py'], capture_output=True, text=True)
    print(f"STDOUT: {result.stdout}")
    if result.returncode != 0:
        print(f"STDERR: {result.stderr}")
        raise Exception(f"Erreur Training: {result.stderr}")
    print("LOG: Training du modèle terminé ✓")

@flow(name="HR_Attrition_ML_Pipeline")
def hr_attrition_flow():
    """
    Pipeline ML complet pour la prédiction d'attrition RH
    
    Étapes :
    1. Ingest : Charger les données brutes
    2. Seed : Charger dans Snowflake
    3. dbt run : Transformer et encoder les données
    4. Data Quality : Valider la qualité ML-ready
    5. Train : Entraîner et promouvoir le modèle
    """
    print("🚀 Démarrage du pipeline ML complet")
    print("="*60)
    
    ingest_data()
    prepare_data()
    data_quality_check()
    train_model()
    
    print("="*60)
    print("✓ ✓ ✓ Pipeline ML terminé avec succès ✓ ✓ ✓")

if __name__ == "__main__":
    hr_attrition_flow.serve(
        name="daily-ml-pipeline",
        interval=timedelta(days=1)
    )