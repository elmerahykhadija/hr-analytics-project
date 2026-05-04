import dash
from dash import dcc, html, Input, Output, State
from simulation_service import load_model, predict_risk

app = dash.Dash(__name__)
server = app.server

model = load_model()

page_style = {
    "minHeight": "100vh",
    "background": "linear-gradient(135deg, #0f172a 0%, #1f2937 45%, #3b0d11 100%)",
    "color": "white",
    "fontFamily": "Arial, sans-serif",
    "padding": "40px",
}

container_style = {
    "maxWidth": "1180px",
    "margin": "0 auto",
    "padding": "28px",
    "backgroundColor": "rgba(255,255,255,0.05)",
    "borderRadius": "18px",
    "boxShadow": "0 18px 60px rgba(0, 0, 0, 0.25)",
    "backdropFilter": "blur(8px)",
}

section_style = {
    "padding": "18px",
    "backgroundColor": "rgba(15, 23, 42, 0.42)",
    "border": "1px solid rgba(255,255,255,0.08)",
    "borderRadius": "14px",
}

field_group_style = {"marginBottom": "14px"}
label_style = {"display": "block", "marginBottom": "6px", "fontWeight": "700", "color": "#f8fafc"}
help_style = {"display": "block", "marginTop": "5px", "color": "#cbd5e1", "fontSize": "12px", "lineHeight": "1.35"}
input_style = {"width": "100%", "borderRadius": "8px", "border": "1px solid rgba(255,255,255,0.14)", "backgroundColor": "rgba(255,255,255,0.94)", "color": "#0f172a"}
dropdown_style = {"width": "100%", "backgroundColor": "rgba(255,255,255,0.94)", "color": "#0f172a"}


def field_block(label, description, control):
    return html.Div(
        style=field_group_style,
        children=[
            html.Label(label, style=label_style),
            control,
            html.Small(description, style=help_style),
        ],
    )


def dropdown_control(**kwargs):
    return dcc.Dropdown(className="dark-dropdown", style=dropdown_style, **kwargs)


def section(title, children):
    return html.Div(
        style=section_style,
        children=[html.H3(title, style={"marginBottom": "14px", "color": "#f8fafc"}), *children],
    )

app.layout = html.Div(
    style=page_style,
    children=[
        html.Div(
            style=container_style,
            children=[
                html.H1("Simulateur de risque d'attrition", style={"color": "#f8fafc", "marginBottom": "8px"}),
                html.P(
                    "Remplissez les informations du candidat. Le risque d'attrition est calculé par le modèle de Machine Learning.",
                    style={"color": "#cbd5e1", "marginBottom": "18px"},
                ),
                html.Div(
                    style={"display": "grid", "gridTemplateColumns": "repeat(2, minmax(0, 1fr))", "gap": "18px", "marginTop": "18px"},
                    children=[
                        section(
                            "Identité",
                            [
                                field_block("Âge", "Âge du candidat en années (18-70).", dcc.Input(id="age", type="number", value=35, min=18, max=70, style=input_style)),
                                field_block(
                                    "Genre",
                                    "Genre du candidat.",
                                    dropdown_control(
                                        id="gender",
                                        options=[{"label": "Homme", "value": "Male"}, {"label": "Femme", "value": "Female"}],
                                        value="Male",
                                    ),
                                ),
                                field_block(
                                    "Situation familiale",
                                    "État matrimonial.",
                                    dropdown_control(
                                        id="maritalstatus",
                                        options=[
                                            {"label": "Célibataire", "value": "Single"},
                                            {"label": "Marié(e)", "value": "Married"},
                                            {"label": "Divorcé(e)", "value": "Divorced"},
                                        ],
                                        value="Single",
                                    ),
                                ),
                                field_block(
                                    "Niveau d'études",
                                    "Niveau de formation (1 à 5).",
                                    dcc.Input(id="education", type="number", value=3, min=1, max=5, style=input_style),
                                ),
                            ],
                        ),
                        section(
                            "Poste et conditions",
                            [
                                field_block(
                                    "Département",
                                    "Département d'affectation.",
                                    dropdown_control(
                                        id="department",
                                        options=[
                                            {"label": "Ventes", "value": "Sales"},
                                            {"label": "Recherche & Développement", "value": "Research & Development"},
                                            {"label": "Ressources Humaines", "value": "Human Resources"},
                                        ],
                                        value="Research & Development",
                                    ),
                                ),
                                field_block(
                                    "Distance domicile-travail",
                                    "Distance en kilomètres.",
                                    dcc.Input(id="distance", type="number", value=10, min=0, style=input_style),
                                ),
                                field_block(
                                    "Expérience professionnelle",
                                    "Années d'expérience totale.",
                                    dcc.Input(id="total_working_years", type="number", value=5, min=0, style=input_style),
                                ),
                                field_block(
                                    "Déplacements professionnels",
                                    "Fréquence des trajets professionnels.",
                                    dropdown_control(
                                        id="businesstravel",
                                        options=[
                                            {"label": "Aucun déplacement", "value": "Non-Travel"},
                                            {"label": "Déplacements rares", "value": "Travel_Rarely"},
                                            {"label": "Déplacements fréquents", "value": "Travel_Frequently"},
                                        ],
                                        value="Non-Travel",
                                    ),
                                ),
                            ],
                        ),
                        section(
                            "Rémunération",
                            [
                                field_block(
                                    "Salaire mensuel",
                                    "Revenu mensuel brut en euros.",
                                    dcc.Input(id="monthly_income", type="number", value=5000, min=0, style=input_style),
                                ),
                                field_block(
                                    "Heures supplémentaires",
                                    "L'employé effectuera-t-il des heures supplémentaires ?",
                                    dropdown_control(
                                        id="overtime",
                                        options=[{"label": "Non", "value": "No"}, {"label": "Oui", "value": "Yes"}],
                                        value="No",
                                    ),
                                ),
                            ],
                        ),
                        section(
                            "Résultat",
                            [
                                field_block(
                                    "Risque d'attrition",
                                    "Cliquez sur 'Analyser' pour obtenir la prédiction.",
                                    html.Div(id="result", style={"color": "#f8fafc", "fontWeight": "700", "minHeight": "100px"}),
                                ),
                            ],
                        ),
                    ],
                ),

                html.Div(
                    style={"marginTop": "18px", "display": "flex", "justifyContent": "flex-end"},
                    children=[
                        html.Button(
                            "Analyser le risque",
                            id="btn",
                            n_clicks=0,
                            style={
                                "minWidth": "240px",
                                "padding": "12px 18px",
                                "background": "#b91c1c",
                                "color": "white",
                                "border": "none",
                                "borderRadius": "10px",
                                "fontWeight": "700",
                                "cursor": "pointer",
                                "fontSize": "16px",
                            },
                        ),
                    ],
                ),

                html.Hr(style={"marginTop": "20px", "borderColor": "rgba(255,255,255,0.06)"}),
            ],
        )
    ],
)

@app.callback(
    Output("result", "children"),
    Input("btn", "n_clicks"),
    State("age", "value"),
    State("gender", "value"),
    State("maritalstatus", "value"),
    State("education", "value"),
    State("department", "value"),
    State("distance", "value"),
    State("total_working_years", "value"),
    State("monthly_income", "value"),
    State("businesstravel", "value"),
    State("overtime", "value"),
)
def run_simulation(
    n,
    age,
    gender,
    maritalstatus,
    education,
    department,
    distance,
    total_working_years,
    monthly_income,
    businesstravel,
    overtime,
):
    if n == 0:
        return "Remplissez tous les champs et cliquez sur « Analyser le risque »."

    data = {
        "AGE": age or 35,
        "GENDER": gender,
        "MARITALSTATUS": maritalstatus,
        "EDUCATION": education or 3,
        "DEPARTMENT": department,
        "DISTANCEFROMHOME": distance or 10,
        "TOTALWORKINGYEARS": total_working_years or 5,
        "MONTHLYINCOME": monthly_income or 5000,
        "BUSINESSTRAVEL": businesstravel,
        "OVERTIME": overtime,
    }

    try:
        res = predict_risk(model, data)
        risk_score = res.get("risk_score", 0)
        risk_percent = risk_score * 100 if risk_score <= 1 else risk_score

        # Déterminer le niveau de risque et la couleur
        if risk_percent < 30:
            color = "#4ade80"  # Vert
            level = "TRÈS FAIBLE"
            icon = "✓"
            verdict = f"Excellent ! Ce candidat a un risque très faible de départ ({risk_percent:.1f}%)."
        elif risk_percent < 50:
            color = "#fbbf24"  # Orange
            level = "MODÉRÉ"
            icon = "⚠️"
            verdict = f"Attention : Ce candidat a un risque modéré de départ ({risk_percent:.1f}%). À surveiller."
        else:
            color = "#f87171"  # Rouge
            level = "ÉLEVÉ"
            icon = "⛔"
            verdict = f"Danger : Ce candidat risque probablement de quitter l'entreprise ({risk_percent:.1f}%)."

        return html.Div([
            html.Div(f"{risk_percent:.1f}%", style={"fontSize": "56px", "fontWeight": "800", "color": color, "marginBottom": "8px"}),
            html.Div(f"{icon} Risque {level}", style={"fontSize": "20px", "fontWeight": "700", "color": color, "marginBottom": "12px"}),
            html.Div(verdict, style={"marginTop": "10px", "fontSize": "15px", "lineHeight": "1.5"}),
            html.Div(f"Classe prédite : {res.get('prediction', 'N/A')}", style={"marginTop": "14px", "color": "#cbd5e1", "fontSize": "13px"})
        ])
    except Exception as e:
        return html.Div(f"Erreur lors de la prédiction : {str(e)}", style={"color": "#fca5a5"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=False)