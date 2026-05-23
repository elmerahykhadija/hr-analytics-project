import os
import pandas as pd
import mlflow
import mlflow.sklearn
from snowflake.connector import connect
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, GridSearchCV, StratifiedKFold
from sklearn.metrics import accuracy_score, f1_score
from dotenv import load_dotenv
from mlflow.tracking import MlflowClient

load_dotenv()

# 1. Configuration MLflow
mlflow.set_tracking_uri("http://mlflow:5000")
mlflow.set_experiment("HR_Attrition_Prediction")

# === FEATURES SIMPLIFIÉES ===
REQUIRED_FEATURES = [
    # ========== NUMÉRIQUES ==========
    # Informations Personnelles
    "AGE", "DISTANCEFROMHOME", "EDUCATION",
    
    # Informations Professionnelles
    "JOBLEVEL",
    
    # Rémunération
    "MONTHLYINCOME",
    
    # Expérience
    "TOTALWORKINGYEARS", "NUMCOMPANIESWORKED",
    
    # Satisfaction & Engagement
    "JOBSATISFACTION", "ENVIRONMENTSATISFACTION", "RELATIONSHIPSATISFACTION",
    "JOBINVOLVEMENT", "WORKLIFEBALANCE", "PERFORMANCERATING",
    
    # ========== ONE-HOT ENCODÉES ==========
    # Gender
    "GENDER_MALE", "GENDER_FEMALE",
    
    # MaritalStatus
    "MARITALSTATUS_SINGLE", "MARITALSTATUS_MARRIED", "MARITALSTATUS_DIVORCED",
    
    # BusinessTravel
    "BUSINESSTRAVEL_NONTRAVEL", "BUSINESSTRAVEL_RARELY", "BUSINESSTRAVEL_FREQUENTLY",
    
    # OverTime
    "OVERTIME_NO", "OVERTIME_YES",
]

def train_model():
    # 2. Récupération des données depuis Snowflake
    ctx = connect(
        user=os.getenv('SNOWFLAKE_USER'),
        password=os.getenv('SNOWFLAKE_PASS'),
        account=os.getenv('SNOWFLAKE_ACCOUNT'),
        database=os.getenv('SNOWFLAKE_DATABASE'),
        schema='GOLD',
        role=os.getenv('SNOWFLAKE_ROLE'),
        warehouse=os.getenv('SNOWFLAKE_WAREHOUSE')
    )
    
    query = "SELECT * FROM HR_EMPLOYEE_ENCODED"
    df = pd.read_sql(query, ctx)
    ctx.close()

    print("\n=== DONNÉES BRUTES ===")
    print(f"Shape: {df.shape}")
    print(f"Colonnes disponibles: {len(df.columns)}")
    
    # 3. Filtrer les colonnes valides dans la table réelle
    missing_features = [f for f in REQUIRED_FEATURES if f not in df.columns]
    if missing_features:
        print(f"\n⚠️ ATTENTION - Colonnes manquantes ({len(missing_features)}):")
        print(missing_features)
        print("\nContinue avec les colonnes disponibles...")
        REQUIRED_FEATURES_ACTUAL = [f for f in REQUIRED_FEATURES if f in df.columns]
    else:
        REQUIRED_FEATURES_ACTUAL = REQUIRED_FEATURES
    
    print(f"\n✓ Features à utiliser ({len(REQUIRED_FEATURES_ACTUAL)}):")
    print(REQUIRED_FEATURES_ACTUAL)
    
    # 4. Sélectionner les features + target
    if 'ATTRITION' not in df.columns:
        raise KeyError("La colonne 'ATTRITION' n'existe pas!")
    
    df = df[REQUIRED_FEATURES_ACTUAL + ['ATTRITION']]
    
    print(f"\nDataset final shape: {df.shape}")
    print(f"Attrition distribution:\n{df['ATTRITION'].value_counts()}")

    # 5. Préparation Features/Target
    X = df.drop(columns=['ATTRITION'])
    y = df['ATTRITION'].apply(lambda x: 1 if x == 'Yes' else 0)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=0.2,
        random_state=42,
        stratify=y
    )

    param_grid = {
        "n_estimators": [100, 200, 300],
        "max_depth": [5, 10, 15],
        "min_samples_split": [2, 5, 10],
        "min_samples_leaf": [1, 2, 4],
        "max_features": ["sqrt", "log2"]
    }

    base_model = RandomForestClassifier(
        random_state=42,
        class_weight="balanced"
    )

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

    grid = GridSearchCV(
        estimator=base_model,
        param_grid=param_grid,
        scoring="f1",
        cv=cv,
        n_jobs=-1,
        verbose=2
    )

    with mlflow.start_run():
        print("\n🚀 Entraînement en cours...")
        grid.fit(X_train, y_train)

        best_model = grid.best_estimator_
        y_pred = best_model.predict(X_test)

        acc = accuracy_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred)

        # Feature Importance
        feature_importance = pd.DataFrame({
            'feature': X.columns,
            'importance': best_model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        print("\n--- Top 15 Features ---")
        print(feature_importance.head(15))

        mlflow.log_params(grid.best_params_)
        mlflow.log_metric("best_cv_f1", grid.best_score_)
        mlflow.log_metric("accuracy", acc)
        mlflow.log_metric("f1_score", f1)

        mlflow.sklearn.log_model(
            best_model,
            "attrition_model",
            registered_model_name="RF_Attrition_v1"
        )

        client = MlflowClient()
        model_name = "RF_Attrition_v1"

        # Récupérer la meilleure performance précédente
        try:
            latest_version_info = client.get_latest_versions(model_name, stages=["Production"])
            if latest_version_info:
                production_run_id = latest_version_info[0].run_id
                old_f1 = client.get_run(production_run_id).data.metrics['f1_score']
            else:
                old_f1 = 0
        except Exception:
            old_f1 = 0

        # Comparer et Promouvoir
        if f1 > old_f1:
            print("\n✓ Nouveau modèle meilleur ! Promotion en PRODUCTION.")
            try:
                new_version = client.get_latest_versions(model_name, stages=["None"])[0].version
                client.transition_model_version_stage(
                    name=model_name,
                    version=new_version,
                    stage="Production",
                    archive_existing_versions=True
                )
            except Exception as e:
                print(f"⚠️ Impossible de promouvoir: {e}")
        else:
            print(f"\n✗ Modèle actuel F1={f1:.4f} n'est pas meilleur que F1={old_f1:.4f}")

        print("\n=== RÉSULTATS FINAUX ===")
        print(f"Meilleurs paramètres: {grid.best_params_}")
        print(f"Accuracy: {acc:.4f}")
        print(f"F1 Score: {f1:.4f}")

if __name__ == "__main__":
    train_model()