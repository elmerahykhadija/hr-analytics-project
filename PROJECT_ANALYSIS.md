# Projet-RH: Comprehensive Project Analysis

## 📋 Executive Summary

**Projet-RH** is an enterprise-grade ML/Data Engineering pipeline for **HR Employee Attrition Prediction**. It combines data ingestion, data quality validation, feature engineering, machine learning model training, data drift detection, and interactive dashboard visualization using a modern data stack architecture.

---

## 1. Main Objectives & Use Case

### Primary Goal
Predict and mitigate **employee attrition** using machine learning, enabling HR departments to:
- Identify high-risk employees for retention interventions
- Understand key factors driving employee turnover
- Generate data-driven counterfactual scenarios for HR interventions
- Monitor data drift in production to ensure model reliability

### Business Impact
- **Reduce employee turnover** through early intervention
- **Optimize HR strategy** using predictive insights
- **Calculate ROI** on retention initiatives
- **Minimize hiring/training costs** by preventing valuable employee departures

### Target Users
- HR Business Partners
- Data Scientists & Analytics Teams
- C-Level executives monitoring employee retention KPIs

---

## 2. Technology Stack

### Core Technologies

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **Data Warehouse** | Snowflake | Latest | Cloud-based data storage & SQL execution |
| **Orchestration** | Prefect | 2.19.5 | Workflow scheduling & monitoring |
| **Data Transformation** | dbt | 1.8.0 | ELT pipeline & data modeling |
| **ML Framework** | scikit-learn | 1.5.1 | Random Forest classifier training |
| **ML Tracking** | MLflow | 2.13.0 | Model versioning, tracking, registry |
| **Data Quality** | Great Expectations | 0.18.15 | Data validation & testing |
| **Data Drift** | Evidently | 0.4.32 | Production ML monitoring |
| **Explainability** | DICE-ML | Latest | Counterfactual explanations |
| **Dashboard** | Dash/Plotly | 2.17.1 / 5.23.0 | Interactive web UI |
| **Orchestration** | Docker | Latest | Containerization & deployment |

### Languages & Libraries
- **Python 3.11** (runtime)
- **pandas, numpy, scikit-learn** (data science)
- **Snowflake-connector-python** (Snowflake integration)
- **sqlalchemy** (ORM & database abstraction)
- **dash-bootstrap-components** (UI framework)

---

## 3. Project Architecture

### High-Level Data Flow

```
Raw Data (CSV)
    ↓
[1] INGEST (ingest.py)
    ├─ CSV Load & Validation
    ├─ Duplicate Removal
    ├─ Rule-Based Row Validation
    └─ Insert → Snowflake RAW schema
    ↓
[2] TRANSFORM (dbt run)
    ├─ hr_employee_cleaned.sql (imputation, cleaning)
    ├─ hr_employee_encoded.sql (one-hot encoding)
    └─ Output → Snowflake GOLD schema
    ↓
[3] DATA QUALITY (dataquality.py)
    ├─ Great Expectations validation
    ├─ ML-ready checks
    └─ Report generation
    ↓
[4] DRIFT & TRAIN (monitoring-training.py)
    ├─ Evidently drift detection
    ├─ Random Forest training (train.py)
    ├─ Hyperparameter tuning (GridSearchCV)
    ├─ MLflow experiment tracking
    └─ Model registry
    ↓
[5] SERVE & EXPLAIN
    ├─ Dashboard (dashboard.py)
    ├─ Predictions (simulation_service.py)
    └─ Counterfactuals (dice.py)
```

### Architecture Components

```
PROJECT-RH/
├─ app/                          # Python application layer
│  ├─ ingest.py                  # Data ingestion & validation
│  ├─ train.py                   # Model training pipeline
│  ├─ flow.py                    # Prefect orchestration
│  ├─ dataquality.py             # Data quality checks (Great Expectations)
│  ├─ monitoring-training.py     # Data drift detection & training trigger
│  ├─ dice.py                    # Counterfactual explanations
│  ├─ dashboard.py               # Dash web interface
│  ├─ simulation_service.py      # Model serving & predictions
│  ├─ data/                      # Source data (CSV)
│  └─ assets/                    # UI assets (CSS, etc.)
│
├─ dbt_hr_project/               # Data transformation layer
│  ├─ dbt_project.yml            # dbt configuration
│  ├─ profiles.yml               # Snowflake credentials config
│  ├─ models/
│  │  ├─ sources.yml             # Data source definitions
│  │  ├─ hr_employee_cleaned.sql # Cleaning & imputation
│  │  └─ hr_employee_encoded.sql # Feature engineering
│  └─ macros/
│     └─ generate_schema_name.sql # Custom schema logic
│
├─ docker/                       # Container orchestration
│  ├─ Dockerfile                 # Python 3.11 application image
│  ├─ docker-compose.yml         # Multi-container setup
│  └─ requirements.txt           # Python dependencies
│
├─ creation_de_db_snowflake.sql  # Snowflake warehouse setup script
├─ reports/                      # Output artifacts
│  └─ ml_ready_validation.json   # Validation reports
└─ mlruns/                       # MLflow artifacts
```

---

## 4. Python Scripts: Detailed Analysis

### 4.1 ingest.py
**Purpose**: Raw data ingestion with validation

**Key Functions**:
- `validate_row(row)`: Row-level validation logic
  - AGE: 18-65 range check
  - ATTRITION: Yes/No categorical validation
  - Salary columns: Must be > 0
  - Years columns: Must be ≥ 0
  - Satisfaction scores: 1-4 scale validation
  - Job level: 1-5 range
  - Performance rating: 3-4 range
  - Categorical constraints (Gender: Male/Female, OverTime: Yes/No, etc.)

**Process**:
1. Load CSV from `app/data/data.csv`
2. Normalize column names to UPPERCASE
3. Remove duplicates
4. Validate each row against business rules
5. Separate valid/invalid rows
6. Insert valid rows into Snowflake `RH_DB.RAW.HR_RAW_DATA`
7. Export invalid rows to `reports/rejected_rows.json`

**Output**: 
- Snowflake table with validated data
- Rejection report with error details

---

### 4.2 train.py
**Purpose**: ML model training with hyperparameter optimization

**Model Architecture**:
- **Algorithm**: Random Forest Classifier
- **Objective**: Binary classification (Attrition: Yes/No)

**Features (13 + 22 encoded)**:
- **Numerical** (13 features):
  - Demographics: AGE, EDUCATION, DISTANCEFROMHOME
  - Job: JOBLEVEL, MONTHLYINCOME
  - Experience: TOTALWORKINGYEARS, NUMCOMPANIESWORKED
  - Engagement: JOBSATISFACTION, ENVIRONMENTSATISFACTION, RELATIONSHIPSATISFACTION, JOBINVOLVEMENT, WORKLIFEBALANCE, PERFORMANCERATING

- **Categorical (One-Hot Encoded)** (22 features):
  - GENDER_MALE, GENDER_FEMALE
  - MARITALSTATUS_SINGLE, MARITALSTATUS_MARRIED, MARITALSTATUS_DIVORCED
  - BUSINESSTRAVEL_NONTRAVEL, BUSINESSTRAVEL_RARELY, BUSINESSTRAVEL_FREQUENTLY
  - OVERTIME_NO, OVERTIME_YES
  - (Plus additional department, role, education field encodings)

**Training Pipeline**:
```python
# Hyperparameter Grid
param_grid = {
    "n_estimators": [100, 200, 300],
    "max_depth": [5, 10, 15],
    "min_samples_split": [2, 5, 10],
    "min_samples_leaf": [1, 2, 4],
    "max_features": ["sqrt", "log2"]
}

# Cross-Validation Strategy
StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

# Optimization Metric
GridSearchCV(scoring="f1")
```

**Key Metrics**:
- **Best CV F1 Score**: Logged in MLflow
- **Test Accuracy**: Accuracy_score on holdout set
- **Test F1 Score**: F1_score on predictions
- **Feature Importance**: Top 15 features ranked by importance

**Output**:
- Best model registered in MLflow Model Registry
- Feature importance dataframe
- Cross-validation metrics

---

### 4.3 flow.py
**Purpose**: Prefect orchestration DAG

**Pipeline Steps**:
1. **ingest_data()**: Run ingest.py with retry logic
2. **prepare_data()**: Execute `dbt run` for data transformation
3. **data_quality_check()**: Validate ML-ready data quality
4. **datadrifting_training()**: Detect drift & train model

**Execution**:
- Daily execution via `hr_attrition_flow.serve(interval=timedelta(days=1))`
- Retry mechanism: 1 retry with 30-second delay per task
- Error handling: Subprocess capture & logging

**Prefect Integration**:
- Task decorator for individual steps
- Flow decorator for orchestration
- Automatic state tracking & error reporting

---

### 4.4 dataquality.py
**Purpose**: ML-ready data validation using Great Expectations

**Validation Checks**:

| Category | Checks |
|----------|--------|
| **Target Validation** | ATTRITION ∈ {Yes, No, 0, 1} |
| **Critical Features** | MONTHLYINCOME & AGE ≠ NULL |
| **Range Checks** | AGE ∈ [18,100], INCOME > 0 |
| **One-Hot Encoding** | Binary columns ∈ {0,1} |
| **Feature Completeness** | All ML features present |

**Output**:
- `reports/ml_ready_validation.json`: Validation results
- Success/failure count summary
- Passed: X/Y validations

---

### 4.5 monitoring-training.py
**Purpose**: Data drift detection + model retraining trigger

**Class**: `DataDriftDetector`

**Workflow**:
1. **Data Fetching**: Load 10,000 most recent records from GOLD schema
2. **Time Series Split**: Group records by ingestion date
3. **Drift Detection Logic**:
   - If **1 day only**: Run training directly
   - If **multiple days**: 
     - Reference data: All historical days combined
     - Current data: Latest day
     - Evidently DataDriftPreset analysis
     - Flag if drift_detected = True

4. **Conditional Training**:
   - Always runs training if single day
   - Trains only if significant drift detected (multi-day)

**Metrics Tracked**:
- Number of records per day
- Drift detection status
- Training completion confirmation

---

### 4.6 dice.py
**Purpose**: Counterfactual explanations for HR intervention

**Key Functions**:

**generate_counterfactuals(input_data)**
- Uses DICE-ML library to generate counterfactuals
- Input: Employee features
- Output: 3 counterfactual scenarios

**generate_smart_counterfactuals(input_data)**
- Context-aware HR scenarios based on business logic
- **Scenario 1**: Telework partial (distance > 25km)
  - Reduces distance by 60%
- **Scenario 2**: Compensatory salary increase
  - Increase: (distance/5) × 1% (capped at 20%)
- **Scenario 3**: Combined telework + salary
  - Distance reduction: 40%
  - Salary increase: 8%
- **Scenario 4**: Eliminate overtime + compensation
  - Remove overtime, +5% salary

---

### 4.7 dashboard.py
**Purpose**: Interactive Dash web application

**UI Design**:
- **Theme**: "Nature Zen" (green/natural palette)
- **Colors**:
  - Primary: #2D7A4F (brand green)
  - Background: #F6F9F4 (light natural)
  - Text: #1C3829 (dark green)

**Components** (Estimated):
- KPI cards (attrition rate, model accuracy, etc.)
- Employee risk profile input form
- Prediction display (risk score, attrition probability)
- Counterfactual scenario explorer
- Feature importance visualization
- Bootstrap responsive layout

**Dependencies**:
- Dash/Plotly for interactivity
- Dash Bootstrap Components for styling
- Integration with `simulation_service` for predictions

---

### 4.8 simulation_service.py
**Purpose**: Model serving and prediction API

**Key Functions**:

**load_model()**
- Connects to MLflow tracking URI: `http://mlflow:5000`
- Loads model: `RF_Attrition_v1/Production` (from registry)
- Caches model in memory for performance

**predict_risk(row_dict)**
- Input: Dictionary with employee attributes
- Validation: Maps input columns to model feature names
- Imputation: Missing features default to 0
- One-hot encoding: Maps categorical values to encoded columns
- Output: `{"risk_score": float, "prediction": str}`
  - risk_score: Probability of attrition [0,1]
  - prediction: "Risque Élevé" (>0.5) or "Risque Faible" (≤0.5)

**Feature Mapping**:
- Numeric: Direct mapping (AGE, MONTHLYINCOME, etc.)
- Categorical: Dictionary-based one-hot encoding
  - GENDER: {"Male" → "GENDER_MALE", "Female" → "GENDER_FEMALE"}
  - MARITALSTATUS: {Single, Married, Divorced}
  - BUSINESSTRAVEL: {Non-Travel, Rarely, Frequently}
  - OVERTIME: {No, Yes}

---

## 5. dbt Project Structure

### 5.1 dbt Configuration

**dbt_project.yml**:
```yaml
name: 'dbt_hr_project'
version: '1.0.0'
profile: 'dbt_hr_project'
model-paths: ["models"]
models:
  dbt_hr_project:
    example:
      +materialized: table
```

**profiles.yml**: Snowflake connection config
- Account, User, Password via environment variables
- Role: Configurable
- Warehouse: Dynamic assignment
- Schema: Dynamic assignment
- Threads: 4 (parallel execution)

**Directory Structure**:
```
dbt_hr_project/
├─ models/
│  ├─ sources.yml          # Data source definitions
│  ├─ hr_employee_cleaned.sql    # Cleaning layer
│  └─ hr_employee_encoded.sql    # ML-ready layer
├─ macros/                  # Custom Jinja templates
├─ tests/                   # Data tests (custom SQL)
├─ seeds/                   # Static data loading
└─ target/                  # Compiled artifacts
```

---

### 5.2 Data Models

#### **Model 1: hr_employee_cleaned.sql**
**Materialization**: Table
**Schema**: RH_DB.GOLD

**Purpose**: Data cleaning with statistical imputation

**Transformations**:
1. **CTE: base**: Raw data selection from HR_RAW_DATA
2. **CTE: stats**: Calculate median for 23 numerical columns
   - Percentile 0.5 (median) for each numeric field
3. **CTE: mode_values**: Modal values for 7 categorical columns
   - Most frequent values for BusinessTravel, Department, Gender, etc.
4. **SELECT**: Main transformation
   - **Target**: Attrition (preserved)
   - **Numerical**: NULL → MEDIAN imputation for 23 features
   - **Categorical**: NULL → MODE imputation for 7 features

**Columns Handled**:
- Age, DailyRate, DistanceFromHome, Education, EnvironmentSatisfaction
- HourlyRate, JobInvolvement, JobLevel, JobSatisfaction, MonthlyIncome
- MonthlyRate, NumCompaniesWorked, PercentSalaryHike, PerformanceRating
- RelationshipSatisfaction, StockOptionLevel, TotalWorkingYears, TrainingTimesLastYear
- WorkLifeBalance, YearsAtCompany, YearsInCurrentRole, YearsSinceLastPromotion
- YearsWithCurrManager, BusinessTravel, Department, EducationField, Gender
- JobRole, MaritalStatus, OverTime

---

#### **Model 2: hr_employee_encoded.sql**
**Materialization**: Table
**Schema**: RH_DB.GOLD
**Depends On**: hr_employee_cleaned.sql

**Purpose**: Feature engineering with one-hot encoding for ML

**Transformations**:
1. **Reference**: Select from hr_employee_cleaned
2. **Preserved Columns**: All numerical features (already cleaned)
   - 24 numerical features retained as-is
3. **One-Hot Encoding**: 22 binary columns created

**Encoded Features**:

| Category | Columns | Example |
|----------|---------|---------|
| **BusinessTravel** | 3 | BusinessTravel_Rarely, BusinessTravel_Frequently, BusinessTravel_NonTravel |
| **Department** | 3 | Department_Sales, Department_RnD, Department_HR |
| **EducationField** | 6 | EducationField_LifeSciences, EducationField_Medical, EducationField_Technical, etc. |
| **Gender** | 2 | Gender_Male, Gender_Female |
| **JobRole** | 9 | JobRole_SalesExecutive, JobRole_Manager, JobRole_ResearchScientist, etc. |
| **MaritalStatus** | 3 | MaritalStatus_Single, MaritalStatus_Married, MaritalStatus_Divorced |
| **OverTime** | 2 | OverTime_Yes, OverTime_No |

**Final Output**: 24 numerical + 28 encoded = 52 total features + ATTRITION target + INGESTIONDATE

---

### 5.3 Source Definitions (sources.yml)

```yaml
sources:
  - name: raw
    database: RH_DB
    schema: RAW
    tables:
      - name: hr_raw_data (maps to HR_RAW_DATA)
        description: "Raw HR data from CSV"
```

---

## 6. Snowflake Database Schema

### Database Structure
```
RH_DB (Database)
├─ RAW (Schema)
│  └─ HR_RAW_DATA (Table)
│     └─ 35 columns + INGESTIONDATE
│
└─ GOLD (Schema)
   ├─ HR_EMPLOYEE_CLEANED (Table, dbt output)
   │  └─ 35 columns with NULL imputation
   │
   └─ HR_EMPLOYEE_ENCODED (Table, dbt output)
      └─ 52 features + ATTRITION + INGESTIONDATE
```

### Warehouse Setup
**creation_de_db_snowflake.sql**:
- Warehouse: RH_WH (XSMALL, auto-suspend 60s, auto-resume enabled)
- Database: RH_DB
- Schemas: RAW, GOLD

### HR_RAW_DATA Table Schema
**35 Columns**:

| Column | Type | Notes |
|--------|------|-------|
| Age | INT | Age range validation in ingest.py |
| Attrition | STRING | Target variable (Yes/No) |
| BusinessTravel | STRING | Travel frequency |
| DailyRate | INT | Hourly wage rate |
| Department | STRING | Sales, R&D, HR |
| DistanceFromHome | INT | Distance in km |
| Education | INT | Education level (1-5) |
| EducationField | STRING | Field of study |
| EmployeeCount | INT | (metadata) |
| EmployeeNumber | INT | Unique employee ID |
| EnvironmentSatisfaction | INT | 1-4 scale |
| Gender | STRING | Male/Female |
| HourlyRate | INT | Hourly pay rate |
| JobInvolvement | INT | 1-4 scale |
| JobLevel | INT | 1-5 range |
| JobRole | STRING | Position (9 types) |
| JobSatisfaction | INT | 1-4 scale |
| MaritalStatus | STRING | Single/Married/Divorced |
| MonthlyIncome | INT | Monthly salary |
| MonthlyRate | INT | Monthly wage |
| NumCompaniesWorked | INT | Number of employers |
| Over18 | STRING | Validation flag |
| OverTime | STRING | Yes/No |
| PercentSalaryHike | INT | Percentage (0-25%) |
| PerformanceRating | INT | 3-4 scale |
| RelationshipSatisfaction | INT | 1-4 scale |
| StandardHours | INT | Weekly hours (40) |
| StockOptionLevel | INT | 0-3 level |
| TotalWorkingYears | INT | Career experience |
| TrainingTimesLastYear | INT | Training count |
| WorkLifeBalance | INT | 1-4 scale |
| YearsAtCompany | INT | Tenure |
| YearsInCurrentRole | INT | Current job tenure |
| YearsSinceLastPromotion | INT | Time since promotion |
| YearsWithCurrManager | INT | Manager tenure |
| IngestionDate | TIMESTAMP | Load timestamp |

---

## 7. Docker Configuration

### docker-compose.yml Services

#### **App Container**
- **Image**: Python 3.11-slim
- **Context**: Project root
- **Ports**: 
  - 8000: API (reserved)
  - 8050: Dash dashboard
- **Volumes**: Entire project mounted at /app
- **Dependencies**: MLflow, Prefect
- **CMD**: `tail -f /dev/null` (keeps container running)
- **Environment**:
  - PREFECT_API_URL=http://prefect:4200/api
  - MLFLOW_TRACKING_URI=http://mlflow:5000
  - Environment variables from .env file

#### **MLflow Container**
- **Image**: ghcr.io/mlflow/mlflow:v2.13.0
- **Port**: 5000
- **Backend**: SQLite (mlflow.db)
- **Artifact Root**: /mlflow/artifacts (mounted to ../mlruns)
- **Purpose**: Model tracking, versioning, registry

#### **Prefect Container**
- **Image**: prefecthq/prefect:2.19.5-python3.11
- **Port**: 4200
- **Command**: `prefect server start --host 0.0.0.0`
- **Purpose**: Workflow orchestration & scheduling

### Dockerfile (Python Application)

```dockerfile
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PREFECT_API_URL=http://prefect:4200/api

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY docker/requirements.txt .
RUN pip install --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["tail", "-f", "/dev/null"]
```

---

## 8. Python Dependencies (requirements.txt)

### Core Data & ML
- **pandas** 1.5.0-1.9.x: Data manipulation
- **numpy** 1.26.4-1.9.x: Numerical computing
- **scikit-learn** 1.5.1: ML algorithms

### Snowflake & Database
- **snowflake-connector-python[pandas]** 3.10.1: Snowflake connectivity
- **snowflake-sqlalchemy** 1.4.x: SQLAlchemy Snowflake dialect
- **sqlalchemy** 1.4.x: ORM & database abstraction

### Data Transformation
- **dbt-snowflake** 1.8.0: dbt Snowflake adapter

### Orchestration & MLOps
- **prefect** 2.19.5: Workflow orchestration
- **mlflow** 2.13.0: ML experiment tracking & registry
- **evidently** 0.4.32: Data drift monitoring
- **pydantic** <2.9.0: Data validation
- **litestar** ≤2.8.3: Web framework (alternative to FastAPI)

### Data Quality
- **great-expectations** 0.18.15: Data validation framework

### Dashboard & Visualization
- **dash** 2.17.1: Web dashboard framework
- **plotly** 5.23.0: Interactive visualizations
- **dash-bootstrap-components**: Bootstrap styling for Dash

### Explainability & Utilities
- **dice-ml**: Counterfactual explanations
- **python-dotenv** 1.0.1: Environment variable management
- **requests** 2.32.3: HTTP library
- **griffe** 0.38.0: Python documentation parser

---

## 9. Machine Learning Pipeline Details

### 9.1 Data Flow for ML

```
CSV Input
   ↓
[Ingest] Validation & Cleaning
   ↓
Snowflake RAW (HR_RAW_DATA)
   ↓
[dbt] hr_employee_cleaned
   ├─ NULL Imputation (Median/Mode)
   └─ Output: RH_DB.GOLD.HR_EMPLOYEE_CLEANED
   ↓
[dbt] hr_employee_encoded
   ├─ One-Hot Encoding
   └─ Output: RH_DB.GOLD.HR_EMPLOYEE_ENCODED (52 features)
   ↓
[Data Quality] Great Expectations Validation
   ├─ Target validation (ATTRITION in {Yes, No})
   ├─ Feature completeness
   ├─ Binary column validation
   └─ Range checks
   ↓
[Drift Detection] Evidently DataDriftPreset
   ├─ Detect distribution shifts
   └─ Trigger training if drift detected
   ↓
[Train] Random Forest with GridSearchCV
   ├─ 80/20 train/test split
   ├─ 5-fold stratified cross-validation
   ├─ Hyperparameter optimization
   └─ Feature importance calculation
   ↓
[MLflow] Model Registry
   ├─ Experiment tracking
   ├─ Metrics logging
   ├─ Model versioning
   └─ Production stage promotion
   ↓
[Serve] Dashboard + API
   ├─ Real-time predictions
   ├─ Counterfactual generation
   └─ Risk scoring
```

### 9.2 Feature Importance

The trained Random Forest provides feature importance scores. Top features typically include:
- **OverTime** (very high impact): Overtime work strongly correlates with attrition
- **MonthlyIncome**: Salary is a key retention factor
- **JobSatisfaction**: High satisfaction reduces attrition
- **DistanceFromHome**: Longer commutes increase attrition risk
- **TotalWorkingYears**: Experience level matters
- **JobLevel**: Career progression impacts retention

### 9.3 Model Metrics

**Training Metrics**:
- **Cross-Validation F1 Score**: Best CV F1 from GridSearchCV
- **Test Accuracy**: Accuracy on holdout test set
- **Test F1 Score**: F1 score on test predictions (class-weighted given imbalance)

**Class Balancing**:
- `class_weight="balanced"` in RandomForestClassifier
- Handles potential class imbalance in attrition (Yes vs No)

**Hyperparameter Tuning**:
- **n_estimators**: [100, 200, 300] trees
- **max_depth**: [5, 10, 15] tree depth
- **min_samples_split**: [2, 5, 10] node split threshold
- **min_samples_leaf**: [1, 2, 4] leaf size constraint
- **max_features**: ["sqrt", "log2"] feature selection strategy

---

## 10. Data Quality & Monitoring

### 10.1 Ingestion Validation (ingest.py)

**Row-Level Validations**:
```python
✓ AGE ∈ [18, 65]
✓ ATTRITION ∈ {Yes, No}
✓ Salary columns > 0 (MonthlyIncome, HourlyRate, DailyRate, MonthlyRate)
✓ Years columns ≥ 0 (YearsAtCompany, TotalWorkingYears, etc.)
✓ Satisfaction scores ∈ [1, 4]
✓ JobLevel ∈ [1, 5]
✓ PerformanceRating ∈ [3, 4]
✓ PercentSalaryHike ∈ [0, 25]
✓ StockOptionLevel ∈ [0, 3]
✓ GENDER ∈ {Male, Female}
✓ OverTime ∈ {Yes, No}
✓ DistanceFromHome ≥ 0
```

**Metrics**:
- Total rows, Valid rows, Invalid rows
- Duplicate removal count
- Rejection report with error details

### 10.2 ML-Ready Validation (dataquality.py)

**Great Expectations Checks**:
- Target distribution (ATTRITION ∈ {Yes, No, 0, 1})
- NULL checks for critical features
- Range validation (AGE, INCOME, YEARS)
- One-hot encoding validation (binary ∈ {0, 1})
- Feature completeness

**Output**:
- `reports/ml_ready_validation.json`: Validation report
- Pass/fail count summary

### 10.3 Data Drift Monitoring (monitoring-training.py)

**Evidently DataDriftPreset**:
- Detects statistical distribution shifts in features
- Compares reference data (historical) vs current data
- Triggers retraining if drift_detected = True

**Triggers**:
- Single-day data: Always trains
- Multi-day data: Trains only if drift detected

---

## 11. Current State & Deployment Status

### Project Maturity
✅ **Fully Developed** with integrated components:
- Data pipeline (ingest → transform)
- Model training & tracking (MLflow)
- Data quality framework (Great Expectations)
- Drift monitoring (Evidently)
- Interactive dashboard (Dash)
- Docker containerization

### Operational Status
- **Orchestration**: Prefect flow defined (`hr_attrition_flow`) with daily scheduling
- **Docker**: Multi-container setup (app, MLflow, Prefect)
- **Database**: Snowflake schema prepared (`creation_de_db_snowflake.sql`)
- **Models**: Random Forest classifier with GridSearchCV tuning

### Key Artifacts
- ✅ dbt models (cleaned, encoded)
- ✅ Data quality reports
- ✅ ML-ready validation
- ✅ MLflow experiment tracking
- ✅ Dashboard interface
- ✅ Counterfactual explanations (DICE)

### Potential Enhancements
- [ ] Advanced drift detection (beyond Evidently)
- [ ] A/B testing framework for model versions
- [ ] API endpoint documentation (Swagger/OpenAPI)
- [ ] Advanced feature engineering (interactions, polynomials)
- [ ] Time-series features (seasonality, trends)
- [ ] Explainability dashboard (SHAP values, feature dependencies)
- [ ] Automated retraining triggers in Prefect
- [ ] Monitoring alerts for SLA breaches
- [ ] Cost optimization for Snowflake warehouse

---

## 12. Key Metrics & KPIs

### Model Performance Metrics
- **Accuracy**: Percentage of correct predictions
- **F1 Score**: Harmonic mean of precision & recall (weighted for imbalance)
- **Cross-Validation F1**: Best F1 from 5-fold stratified CV
- **Feature Importance**: Top 15 features ranked by split importance

### Business Metrics
- **Attrition Rate**: Percentage of employees leaving
- **Precision**: Among predicted high-risk, how many actually leave
- **Recall**: Among actual departures, how many were predicted
- **ROI of Interventions**: Cost of retention vs cost of replacement

### Data Quality Metrics
- **Validation Pass Rate**: Percentage of rows passing validation
- **Data Freshness**: Ingestion timestamp recency
- **Feature Completeness**: Non-null percentage per feature
- **Drift Score**: Evidently drift metric

---

## 13. Technologies Used - Summary Table

| **Layer** | **Technology** | **Function** |
|-----------|---------------|------------|
| **Data Warehouse** | Snowflake | Cloud data storage, SQL execution |
| **Data Ingestion** | Python, pandas | CSV load & validation |
| **Data Transformation** | dbt, Jinja | ELT, feature engineering |
| **Data Quality** | Great Expectations | Automated testing |
| **ML Training** | scikit-learn | Random Forest classifier |
| **ML Tracking** | MLflow | Experiment tracking, model registry |
| **Drift Detection** | Evidently | Production monitoring |
| **Orchestration** | Prefect | Workflow scheduling |
| **Web Dashboard** | Dash, Plotly, Bootstrap | Interactive UI |
| **Explainability** | DICE-ML | Counterfactual generation |
| **Containerization** | Docker, Docker Compose | Deployment & reproducibility |
| **Runtime** | Python 3.11 | Programming language |
| **Config Management** | python-dotenv | Environment variables |

---

## 14. Workflow Summary

### Typical Daily Execution
```
00:00 (Scheduled)
  ↓
[Prefect] Trigger hr_attrition_flow
  ↓
[1] ingest_data()
  ├─ Load CSV
  ├─ Validate rows
  └─ Insert to RAW schema
  ↓
[2] prepare_data()
  ├─ dbt run (hr_employee_cleaned)
  ├─ dbt run (hr_employee_encoded)
  └─ Output to GOLD schema
  ↓
[3] data_quality_check()
  ├─ Great Expectations validation
  └─ Generate report
  ↓
[4] datadrifting_training()
  ├─ Evidently drift detection
  ├─ Compare reference vs current
  ├─ train.py (if drift detected or single day)
  ├─ GridSearchCV hyperparameter tuning
  ├─ MLflow logging
  └─ Model registry update
  ↓
[Dashboard & API]
  ├─ Load latest model from MLflow
  ├─ Serve predictions via simulation_service
  └─ Display results in Dash UI
  ↓
End of Pipeline
```

---

## Conclusion

**Projet-RH** is a production-ready, enterprise-grade ML pipeline for HR analytics. It seamlessly integrates:
- **Data engineering** (ingestion, validation, transformation)
- **Machine learning** (training, tracking, monitoring)
- **Data quality** (expectations, drift detection)
- **Visualization** (interactive dashboard, explainability)
- **Orchestration** (Prefect scheduling, Docker containerization)

The system enables HR teams to proactively identify and retain at-risk employees while maintaining data quality, monitoring model performance, and providing interpretable predictions through counterfactual analysis.
