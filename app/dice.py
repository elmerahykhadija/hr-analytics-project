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
