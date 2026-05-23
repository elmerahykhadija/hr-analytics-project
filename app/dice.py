from dice_ml import Dice
from dice_ml import Data, Model
import mlflow
import mlflow.sklearn
import pandas as pd

# Charger le CSV et convertir les colonnes en MAJUSCULES
df = pd.read_csv('/app/app/data/data.csv')
df.columns = df.columns.str.upper()

def load_model():
    mlflow.set_tracking_uri("http://mlflow:5000")
    model_name = "RF_Attrition_v1"
    return mlflow.sklearn.load_model(f"models:/{model_name}/Production")

# Initialiser DICE avec les features en MAJUSCULES
dice_data = Data(
    dataframe=df, 
    continuous_features=['AGE', 'DISTANCEFROMHOME', 'EDUCATION', 'MONTHLYINCOME', 'TOTALWORKINGYEARS'],
    categorical_features=['GENDER', 'MARITALSTATUS', 'OVERTIME', 'BUSINESSTRAVEL'],
    outcome_name='ATTRITION'
)

model = Model(model=load_model(), backend="sklearn")
explainer = Dice(dice_data, model, method="random")

def generate_counterfactuals(input_data, total_CFs=3, desired_class="opposite"):
    """
    Générer des contre-factuels pour un candidat donné.
    input_data est un dict avec les valeurs du formulaire dashboard
    """
    query_instance = pd.DataFrame([input_data])
    query_instance = query_instance[dice_data.feature_names]
    counterfactuals = explainer.generate_counterfactuals(query_instance, total_CFs=total_CFs, desired_class=desired_class)
    return counterfactuals.cf_examples_list[0].final_cfs_df

def generate_smart_counterfactuals(input_data, df_train):
    """
    Générer des scénarios intelligents avec calculs en pourcentage
    Basé sur les critères RH pour réduire l'attrition
    """
    scenarios = []
    current_distance = input_data['DISTANCEFROMHOME']
    current_salary = input_data['MONTHLYINCOME']
    
    # Scénario 1: Distance élevée → Télétravail partiel (60% réduction)
    if current_distance > 25:
        telework_scenario = input_data.copy()
        distance_reduction_pct = 0.60
        new_distance = current_distance * (1 - distance_reduction_pct)
        telework_scenario['DISTANCEFROMHOME'] = new_distance
        telework_scenario['BUSINESSTRAVEL'] = 'Non-Travel'
        
        scenarios.append({
            'name': 'Télétravail partiel',
            'changes': f"Distance: {current_distance:.1f}km → {new_distance:.1f}km (-{distance_reduction_pct*100:.0f}%)",
            'data': telework_scenario
        })
    
    # Scénario 2: Distance élevée → Augmentation salaire compensatrice
    if current_distance > 25:
        salary_scenario = input_data.copy()
        salary_compensation_pct = min((current_distance / 5) * 0.01, 0.20)
        salary_increase = current_salary * salary_compensation_pct
        new_salary = current_salary + salary_increase
        
        salary_scenario['MONTHLYINCOME'] = new_salary
        salary_scenario['DISTANCEFROMHOME'] = current_distance
        
        scenarios.append({
            'name': 'Augmentation compensatrice distance',
            'changes': f"Salaire: {current_salary:.0f}€ → {new_salary:.0f}€ (+{salary_compensation_pct*100:.1f}%)",
            'data': salary_scenario
        })
    
    # Scénario 3: Distance + Salaire (approche combinée)
    if current_distance > 20:
        combined_scenario = input_data.copy()
        distance_reduction_pct = 0.40
        new_distance = current_distance * (1 - distance_reduction_pct)
        salary_bonus_pct = 0.08
        new_salary = current_salary * (1 + salary_bonus_pct)
        
        combined_scenario['DISTANCEFROMHOME'] = new_distance
        combined_scenario['MONTHLYINCOME'] = new_salary
        combined_scenario['BUSINESSTRAVEL'] = 'Non-Travel'
        
        scenarios.append({
            'name': 'Télétravail + augmentation combinée',
            'changes': f"Distance: -{distance_reduction_pct*100:.0f}% | Salaire: +{salary_bonus_pct*100:.0f}%",
            'data': combined_scenario
        })
    
    # Scénario 4: Heures supplémentaires → Éliminer + compensation
    if input_data.get('OVERTIME') == 'Yes':
        overtime_scenario = input_data.copy()
        overtime_scenario['OVERTIME'] = 'No'
        overtime_scenario['MONTHLYINCOME'] = current_salary * 1.05
        
        scenarios.append({
            'name': 'Éliminer heures supplémentaires (+5% salaire)',
            'changes': f"OverTime: Yes → No | Salaire: +5%",
            'data': overtime_scenario
        })
    
    # Scénario 5: Déplacements fréquents → Éliminer + compensation
    if input_data['BUSINESSTRAVEL'] != 'Non-Travel':
        travel_scenario = input_data.copy()
        travel_scenario['BUSINESSTRAVEL'] = 'Non-Travel'
        travel_scenario['MONTHLYINCOME'] = current_salary * 1.03
        
        scenarios.append({
            'name': 'Éliminer déplacements professionnels (+3% salaire)',
            'changes': f"Déplacements: {input_data['BUSINESSTRAVEL']} → Non-Travel | Salaire: +3%",
            'data': travel_scenario
        })
    
    return scenarios

def generate_counterfactuals_with_scenarios(input_data, total_CFs=3, desired_class="opposite"):
    """
    Combine DICE avec scénarios intelligents RH
    """
    query_instance = pd.DataFrame([input_data])
    query_instance = query_instance[dice_data.feature_names]
    counterfactuals = explainer.generate_counterfactuals(
        query_instance, total_CFs=total_CFs, desired_class=desired_class
    )
    
    scenarios = generate_smart_counterfactuals(input_data, df)
    
    results = {
        'dice_counterfactuals': counterfactuals.cf_examples_list[0].final_cfs_df,
        'smart_scenarios': scenarios
    }
    
    return results

def generate_smart_scenarios(input_data):
    """
    Générer des scénarios intelligents avec montants exacts en DH
    et jours de télétravail réels
    """
    scenarios = []
    current_distance = input_data['DISTANCEFROMHOME']
    current_salary = input_data['MONTHLYINCOME']
    current_overtime = input_data['OVERTIME']
    current_travel = input_data['BUSINESSTRAVEL']
    
    # Scénario 1: Distance élevée → Ajouter jours de télétravail
    if current_distance > 20:
        scenario1 = input_data.copy()
        telework_days = min(3, int(current_distance / 15))  # 1-3 jours selon distance
        
        # Réduire la distance de 20% par jour de télétravail
        distance_reduction = current_distance * (0.20 * telework_days)
        new_distance = max(0, current_distance - distance_reduction)
        
        scenario1['DISTANCEFROMHOME'] = new_distance
        scenario1['telework_days'] = telework_days
        
        # Prédire le risque pour ce scénario
        predicted_risk1 = predict_scenario_risk(scenario1)
        
        scenarios.append({
            'name': f'Télétravail : {telework_days} jour{"s" if telework_days > 1 else ""}/semaine',
            'changes': f"Distance: {current_distance:.0f}km → {new_distance:.0f}km (-{distance_reduction:.0f}km)",
            'telework_days': telework_days,
            'distance': new_distance,
            'monthly_income': current_salary,
            'overtime': current_overtime,
            'businesstravel': current_travel,
            'estimated_risk': predicted_risk1,
        })
    
    # Scénario 2: Télétravail 2j + Augmentation salaire 300 DH
    if current_distance > 15:
        scenario2 = input_data.copy()
        telework_days = 2
        
        distance_reduction = current_distance * (0.20 * telework_days)
        new_distance = max(0, current_distance - distance_reduction)
        salary_increase = 300  # Montant exact en DH
        new_salary = current_salary + salary_increase
        
        scenario2['DISTANCEFROMHOME'] = new_distance
        scenario2['MONTHLYINCOME'] = new_salary
        scenario2['telework_days'] = telework_days
        
        predicted_risk2 = predict_scenario_risk(scenario2)
        
        scenarios.append({
            'name': 'Télétravail 2j + Augmentation 300 DH',
            'changes': f"Distance: -{distance_reduction:.0f}km | Salaire: +300 DH/mois",
            'telework_days': telework_days,
            'distance': new_distance,
            'monthly_income': new_salary,
            'overtime': current_overtime,
            'businesstravel': current_travel,
            'estimated_risk': predicted_risk2,
        })
    
    # Scénario 3: Éliminer les heures supplémentaires + Augmentation 200 DH
    if current_overtime == 'Yes':
        scenario3 = input_data.copy()
        salary_increase = 200  # Montant exact
        new_salary = current_salary + salary_increase
        
        scenario3['OVERTIME'] = 'No'
        scenario3['MONTHLYINCOME'] = new_salary
        scenario3['telework_days'] = 0
        
        predicted_risk3 = predict_scenario_risk(scenario3)
        
        scenarios.append({
            'name': 'Éliminer heures supplémentaires + Augmentation 200 DH',
            'changes': f"OverTime: Oui → Non | Salaire: +200 DH/mois",
            'telework_days': 0,
            'distance': current_distance,
            'monthly_income': new_salary,
            'overtime': 'No',
            'businesstravel': current_travel,
            'estimated_risk': predicted_risk3,
        })
    
    # Scénario 4: Réduire déplacements + Augmentation 250 DH
    if current_travel != 'Non-Travel':
        scenario4 = input_data.copy()
        salary_increase = 250  # Montant exact
        new_salary = current_salary + salary_increase
        
        scenario4['BUSINESSTRAVEL'] = 'Non-Travel'
        scenario4['MONTHLYINCOME'] = new_salary
        scenario4['telework_days'] = 0
        
        predicted_risk4 = predict_scenario_risk(scenario4)
        
        scenarios.append({
            'name': 'Réduire déplacements + Augmentation 250 DH',
            'changes': f"Déplacements: {current_travel} → Non-Travel | Salaire: +250 DH/mois",
            'telework_days': 0,
            'distance': current_distance,
            'monthly_income': new_salary,
            'overtime': current_overtime,
            'businesstravel': 'Non-Travel',
            'estimated_risk': predicted_risk4,
        })
    
    return scenarios


def predict_scenario_risk(scenario_data):
    """
    Prédire le risque d'attrition pour un scénario donné
    """
    try:
        from simulation_service import predict_risk
        result = predict_risk(scenario_data)
        return result.get('risk_score', 0.5) * 100
    except Exception as e:
        print(f"Erreur prédiction risque: {e}")
        return 50.0
