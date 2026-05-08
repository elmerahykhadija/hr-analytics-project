# Système Prédictif d'Attrition RH - MLOps Pipeline

## 📋 Vue d'ensemble

Ce projet implémente une solution MLOps complète et production-ready pour la **prédiction d'attrition des employés**. Il combine des technologies modernes (Snowflake, dbt, Great Expectations, MLflow, Prefect) pour construire un pipeline de données robuste, automatisé et hautement fiable.

L'objectif principal est d'**identifier proactivement les employés à risque de départ** afin de permettre aux équipes RH d'implémenter des stratégies de rétention ciblées et efficaces.

---

## 🎯 Objectifs du projet

1. **Prédiction précise d'attrition** - Développer un modèle ML performant capable de classifier le risque d'attrition avec une F1-Score optimisée
2. **Automatisation complète** - Orchestrer l'ensemble du pipeline (ingestion, transformation, validation, entraînement) de façon autonome et planifiée
3. **Qualité de données garantie** - Valider systématiquement la qualité et la cohérence des données à chaque étape
4. **Expérimentation tracée** - Tracker toutes les itérations du modèle, les performances et les hyperparamètres pour la reproductibilité
5. **Interface utilisateur accessible** - Fournir un dashboard interactif permettant la simulation de risque d'attrition
6. **Scalabilité et maintenabilité** - Architecture modulaire et containerisée pour faciliter l'évolution et le déploiement

---

## 🔄 Flux du Pipeline MLOps

Le pipeline est organisé en **5 étapes clés** exécutées en séquence :

### **1. Ingestion des données (Data Import)**
- **Source** : Fichier CSV (`app/data/data.csv`)
- **Destination** : Snowflake schema `RAW`
- **Validations** :
  - Vérification des plages de valeurs (âge 18-65, salaires > 0, années ≥ 0)
  - Validation des énumérations (Attrition: Yes/No, Gender: Male/Female, etc.)
  - Détection et suppression des doublons
  - Nettoyage des données manquantes
- **Sortie** : Table `HR_RAW_DATA` prête pour la transformation

### **2. Transformation et Feature Engineering (dbt)**
- **Outil** : dbt (data build tool) - transformations SQL reproducibles
- **Processus** :
  - Nettoyage des données brutes (`hr_employee_cleaned.sql`)
  - One-hot encoding des variables catégorielles (BusinessTravel, Department, Gender, MaritalStatus, OverTime)
  - Encodage des variables numériques
  - Sélection et création des features pertinentes
- **Destination** : Snowflake schema `GOLD`
- **Sortie** : Table `HR_EMPLOYEE_ENCODED` prête pour le ML

### **3. Validation de la Qualité des Données (Data Quality)**
- **Outil** : Great Expectations
- **Validations exécutées** :
  - Vérification des valeurs cibles (target `ATTRITION` uniquement Yes/No)
  - Détection des valeurs NULL sur les colonnes critiques
  - Validation des plages de valeurs (cohérence RH)
  - Vérification du one-hot encoding (colonnes binaires = 0 ou 1)
  - Conformité ML-ready
- **Rapport** : `reports/ml_ready_validation.json`
- **Condition de passage** : Dataset doit passer 100% des validations avant entraînement

### **4. Entraînement et Promotion du Modèle (ML Training)**
- **Algorithme** : RandomForest Classifier (18 features sélectionnées)
- **Processus** :
  - Split 80/20 (train/test) avec stratification sur la target
  - Hypertuning par GridSearchCV (5-fold cross-validation)
  - Optimisation de la F1-Score
  - Calcul de l'importance des features
- **Comparaison vs Production** : Le nouveau modèle ne remplace le modèle en production que s'il surpasse la F1-Score existante
- **Tracking** : MLflow enregistre params, métriques et artefacts
- **Promotion** : Meilleur modèle automatiquement promu en stage "Production"

### **5. Orchestration du Pipeline (Prefect)**
- **Déclenchement** : Exécution quotidienne à heure fixe via Prefect
- **Resilience** : Retry automatique sur erreur (30 secondes délai)
- **Logging** : Journalisation complète de chaque étape
- **Gestion d'erreurs** : Pipeline s'arrête à la première erreur critique
- **Statut** : Notifications d'exécution (succès/échec)

---

## 🛠 Technologies et Rôles

| Technologie | Rôle | Version |
|---|---|---|
| **Snowflake** | Cloud Data Warehouse - Stockage centralisé des données brutes et transformées | Enterprise |
| **dbt** | Transformation ELT - Modélisation et transformation SQL reproducible | 1.x+ |
| **Great Expectations** | Data Quality Framework - Validation et assertion sur les données | 0.15+ |
| **Python 3.11** | Langage de programmation - Ingestion, ML, orchestration | 3.11 |
| **scikit-learn** | ML Framework - Implémentation RandomForest et métriques | 1.x+ |
| **MLflow** | ML Ops - Tracking d'expériences, registry de modèles, model serving | 2.13+ |
| **Prefect** | Workflow Orchestration - Orchestration et scheduling du pipeline | 2.19+ |
| **Dash** | Web Framework - Dashboard interactif pour simulation d'attrition | 2.x+ |
| **Docker & Docker Compose** | Containerisation - Déploiement localisé et reproducible | Latest |
| **Pandas, NumPy** | Data Processing - Manipulation et analyse des données | Latest |

---

## 📊 Features du Modèle

Le modèle utilise **18 features** sélectionnées et one-hot encodées :

**Numériques** :
- `AGE` - Âge de l'employé
- `DISTANCEFROMHOME` - Distance domicile-travail (km)
- `EDUCATION` - Niveau d'étude
- `MONTHLYINCOME` - Salaire mensuel
- `TOTALWORKINGYEARS` - Expérience totale

**Catégorielles (one-hot encodées)** :
- `BUSINESSTRAVEL_RARELY`, `BUSINESSTRAVEL_FREQUENTLY`, `BUSINESSTRAVEL_NONTRAVEL`
- `DEPARTMENT_SALES`, `DEPARTMENT_RND`, `DEPARTMENT_HR`
- `GENDER_MALE`, `GENDER_FEMALE`
- `MARITALSTATUS_SINGLE`, `MARITALSTATUS_MARRIED`, `MARITALSTATUS_DIVORCED`
- `OVERTIME_YES`, `OVERTIME_NO`

**Target** : `ATTRITION` (1 = attrition, 0 = retention)

---

## 🚀 Démarrage et Installation

### **Prérequis**
- Docker & Docker Compose
- Python 3.11+
- Snowflake Account (credentials)
- Fichier CSV de données RH

### **Étape 1 : Configuration des variables d'environnement**

Créer un fichier `.env` à la racine du projet :

```bash
# Snowflake Configuration
SNOWFLAKE_USER=your_username
SNOWFLAKE_PASS=your_password
SNOWFLAKE_ACCOUNT=your_account_id
SNOWFLAKE_DATABASE=RH_DB
SNOWFLAKE_SCHEMA=GOLD
SNOWFLAKE_WAREHOUSE=RH_WH
SNOWFLAKE_ROLE=ACCOUNTADMIN

# dbt Configuration
DBT_PROFILES_DIR=dbt_hr_project

# MLflow Configuration (automatique via Docker)
MLFLOW_TRACKING_URI=http://mlflow:5000

# Prefect Configuration (automatique via Docker)
PREFECT_API_URL=http://prefect:4200/api
```

### **Étape 2 : Initialiser la base de données Snowflake**

Exécuter le script SQL de création :

```bash
# Depuis Snowflake Web UI ou CLI
snowsql -f creation_de_db_snowflake.sql
```

Ce script crée :
- Warehouse `RH_WH`
- Database `RH_DB`
- Schemas `RAW` et `GOLD`
- Table `HR_RAW_DATA`

### **Étape 3 : Démarrer les services Docker**

```bash
docker-compose -f docker/docker-compose.yml up -d
```

Cela démarre :
- **hr_mlops_app** : Application principale (ports 8000, 8050)
- **mlflow** : Tracking d'expériences (port 5000)
- **prefect** : Orchestration (port 4200)

### **Étape 4 : Vérifier les services**

```bash
# MLflow UI
http://localhost:5000

# Prefect UI
http://localhost:4200

# Application Dashboard
http://localhost:8050
```

---

## 📈 Exécution du Pipeline

### **Manuel - Exécuter tous les composants**

```bash
# Ingestion
python3 app/ingest.py

# Transformation (dbt)
dbt run --project-dir dbt_hr_project --profiles-dir dbt_hr_project

# Validation
python3 app/dataquality.py

# Entraînement
python3 app/train.py
```

### **Orchestré - Via Prefect (Recommandé)**

```bash
# Démarrer le scheduler Prefect
python3 app/flow.py

# Le pipeline s'exécutera automatiquement selon le calendrier défini
# Suivi en temps réel via http://localhost:4200
```

### **Mode continu**

Le pipeline est configuré pour s'exécuter **quotidiennement à heure fixe**. Les résultats sont persistés dans MLflow et les artefacts archivés.

---

## 📊 Monitoring et Reporting

### **MLflow Dashboard**
- Accès : `http://localhost:5000`
- **Suivi** : Toutes les runs d'entraînement avec hyperparamètres et métriques
- **Comparaison** : Side-by-side comparison de modèles
- **Registry** : État et version du modèle en production

### **Prefect Dashboard**
- Accès : `http://localhost:4200`
- **Scheduling** : Visualisation des exécutions du pipeline
- **Logs** : Détails de chaque étape et dépannage

### **Rapports de Qualité**
- **Chemin** : `reports/ml_ready_validation.json`
- **Contenu** : Résultats détaillés des validations Great Expectations
- **Fréquence** : Généré à chaque exécution

### **Dashboard d'Application**
- Accès : `http://localhost:8050`
- **Fonctionnalité** : Simulation de prédiction d'attrition par employé

---

## 📁 Structure Logique du Projet

```
projet-RH/
├── app/                          # Code applicatif
│   ├── ingest.py                # Ingestion CSV → Snowflake RAW
│   ├── flow.py                  # Orchestration Prefect
│   ├── dataquality.py           # Validation Great Expectations
│   ├── train.py                 # ML Training et model registry
│   ├── simulation_service.py    # Service de prédiction
│   ├── dashboard.py             # Interface Dash
│   └── data/data.csv            # Données source
│
├── dbt_hr_project/              # Transformations dbt
│   ├── dbt_project.yml          # Configuration dbt
│   ├── profiles.yml             # Connexion Snowflake
│   ├── models/                  # SQL transformations
│   │   ├── hr_employee_cleaned.sql
│   │   └── hr_employee_encoded.sql
│   └── macros/                  # Fonctions réutilisables
│
├── docker/                      # Containerisation
│   ├── Dockerfile              # Image application
│   ├── docker-compose.yml       # Orchestration services
│   └── requirements.txt         # Dépendances Python
│
├── reports/                     # Rapports générés
│   └── ml_ready_validation.json
│
├── mlruns/                      # MLflow artifacts
│
└── creation_de_db_snowflake.sql # Setup base de données
```

---

## 🔐 Sécurité et Bonnes Pratiques

1. **Variables d'environnement** : Toutes les credentials stockées dans `.env` (non versionné)
2. **Snowflake Roles** : Utiliser des rôles restreints (pas ACCOUNTADMIN en prod)
3. **Data Governance** : Audit trails des transformations dbt
4. **Model Versioning** : MLflow assure la traçabilité complète des modèles
5. **Data Quality Gates** : Pipeline bloqué si validations échouent
6. **Orchestration Resilience** : Retry automatique et alertes sur erreurs

---

## 📊 Métriques et Performance

**Entraînement** :
- F1-Score optimisée via GridSearchCV
- Cross-validation 5-fold
- Class weighting pour gérer les données déséquilibrées

**Qualité de Données** :
- Taux de completeness des données critiques
- Détection des anomalies et outliers
- Conformité aux schémas attendus

**Pipeline** :
- Temps d'exécution par étape
- Taux de succès des validations
- Latence end-to-end

---

## 🐛 Dépannage

| Problème | Cause Probable | Solution |
|---|---|---|
| Erreur connexion Snowflake | Credentials incorrectes | Vérifier `.env` et permissions Snowflake |
| dbt models ne compilent pas | Schéma n'existe pas | Exécuter `creation_de_db_snowflake.sql` |
| Pipeline bloqué en Data Quality | Données invalides | Consulter `reports/ml_ready_validation.json` |
| MLflow UI inaccessible | Service mlflow down | `docker-compose ps` et redémarrer |
| Modèle n'est pas promu | F1-Score du nouveau modèle < ancien | C'est normal, vérifier les améliorations |

---

## 📞 Support et Contribution

Pour toute question ou amélioration du pipeline :
- Consulter les logs dans `mlruns/` et `reports/`
- Vérifier les détails d'exécution sur Prefect Dashboard
- Analyser les runs MLflow pour debug des modèles

---

## 📄 Licence et Confidentialité

Projet confidentiel - Données RH sensibles. Accès restreint aux équipes autorisées.

---

**Dernière mise à jour** : Mai 2026 | **Version** : 1.0.0