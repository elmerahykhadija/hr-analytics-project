from prefect import flow, task
import subprocess
from datetime import timedelta

@task(retries=1, retry_delay_seconds=30)
def ingest_data():
    print("LOG: Démarrage Ingestion")
    result = subprocess.run(['python3', 'app/ingest.py'], capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"Erreur Ingestion: {result.stderr}")
    print("LOG: Ingestion terminée")

@task
def prepare_data():
    print("LOG: Démarrage dbt")
    result = subprocess.run(['dbt', 'run', '--project-dir', 'dbt_hr_project'], capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"Erreur dbt: {result.stderr}")
    print("LOG: dbt terminé")

@task
def data_quality_check():
    print("LOG: Démarrage Data Quality")
    result = subprocess.run(['python3', 'app/dataquality.py'], capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"Erreur Qualité: {result.stderr}")
    print("LOG: Qualité validée")

@task
def train_model():
    print("LOG: Démarrage Training")
    result = subprocess.run(['python3', 'app/train.py'], capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"Erreur Training: {result.stderr}")
    print("LOG: Training terminé")

@flow(name="_Pipeline")
def hr_attrition_flow():
    ingest_data()
    prepare_data()
    data_quality_check()
    train_model()

if __name__ == "__main__":
    hr_attrition_flow.serve(
        name="daily-ml-pipeline",
        interval=timedelta(days=1)
    )