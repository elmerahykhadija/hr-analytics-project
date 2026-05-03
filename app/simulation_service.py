import mlflow
import mlflow.sklearn
import pandas as pd

# Sauvegarde d'une liste fallback si model.feature_names_in_ n'est pas disponible
FALLBACK_FEATURES = [
    "AGE","DAILYRATE","DISTANCEFROMHOME","EDUCATION","ENVIRONMENTSATISFACTION",
    "HOURLYRATE","JOBINVOLVEMENT","JOBLEVEL","JOBSATISFACTION","MONTHLYINCOME",
    "MONTHLYRATE","NUMCOMPANIESWORKED","PERCENTSALARYHIKE","PERFORMANCERATING",
    "RELATIONSHIPSATISFACTION","STOCKOPTIONLEVEL","TOTALWORKINGYEARS",
    "TRAININGTIMESLASTYEAR","WORKLIFEBALANCE","YEARSATCOMPANY","YEARSINCURRENTROLE",
    "YEARSSINCELASTPROMOTION","YEARSWITHCURRMANAGER",
    # one-hot prefixes (examples)
    "BUSINESSTRAVEL_","DEPARTMENT_","EDUCATIONFIELD_","GENDER_","JOBROLE_","MARITALSTATUS_",
    "OVERTIME_"
]

def load_model():
    mlflow.set_tracking_uri("http://mlflow:5000")
    model_name = "RF_Attrition_v1"
    return mlflow.sklearn.load_model(f"models:/{model_name}/Production")

def _get_feature_names(model):
    if hasattr(model, "feature_names_in_"):
        return list(model.feature_names_in_)
    # fallback: build a conservative list by expanding known one-hot prefixes to empty set;
    # in practice prefer feature_names_in_ from the trained estimator
    return FALLBACK_FEATURES

def _set_one_hot(full_row, feature_names, prefix, value):
    # prefix like "DEPARTMENT_", value like "Sales"
    if value is None:
        return
    v = str(value).strip().upper()
    matched = False
    for fn in feature_names:
        if fn.startswith(prefix):
            # compare ignoring spaces and punctuation
            key = fn[len(prefix):].upper().replace(" ", "").replace("&", "AND").replace("-", "").replace("_", "")
            cand = v.replace(" ", "").replace("&", "AND").replace("-", "").replace("_", "")
            if cand == key or cand in key or key in cand:
                full_row[fn] = 1
                matched = True
            else:
                # leave as 0
                pass
    # if none matched, leave all zeros (safe)
    return matched

def predict_risk(model, row_dict):
    # normalize incoming keys to upper and strip
    input_norm = {k.strip().upper(): v for k, v in row_dict.items() if v is not None}

    feature_names = _get_feature_names(model)

    # build full_row initialized with zeros for every required feature
    full_row = {fn: 0 for fn in feature_names}

    # map direct numeric features if present
    numeric_fields = [
        "AGE","DAILYRATE","DISTANCEFROMHOME","EDUCATION","ENVIRONMENTSATISFACTION",
        "HOURLYRATE","JOBINVOLVEMENT","JOBLEVEL","JOBSATISFACTION","MONTHLYINCOME",
        "MONTHLYRATE","NUMCOMPANIESWORKED","PERCENTSALARYHIKE","PERFORMANCERATING",
        "RELATIONSHIPSATISFACTION","STOCKOPTIONLEVEL","TOTALWORKINGYEARS",
        "TRAININGTIMESLASTYEAR","WORKLIFEBALANCE","YEARSATCOMPANY","YEARSINCURRENTROLE",
        "YEARSSINCELASTPROMOTION","YEARSWITHCURRMANAGER"
    ]

    for nf in numeric_fields:
        if nf in input_norm and nf in full_row:
            try:
                full_row[nf] = float(input_norm[nf])
            except Exception:
                full_row[nf] = input_norm[nf]

    # handle overtime if passed as raw Yes/No or as encoded flags
    if "OVERTIME" in input_norm:
        val = input_norm["OVERTIME"]
        _set_one_hot(full_row, feature_names, "OVERTIME_", val)
    else:
        # allow encoded keys directly
        if "OVERTIME_YES" in input_norm and "OVERTIME_YES" in full_row:
            full_row["OVERTIME_YES"] = int(bool(input_norm["OVERTIME_YES"]))
        if "OVERTIME_NO" in input_norm and "OVERTIME_NO" in full_row:
            full_row["OVERTIME_NO"] = int(bool(input_norm["OVERTIME_NO"]))

    # one-hot categories: BusinessTravel, Department, EducationField, JobRole, MaritalStatus, Gender
    if "BUSINESSTRAVEL" in input_norm:
        _set_one_hot(full_row, feature_names, "BUSINESSTRAVEL_", input_norm["BUSINESSTRAVEL"])
    if "DEPARTMENT" in input_norm:
        _set_one_hot(full_row, feature_names, "DEPARTMENT_", input_norm["DEPARTMENT"])
    if "EDUCATIONFIELD" in input_norm:
        _set_one_hot(full_row, feature_names, "EDUCATIONFIELD_", input_norm["EDUCATIONFIELD"])
    if "JOBROLE" in input_norm:
        _set_one_hot(full_row, feature_names, "JOBROLE_", input_norm["JOBROLE"])
    if "MARITALSTATUS" in input_norm:
        _set_one_hot(full_row, feature_names, "MARITALSTATUS_", input_norm["MARITALSTATUS"])
    if "GENDER" in input_norm:
        _set_one_hot(full_row, feature_names, "GENDER_", input_norm["GENDER"])

    # if user passed encoded columns directly, accept them
    for k, v in input_norm.items():
        if k in full_row:
            try:
                full_row[k] = float(v)
            except Exception:
                full_row[k] = v

    # final DataFrame in the exact order expected by the model
    df = pd.DataFrame([full_row], columns=feature_names)

    # predict
    proba = model.predict_proba(df)[0]
    # class 1 is attrition positive
    risk_score = float(proba[1])
    prediction = "Risque Élevé" if risk_score > 0.5 else "Risque Faible"
    return {"risk_score": risk_score, "prediction": prediction}