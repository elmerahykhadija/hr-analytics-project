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
# L'URI pointe vers le service nommé 'mlflow' dans ton docker-compose
mlflow.set_tracking_uri("http://localhost:5000") 
mlflow.set_experiment("HR_Attrition_Prediction")

def train_model():
    # 2. Récupération des données depuis Snowflake (Table GOLD)
    ctx = connect(
        user=os.getenv('SNOWFLAKE_USER'),
        password=os.getenv('SNOWFLAKE_PASS'),
        account=os.getenv('SNOWFLAKE_ACCOUNT'),
        database=os.getenv('SNOWFLAKE_DATABASE'),
        schema='GOLD', # On utilise les données préparées par dbt[cite: 7]
        role=os.getenv('SNOWFLAKE_ROLE'),
        warehouse=os.getenv('SNOWFLAKE_WAREHOUSE')
    )
    
    query = "SELECT * FROM HR_EMPLOYEE_ENCODED" # Nom de ton dernier modèle dbt
    df = pd.read_sql(query, ctx)
    ctx.close()

    # 3. Préparation Features/Target
    X = df.drop(columns=['ATTRITION'])
    # Encodage de la target Attrition (Yes -> 1, No -> 0)
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
        grid.fit(X_train, y_train)

        best_model = grid.best_estimator_
        y_pred = best_model.predict(X_test)

        acc = accuracy_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred)

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

        # 1. Récupérer la meilleure performance précédente (Production)
        try:
            latest_version_info = client.get_latest_versions(model_name, stages=["Production"])
            if latest_version_info:
                production_run_id = latest_version_info[0].run_id
                old_f1 = client.get_run(production_run_id).data.metrics['f1_score']
            else:
                old_f1 = 0
        except Exception:
            old_f1 = 0

        # 2. Comparer et Promouvoir
        if f1 > old_f1:
            print("Nouveau modèle meilleur ! Promotion en PRODUCTION.")
            new_version = client.get_latest_versions(model_name, stages=["None"])[0].version
            client.transition_model_version_stage(
                name=model_name,
                version=new_version,
                stage="Production",
                archive_existing_versions=True
            )
        else:
            print("Le nouveau modèle n'est pas meilleur. On garde l'ancien en Production.")

        print("Meilleurs paramètres:", grid.best_params_)
        print(f"Accuracy test: {acc:.2f}, F1 test: {f1:.2f}")

if __name__ == "__main__":
    train_model()