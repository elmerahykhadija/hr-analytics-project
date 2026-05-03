import pandas as pd
from snowflake.connector.pandas_tools import write_pandas
import snowflake.connector
import os
from dotenv import load_dotenv
import great_expectations as ge

# Charger les variables du fichier .env
load_dotenv()

# 1. Connexion à Snowflake avec tes paramètres
ctx = snowflake.connector.connect(
    user=os.getenv('SNOWFLAKE_USER'),
    password=os.getenv('SNOWFLAKE_PASS'),
    account=os.getenv('SNOWFLAKE_ACCOUNT'),
    warehouse=os.getenv('SNOWFLAKE_WAREHOUSE'),
    database=os.getenv('SNOWFLAKE_DATABASE'),
    schema='RAW',
    role=os.getenv('SNOWFLAKE_ROLE')
)
def validate_data(df):

    df_ge = ge.from_pandas(df)

    # -------------------------
    # 🎯 Règles RH (IMPORTANT)
    # -------------------------

    # 1. AGE
    df_ge.expect_column_values_to_be_between("Age", 18, 65)

    # 2. ATTRITION
    df_ge.expect_column_values_to_be_in_set("Attrition", ["Yes", "No"])

    # 3. SALAIRE & REVENUS (supérieur ou égal à 1)
    df_ge.expect_column_values_to_be_greater_than_or_equal_to("MonthlyIncome", 1)
    df_ge.expect_column_values_to_be_greater_than_or_equal_to("HourlyRate", 1)
    df_ge.expect_column_values_to_be_greater_than_or_equal_to("DailyRate", 1)
    df_ge.expect_column_values_to_be_greater_than_or_equal_to("MonthlyRate", 1)

    # 4. ANNÉES DE TRAVAIL (positif)
    df_ge.expect_column_values_to_be_greater_than_or_equal_to("YearsAtCompany", 0)
    df_ge.expect_column_values_to_be_greater_than_or_equal_to("YearsInCurrentRole", 0)
    df_ge.expect_column_values_to_be_greater_than_or_equal_to("YearsSinceLastPromotion", 0)
    df_ge.expect_column_values_to_be_greater_than_or_equal_to("YearsWithCurrManager", 0)
    df_ge.expect_column_values_to_be_greater_than_or_equal_to("TotalWorkingYears", 0)

    # 5. SATISFACTION & ENGAGEMENT (1-4 généralement)
    df_ge.expect_column_values_to_be_between("EnvironmentSatisfaction", 1, 4)
    df_ge.expect_column_values_to_be_between("JobSatisfaction", 1, 4)
    df_ge.expect_column_values_to_be_between("JobInvolvement", 1, 4)
    df_ge.expect_column_values_to_be_between("WorkLifeBalance", 1, 4)
    df_ge.expect_column_values_to_be_between("RelationshipSatisfaction", 1, 4)

    # 6. NIVEAU & RATING
    df_ge.expect_column_values_to_be_between("JobLevel", 1, 5)
    df_ge.expect_column_values_to_be_between("PerformanceRating", 3, 4)

    # 7. HIKE & STOCK
    df_ge.expect_column_values_to_be_between("PercentSalaryHike", 0, 25)
    df_ge.expect_column_values_to_be_between("StockOptionLevel", 0, 3)

    # 8. COLONNES CATÉGORIELLES
    df_ge.expect_column_values_to_be_in_set("Gender", ["Male", "Female"])
    df_ge.expect_column_values_to_be_in_set("OverTime", ["Yes", "No"])

    # 9. DISTANCE (km, probablement)
    df_ge.expect_column_values_to_be_greater_than_or_equal_to("DistanceFromHome", 0)

    results = df_ge.validate()

    return results, df
try:
    # 2. Lecture du fichier CSV
    df = pd.read_csv('app/data/data.csv')
    df.columns = [col.strip() for col in df.columns]

    # Suppression des doublons
    df = df.drop_duplicates().reset_index(drop=True)

    # 3. Validation
    results, df = validate_data(df)
    os.makedirs('reports', exist_ok=True)

    if not results.get('success', False):
        import json
        report_path = 'reports/ge_validation.json'
        with open(report_path, 'w') as f:
            json.dump(results, f, default=str, indent=2)
        print(f"Validation échouée — rapport enregistré : {report_path}. Aucune insertion dans Snowflake.")
    else:
        # 4. Insertion directe dans la table existante
        success, nchunks, nrows, _ = write_pandas(
            conn=ctx,
            df=df,
            table_name='HR_RAW_DATA',
            database='RH_DB',
            schema='RAW',
            auto_create_table=False
        )

        if success:
            print(f"Succès : {nrows} lignes insérées directement dans RH_DB.RAW.HR_RAW_DATA.")
        else:
            print("Échec de l'insertion avec write_pandas.")

finally:
    ctx.close()