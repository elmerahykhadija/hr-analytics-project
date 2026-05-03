import pandas as pd
import snowflake.connector
import great_expectations as ge
import os
import json
from dotenv import load_dotenv

load_dotenv()

# Connexion Snowflake (couche GOLD / DBT output)
ctx = snowflake.connector.connect(
    user=os.getenv('SNOWFLAKE_USER'),
    password=os.getenv('SNOWFLAKE_PASS'),
    account=os.getenv('SNOWFLAKE_ACCOUNT'),
    warehouse=os.getenv('SNOWFLAKE_WAREHOUSE'),
    database=os.getenv('SNOWFLAKE_DATABASE'),
    schema=os.getenv('SNOWFLAKE_SCHEMA', 'GOLD'),
    role=os.getenv('SNOWFLAKE_ROLE')
)

# Charger dataset DBT
TABLE = os.getenv('DQ_TABLE', 'HR_EMPLOYEE_ENCODED')
# Force le chemin complet pour être sûr de l'endroit où on cherche
query = f'SELECT * FROM "{os.getenv("SNOWFLAKE_DATABASE")}"."GOLD"."HR_EMPLOYEE_ENCODED"'
df = pd.read_sql(query, ctx)

# nettoyage léger des noms de colonnes
df.columns = [col.strip() for col in df.columns]

# helper pour ajouter des expectations seulement si la colonne existe
def expect_if_exists(df_ge, col_name, method_name, *args, **kwargs):
    if col_name in df.columns:
        getattr(df_ge, method_name)(col_name, *args, **kwargs)

# Validation ML-ready avec Great Expectations
def validate_ml_ready(df):
    df_ge = ge.from_pandas(df)

    # TARGET CHECK
    expect_if_exists(df_ge, "ATTRITION", "expect_column_values_to_be_in_set", [0, 1])

    # NULL CHECK (features critiques)
    expect_if_exists(df_ge, "MonthlyIncome", "expect_column_values_to_not_be_null")
    expect_if_exists(df_ge, "Age", "expect_column_values_to_not_be_null")

    # RANGE CHECK (cohérence RH)
    expect_if_exists(df_ge, "Age", "expect_column_values_to_be_between", 18, 65)
    # MonthlyIncome >= 0 (use greater_than_or_equal_to to allow zero)
    expect_if_exists(df_ge, "MonthlyIncome", "expect_column_values_to_be_greater_than_or_equal_to", 0)
    expect_if_exists(df_ge, "TotalWorkingYears", "expect_column_values_to_be_greater_than_or_equal_to", 0)

    # ENCODING CHECK (DBT output binary flags)
    expect_if_exists(df_ge, "OverTime_Yes", "expect_column_values_to_be_in_set", [0, 1])
    expect_if_exists(df_ge, "Gender_Male", "expect_column_values_to_be_in_set", [0, 1])

    results = df_ge.validate()
    return results

# EXECUTION
results = validate_ml_ready(df)

# LOGIQUE DE PIPELINE
os.makedirs("reports", exist_ok=True)
report_path = os.path.join("reports", "ml_ready_validation.json")

with open(report_path, "w") as f:
    json.dump(results, f, indent=2, default=str)

if results.get("success"):
    print("Dataset ML-ready — prêt pour training")
    print(f"Validation report saved to {report_path}")
    exit_code = 0
else:
    print("Dataset NON ML-ready — correction nécessaire")
    print(f"Validation report saved to {report_path}")
    exit_code = 1

# fermeture connexion
ctx.close()

if __name__ == "__main__":
    raise SystemExit(exit_code)