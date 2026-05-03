import dash
from dash import dcc, html, Input, Output, State, dash_table
import pandas as pd
import os
from simulation_service import load_model, predict_risk

app = dash.Dash(__name__)
server = app.server

model = load_model()

app.layout = html.Div([
    html.H2("Simulateur de risque d'attrition"),
    html.Div([
        html.Label("Salaire mensuel"),
        dcc.Input(
            id="monthly_income",
            type="number",
            value=5000,
            placeholder="Ex: 5000"
        ),

        html.Label("Age"),
        dcc.Input(
            id="age",
            type="number",
            value=35,
            placeholder="Ex: 35"
        ),

        html.Label("Distance domicile-travail"),
        dcc.Input(
            id="distance",
            type="number",
            value=10,
            placeholder="Ex: 10 km"
        ),

        html.Label("Heures supplementaires"),
        dcc.Dropdown(
            id="overtime",
            options=[
                {"label": "Oui", "value": "Yes"},
                {"label": "Non", "value": "No"}
            ],
            value="No"
        ),

        html.Button("Lancer la simulation", id="simulate_btn", n_clicks=0)
    ], style={"display": "grid", "gridTemplateColumns": "1fr", "gap": "8px", "maxWidth": "420px"}),

    html.Hr(),
    html.Div(id="risk_output"),
    html.H4("Scenarios contre-factuels (DiCE)"),
    dash_table.DataTable(id="cf_table", page_size=5)
])

@app.callback(
    Output("risk_output", "children"),
    Output("cf_table", "data"),
    Output("cf_table", "columns"),
    Input("simulate_btn", "n_clicks"),
    State("monthly_income", "value"),
    State("age", "value"),
    State("distance", "value"),
    State("overtime", "value")
)
def simulate(n_clicks, monthly_income, age, distance, overtime):
    if n_clicks == 0:
        return "Cliquez sur 'Lancer la simulation'", [], []

    # Construire un vecteur complet (avec défauts à 0)
    row = {}
    # Tu peux importer FEATURE_COLUMNS depuis simulation_service pour éviter les écarts
    from simulation_service import FEATURE_COLUMNS
    for c in FEATURE_COLUMNS:
        row[c] = 0

    row["MonthlyIncome"] = monthly_income or 0
    row["Age"] = age or 0
    row["DistanceFromHome"] = distance or 0
    row["OverTime_Yes"] = 1 if overtime == "Yes" else 0
    row["OverTime_No"] = 1 if overtime == "No" else 0

    result = predict_risk(model, row)
    msg = f"Risque predit: {result['risk_score']:.2f} | Classe predite: {result['prediction']}"

    # Placeholder tant que DiCE n’est pas branché avec dataset de référence
    cf_df = pd.DataFrame([
        {"Action recommandee": "Augmenter le salaire mensuel", "Impact attendu": "Baisse du risque"},
        {"Action recommandee": "Reduire les heures supplementaires", "Impact attendu": "Baisse du risque"},
        {"Action recommandee": "Ameliorer l'equilibre vie pro / vie perso", "Impact attendu": "Baisse du risque"},
    ])

    return msg, cf_df.to_dict("records"), [{"name": c, "id": c} for c in cf_df.columns]

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8050, debug=False)