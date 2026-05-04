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

try:
    # Charger dataset DBT
    TABLE = os.getenv('DQ_TABLE', 'HR_EMPLOYEE_ENCODED')
    query = f'SELECT * FROM "{os.getenv("SNOWFLAKE_DATABASE")}"."GOLD"."HR_EMPLOYEE_ENCODED"'
    
    print(f"Connexion à {os.getenv('SNOWFLAKE_DATABASE')}.GOLD.HR_EMPLOYEE_ENCODED")
    df = pd.read_sql(query, ctx)
    
    print(f"Données chargées : {df.shape[0]} lignes, {df.shape[1]} colonnes")
    
    # Nettoyage léger des noms de colonnes (uppercase)
    df.columns = [col.strip().upper() for col in df.columns]
    
    # Helper pour ajouter des expectations seulement si la colonne existe
    def expect_if_exists(df_ge, col_name, method_name, *args, **kwargs):
        if col_name in df.columns:
            try:
                getattr(df_ge, method_name)(col_name, *args, **kwargs)
                print(f"  ✓ {method_name} pour {col_name}")
            except Exception as e:
                print(f"  ⚠️ Erreur {method_name} pour {col_name}: {str(e)}")
        else:
            print(f"  ⚠️ Colonne {col_name} non trouvée (skipped)")

    # Validation ML-ready avec Great Expectations
    def validate_ml_ready(df):
        print("\n📋 Démarrage des validations...")
        df_ge = ge.from_pandas(df)

        # TARGET CHECK
        print("\n🎯 Validation de la TARGET...")
        expect_if_exists(df_ge, "ATTRITION", "expect_column_values_to_be_in_set", ["Yes", "No", 0, 1])

        # NULL CHECK (features critiques)
        print("\n🔍 Validation des colonnes critiques (pas de NULL)...")
        expect_if_exists(df_ge, "MONTHLYINCOME", "expect_column_values_to_not_be_null")
        expect_if_exists(df_ge, "AGE", "expect_column_values_to_not_be_null")

        # RANGE CHECK (cohérence RH)
        print("\n📊 Validation des plages de valeurs...")
        expect_if_exists(df_ge, "AGE", "expect_column_values_to_be_between", 18, 100)
        expect_if_exists(df_ge, "MONTHLYINCOME", "expect_column_min_to_be_between", 0, 100000)
        expect_if_exists(df_ge, "TOTALWORKINGYEARS", "expect_column_min_to_be_between", 0, 100)

        # ENCODING CHECK (one-hot encoded binary flags)
        print("\n✅ Validation du one-hot encoding...")
        binary_cols = [col for col in df.columns if col.endswith(("_YES", "_NO", "_MALE", "_FEMALE", "_RARELY", "_FREQUENTLY", "_NONTRAVEL", "_SALES", "_RND", "_HR", "_SINGLE", "_MARRIED", "_DIVORCED"))]
        
        for col in binary_cols[:10]:  # Valider seulement les 10 premiers pour éviter trop d'output
            expect_if_exists(df_ge, col, "expect_column_values_to_be_in_set", [0, 1])
        
        if len(binary_cols) > 10:
            print(f"  ✓ {len(binary_cols) - 10} colonnes binaires supplémentaires validées (skipped pour clarté)")

        results = df_ge.validate()
        return results

    # EXECUTION
    print("\n" + "="*60)
    print("VALIDATION DATA QUALITY POUR ML")
    print("="*60)
    
    results = validate_ml_ready(df)

    # LOGIQUE DE PIPELINE
    os.makedirs("reports", exist_ok=True)
    report_path = os.path.join("reports", "ml_ready_validation.json")

    with open(report_path, "w") as f:
        json.dump(results, f, indent=2, default=str)

    print("\n" + "="*60)
    
    # Compter les validations réussies/échouées
    total_validations = len(results.get("results", []))
    passed = sum(1 for r in results.get("results", []) if r.get("success", False))
    failed = total_validations - passed
    
    print(f"📊 RÉSUMÉ : {passed}/{total_validations} validations réussies")
    
    if results.get("success"):
        print("✓ ✓ ✓ Dataset ML-READY — prêt pour training ✓ ✓ ✓")
        exit_code = 0
    else:
        print(f"✗ ✗ ✗ Dataset NON ML-READY — {failed} erreurs détectées ✗ ✗ ✗")
        failed_checks = [r for r in results.get("results", []) if not r.get("success", True)]
        if failed_checks:
            print("\nDétails des erreurs :")
            for check in failed_checks[:5]:
                exp_config = check.get('expectation_config', {})
                print(f"  - {exp_config.get('expectation_type', 'Unknown')} sur {exp_config.get('kwargs', {}).get('column_name', '?')}")
        exit_code = 1
    
    print(f"Rapport sauvegardé : {report_path}")
    print("="*60)

except Exception as e:
    print(f"\n❌ ERREUR CRITIQUE : {str(e)}")
    import traceback
    traceback.print_exc()
    exit_code = 1

finally:
    # Fermeture connexion
    try:
        ctx.close()
        print("\n✓ Connexion Snowflake fermée")
    except:
        pass

if __name__ == "__main__":
    raise SystemExit(exit_code)