import pandas as pd
from snowflake.connector.pandas_tools import write_pandas
import snowflake.connector
import os
from dotenv import load_dotenv

# Charger les variables du fichier .env[cite: 2]
load_dotenv()

# 1. Connexion à Snowflake avec tes paramètres[cite: 2]
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
    # Chemin relatif dans le conteneur Docker[cite: 3]
    df = pd.read_csv('data/data.csv')

    # IMPORTANT : On ne change pas la casse si ton CSV correspond déjà, 
    # mais on s'assure que l'ordre et les noms matchent ta commande CREATE TABLE.
    # Si ton CSV a des noms comme 'age' au lieu de 'Age', décommente la ligne suivante :
    # df.columns = [col.capitalize() for col in df.columns]

    # 3. Insertion directe dans la table existante
    # auto_create_table=False garantit qu'on n'essaie pas de créer une nouvelle table
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

finally:
    ctx.close()