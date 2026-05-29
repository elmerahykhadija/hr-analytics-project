import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from snowflake.connector import connect
import logging
from evidently.report import Report
from evidently.metric_preset import DataDriftPreset
import sys
import subprocess
import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Configuration logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataDriftDetector:
    def __init__(self):
        """Initialiser la connexion Snowflake"""
        self.conn = connect(
            user=os.getenv('SNOWFLAKE_USER'),
            password=os.getenv('SNOWFLAKE_PASS'),
            account=os.getenv('SNOWFLAKE_ACCOUNT'),
            database=os.getenv('SNOWFLAKE_DATABASE'),
            schema=os.getenv('SNOWFLAKE_SCHEMA'),
            warehouse=os.getenv('SNOWFLAKE_WAREHOUSE')
        )
        self.cursor = self.conn.cursor()
        logger.info(f"✅ Connecté à Snowflake: {os.getenv('SNOWFLAKE_ACCOUNT')}")
        
    def fetch_data_from_snowflake(self):
        """Récupérer les données depuis la table gold_encoded"""
        query = """
        SELECT * 
        FROM RH_DB.GOLD.HR_EMPLOYEE_ENCODED
        ORDER BY INGESTIONDATE DESC
        LIMIT 10000
        """
        self.cursor.execute(query)
        df = self.cursor.fetch_pandas_all()
        
        if df.empty:
            logger.error("❌ Aucune donnée trouvée dans la table. Vérifiez que RH_DB.RAW.HR_RAW_DATA contient des données.")
            raise ValueError("La table HR_EMPLOYEE_ENCODED est vide")
        
        df['INGESTIONDATE'] = pd.to_datetime(df['INGESTIONDATE'])
        return df
    
    def split_by_day(self, df):
        """Séparer les données par jour"""
        df['date'] = df['INGESTIONDATE'].dt.date
        daily_data = {}
        
        for date, group in df.groupby('date'):
            daily_data[date] = group.reset_index(drop=True)
            logger.info(f"📅 {date}: {len(group)} enregistrements")
        
        return daily_data
    
    def detect_drift(self, reference_data, current_data):
        """Détecter le data drift avec Evidently"""
        # Exclure colonnes temporelles
        feature_cols = [col for col in reference_data.columns 
                       if col not in ['INGESTIONDATE', 'date']]
        
        # Créer le rapport
        report = Report(metrics=[DataDriftPreset()])
        report.run(
            reference_data=reference_data[feature_cols],
            current_data=current_data[feature_cols]
        )
        
        # Extraire les résultats
        drift_detected = False
        drift_metrics = report.as_dict()
        
        if 'metrics' in drift_metrics:
            for metric in drift_metrics['metrics']:
                if 'result' in metric and metric['result'].get('drift_detected', False):
                    drift_detected = True
                    logger.warning(f"⚠️ DATA DRIFT DÉTECTÉ: {metric}")
                    break
        
        return drift_detected, report
    
    def run_training(self):
        """Lancer le training"""
        logger.info("🚀 Lancement du training...")
        try:
            # Appeler le script train.py
            result = subprocess.run(
                ['python3', 'app/train.py'],
                capture_output=True,
                text=True,
                timeout=3600
            )
            
            if result.returncode == 0:
                logger.info("✅ Training complété avec succès")
                return True
            else:
                logger.error(f"❌ Erreur training: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"❌ Erreur lors du training: {str(e)}")
            return False
    
    
    def execute(self):
        """Pipeline principal"""
        logger.info("=" * 50)
        logger.info("🔍 DÉTECTION DE DATA DRIFT")
        logger.info("=" * 50)
        
        # 1️⃣ Récupérer les données
        logger.info("📥 Récupération des données depuis Snowflake...")
        df = self.fetch_data_from_snowflake()
        logger.info(f"✅ {len(df)} enregistrements chargés")
        
        # 2️⃣ Séparer par jour
        logger.info("📊 Séparation des données par jour...")
        daily_data = self.split_by_day(df)
        
        unique_dates = sorted(daily_data.keys(), reverse=True)
        logger.info(f"📅 {len(unique_dates)} jours détectés")
        
        # 3️⃣ Vérifier si données d'un seul jour
        if len(unique_dates) == 1:
            logger.info("⚡ DONNÉES D'UN SEUL JOUR")
            logger.info("→ Lancement du TRAINING normal")
            self.run_training()
            return
        
        # 4️⃣ Plusieurs jours: Détecter le drift
        logger.info("📈 Plusieurs jours détectés - Détection de drift...")
        current_date = unique_dates[0]
        historical_dates = unique_dates[1:]
        
        # Combiner tous les jours précédents
        reference_data = pd.concat(
            [daily_data[date] for date in historical_dates],
            ignore_index=True
        )
        current_data = daily_data[current_date]
        
        logger.info(f"  Reference: {len(historical_dates)} jours précédents ({len(reference_data)} records)")
        logger.info(f"  Current:   {current_date} ({len(current_data)} records)")
        
        drift_detected, report = self.detect_drift(reference_data, current_data)
    
        # 5️⃣ Décision: Training ou skip
        if drift_detected:
            logger.warning("⚠️ DATA DRIFT DÉTECTÉ!")
            logger.info("→ Lancement du RETRAINING")
            self.run_training()
        else:
            logger.info("✅ Pas de data drift détecté")
            logger.info("→ Skip du training")
    
        logger.info("=" * 50)
        logger.info("✅ PIPELINE COMPLÉTÉ")
        logger.info("=" * 50)

if __name__ == "__main__":
    detector = DataDriftDetector()
    detector.execute()