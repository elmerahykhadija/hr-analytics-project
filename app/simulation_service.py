import mlflow
import mlflow.sklearn
import pandas as pd

REQUIRED_FEATURES = [
    # Numériques
    "AGE", "DISTANCEFROMHOME", "EDUCATION", "JOBLEVEL",
    "MONTHLYINCOME", "TOTALWORKINGYEARS", "NUMCOMPANIESWORKED",
    "JOBSATISFACTION", "ENVIRONMENTSATISFACTION", "RELATIONSHIPSATISFACTION",
    "JOBINVOLVEMENT", "WORKLIFEBALANCE", "PERFORMANCERATING",
    
    # One-Hot Encodées
    "GENDER_MALE", "GENDER_FEMALE",
    "MARITALSTATUS_SINGLE", "MARITALSTATUS_MARRIED", "MARITALSTATUS_DIVORCED",
    "BUSINESSTRAVEL_NONTRAVEL", "BUSINESSTRAVEL_TRAVEL_RARELY", "BUSINESSTRAVEL_TRAVEL_FREQUENTLY",
    "OVERTIME_NO", "OVERTIME_YES",
]

_cached_model = None
_cached_features = None

def load_model():
    global _cached_model, _cached_features
    if _cached_model is None:
        mlflow.set_tracking_uri("http://mlflow:5000")
        model_name = "RF_Attrition_v1"
        _cached_model = mlflow.sklearn.load_model(f"models:/{model_name}/Production")
        if hasattr(_cached_model, 'feature_names_in_'):
            _cached_features = list(_cached_model.feature_names_in_)
        else:
            _cached_features = REQUIRED_FEATURES
    return _cached_model, _cached_features

def predict_risk(row_dict):
    model, feature_names = load_model()
    
    # Initialisation propre à 0
    full_row = {fn: 0.0 for fn in feature_names}
    
    # Mapping numériques
    numeric_map = {
        "AGE": "AGE",
        "DISTANCEFROMHOME": "DISTANCEFROMHOME",
        "EDUCATION": "EDUCATION",
        "JOBLEVEL": "JOBLEVEL",
        "MONTHLYINCOME": "MONTHLYINCOME",
        "TOTALWORKINGYEARS": "TOTALWORKINGYEARS",
        "NUMCOMPANIESWORKED": "NUMCOMPANIESWORKED",
        "JOBSATISFACTION": "JOBSATISFACTION",
        "ENVIRONMENTSATISFACTION": "ENVIRONMENTSATISFACTION",
        "RELATIONSHIPSATISFACTION": "RELATIONSHIPSATISFACTION",
        "JOBINVOLVEMENT": "JOBINVOLVEMENT",
        "WORKLIFEBALANCE": "WORKLIFEBALANCE",
        "PERFORMANCERATING": "PERFORMANCERATING",
    }
    
    for key, col in numeric_map.items():
        val = row_dict.get(key)
        if val is not None and col in full_row:
            try:
                full_row[col] = float(val)
            except (ValueError, TypeError):
                full_row[col] = 0.0
                
    # Mapping One-Hot
    cat_maps = {
        "GENDER": {"Male": "GENDER_MALE", "Female": "GENDER_FEMALE"},
        "MARITALSTATUS": {
            "Single": "MARITALSTATUS_SINGLE", 
            "Married": "MARITALSTATUS_MARRIED", 
            "Divorced": "MARITALSTATUS_DIVORCED"
        },
        "BUSINESSTRAVEL": {
            "Non-Travel": "BUSINESSTRAVEL_NONTRAVEL",
            "Travel_Rarely": "BUSINESSTRAVEL_TRAVEL_RARELY",
            "Travel_Frequently": "BUSINESSTRAVEL_TRAVEL_FREQUENTLY"
        },
        "OVERTIME": {"No": "OVERTIME_NO", "Yes": "OVERTIME_YES"}
    }
    
    for cat_key, mapping in cat_maps.items():
        val = row_dict.get(cat_key)
        if val in mapping:
            target_col = mapping[val]
            if target_col in full_row:
                full_row[target_col] = 1.0
                
    # Construction du DataFrame dans l'ordre exact attendu par le modèle
    df = pd.DataFrame([full_row], columns=feature_names)
    
    # Prédiction
    proba = model.predict_proba(df)[0]
    risk_score = float(proba[1])
    prediction = "Risque Élevé" if risk_score > 0.5 else "Risque Faible"
    
    return {"risk_score": risk_score, "prediction": prediction}