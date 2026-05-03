import pandas as pd
from snowflake.connector.pandas_tools import write_pandas
import snowflake.connector
import os
import json
from dotenv import load_dotenv

load_dotenv()

def validate_row(row):
    """
    Valide une ligne individuellement.
    Retourne True si valide, False sinon.
    """
    try:
        # 1. AGE (18-65)
        if not (18 <= row['AGE'] <= 65):
            return False, f"AGE hors limites: {row['AGE']}"
        
        # 2. ATTRITION (Yes/No)
        if row['ATTRITION'] not in ['Yes', 'No']:
            return False, f"ATTRITION invalide: {row['ATTRITION']}"
        
        # 3. SALAIRE > 1
        salary_cols = ['MONTHLYINCOME', 'HOURLYRATE', 'DAILYRATE', 'MONTHLYRATE']
        for col in salary_cols:
            if pd.notna(row[col]) and row[col] <= 0:
                return False, f"{col} <= 0: {row[col]}"
        
        # 4. ANNÉES >= 0
        years_cols = [
            'YEARSATCOMPANY', 'YEARSINCURRENTROLE',
            'YEARSSINCELASTPROMOTION', 'YEARSWITHCURRMANAGER',
            'TOTALWORKINGYEARS'
        ]
        for col in years_cols:
            if pd.notna(row[col]) and row[col] < 0:
                return False, f"{col} < 0: {row[col]}"
        
        # 5. SATISFACTION (1-4)
        sat_cols = [
            'ENVIRONMENTSATISFACTION', 'JOBSATISFACTION',
            'JOBINVOLVEMENT', 'WORKLIFEBALANCE',
            'RELATIONSHIPSATISFACTION'
        ]
        for col in sat_cols:
            if pd.notna(row[col]) and not (1 <= row[col] <= 4):
                return False, f"{col} hors [1,4]: {row[col]}"
        
        # 6. NIVEAU & RATING
        if pd.notna(row['JOBLEVEL']) and not (1 <= row['JOBLEVEL'] <= 5):
            return False, f"JOBLEVEL hors [1,5]: {row['JOBLEVEL']}"
        if pd.notna(row['PERFORMANCERATING']) and not (3 <= row['PERFORMANCERATING'] <= 4):
            return False, f"PERFORMANCERATING hors [3,4]: {row['PERFORMANCERATING']}"
        
        # 7. HIKE & STOCK
        if pd.notna(row['PERCENTSALARYHIKE']) and not (0 <= row['PERCENTSALARYHIKE'] <= 25):
            return False, f"PERCENTSALARYHIKE hors [0,25]: {row['PERCENTSALARYHIKE']}"
        if pd.notna(row['STOCKOPTIONLEVEL']) and not (0 <= row['STOCKOPTIONLEVEL'] <= 3):
            return False, f"STOCKOPTIONLEVEL hors [0,3]: {row['STOCKOPTIONLEVEL']}"
        
        # 8. CATÉGORIELLES
        if row['GENDER'] not in ['Male', 'Female']:
            return False, f"GENDER invalide: {row['GENDER']}"
        if row['OVERTIME'] not in ['Yes', 'No']:
            return False, f"OVERTIME invalide: {row['OVERTIME']}"
        
        # 9. DISTANCE >= 0
        if pd.notna(row['DISTANCEFROMHOME']) and row['DISTANCEFROMHOME'] < 0:
            return False, f"DISTANCEFROMHOME < 0: {row['DISTANCEFROMHOME']}"
        
        return True, None
        
    except Exception as e:
        return False, str(e)

# 1. Connexion à Snowflake
ctx = snowflake.connector.connect(
    user=os.getenv('SNOWFLAKE_USER'),
    password=os.getenv('SNOWFLAKE_PASS'),
    account=os.getenv('SNOWFLAKE_ACCOUNT'),
    warehouse=os.getenv('SNOWFLAKE_WAREHOUSE'),
    database=os.getenv('SNOWFLAKE_DATABASE'),
    schema='RAW',
    role=os.getenv('SNOWFLAKE_ROLE')
)

try:
    # 2. Lecture du fichier CSV
    print("📖 Lecture du CSV...")
    df = pd.read_csv('app/data/data.csv')
    print(f"   {len(df)} lignes lues")
    
    # Normalisation des colonnes
    df.columns = [col.strip().upper() for col in df.columns]

    # Suppression des doublons
    print("🧹 Suppression des doublons...")
    df_before = len(df)
    df = df.drop_duplicates().reset_index(drop=True)
    print(f"   {df_before} → {len(df)} lignes (supprimés: {df_before - len(df)})")

    # 3. Validation ligne par ligne
    print("✔️  Validation ligne par ligne...")
    valid_rows = []
    invalid_rows = []
    
    for idx, row in df.iterrows():
        is_valid, error_msg = validate_row(row)
        if is_valid:
            valid_rows.append(row)
        else:
            invalid_rows.append({
                'row_index': idx,
                'error': error_msg,
                **row.to_dict()
            })
    
    df_valid = pd.DataFrame(valid_rows)
    os.makedirs('reports', exist_ok=True)
    
    print(f"   ✅ Valides: {len(df_valid)}")
    print(f"   ❌ Invalides: {len(invalid_rows)}")
    
    # Enregistrer rapport des rejets
    if invalid_rows:
        report_path = 'reports/rejected_rows.json'
        with open(report_path, 'w') as f:
            json.dump(invalid_rows, f, default=str, indent=2)
        print(f"   Rapport rejet: {report_path}")
    
    if len(df_valid) == 0:
        print("❌ Aucune ligne valide. Aucune insertion.")
    else:
        # 4. Insertion Snowflake (seulement les lignes valides)
        print("📤 Insertion dans Snowflake...")
        try:
            success, nchunks, nrows, _ = write_pandas(
                conn=ctx,
                df=df_valid,
                table_name='HR_RAW_DATA',
                database='RH_DB',
                schema='RAW',
                auto_create_table=False
            )

            if success:
                print(f"🚀 Succès! {nrows} lignes insérées en {nchunks} chunk(s)")
            else:
                print("⚠️  Insertion retourna False")
        except Exception as insert_err:
            print(f"💥 Erreur insertion: {str(insert_err)}")

except Exception as e:
    print(f"💥 Erreur critique: {str(e)}")
    import traceback
    traceback.print_exc()

finally:
    ctx.close()