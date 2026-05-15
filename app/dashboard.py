import dash
from dash import dcc, html, Input, Output, callback
import plotly.graph_objects as go
from simulation_service import load_model, predict_risk

app = dash.Dash(__name__)
server = app.server

# Tentative de chargement du modèle
try:
    model = load_model()
except:
    model = None
    print("[WARNING] Le modèle n'a pas pu être chargé.")

# --- PALETTE DE COULEURS "NATURE ZEN" ---
BG_APP = "#F6F9F4"
BG_CARD = "#FFFFFF"
TEXT_HEADER = "#1C3829"
TEXT_BODY = "#6B7280"
BRAND_COLOR = "#2D7A4F"
HIGHLIGHT_GREEN = "#E9F5E1"
BORDER_GREEN = "#C6E8C0"

# --- COULEURS D'ÉTAT ---
SUCCESS_COLOR = "#16A34A"
WARNING_COLOR = "#D97706"
DANGER_COLOR = "#DC2626"

# --- STYLES RÉUTILISABLES ---
shadow_soft = "0px 8px 30px rgba(45, 122, 79, 0.08)"
shadow_salary = "0px 8px 20px rgba(45, 122, 79, 0.25)"

page_style = {
    "minHeight": "100vh",
    "background": BG_APP,
    "color": TEXT_BODY,
    "fontFamily": "'DM Sans', 'Inter', '-apple-system', sans-serif",
    "padding": "40px 20px",
}

header_style = {
    "maxWidth": "1200px",
    "margin": "0 auto 30px auto",
    "textAlign": "center",
}

card_style = {
    "padding": "24px",
    "backgroundColor": BG_CARD,
    "borderRadius": "24px",
    "boxShadow": shadow_soft,
    "border": f"1px solid {BORDER_GREEN}",
}

kpi_style = {
    "padding": "20px",
    "backgroundColor": HIGHLIGHT_GREEN,
    "borderRadius": "20px",
    "textAlign": "center",
    "border": f"1px solid {BORDER_GREEN}",
    "display": "flex",
    "flexDirection": "column",
    "justifyContent": "center",
}

input_container_style = {
    "background": HIGHLIGHT_GREEN,
    "borderRadius": "14px",
    "padding": "15px",
    "marginBottom": "16px",
    "border": f"1px solid {BORDER_GREEN}",
}

label_style = {
    "fontWeight": "700",
    "color": TEXT_HEADER,
    "fontSize": "13px",
    "marginBottom": "10px",
    "display": "block",
}


# --- FONCTION POUR CRÉER LE CERCLE DE RISQUE ---
def create_risk_donut(risk_percent):
    """Créer un graphique circulaire (donut) avec le pourcentage au centre."""
    
    # Déterminer la couleur selon le risque
    if risk_percent < 30:
        base_color = SUCCESS_COLOR
    elif risk_percent < 50:
        base_color = WARNING_COLOR
    else:
        base_color = DANGER_COLOR
    
    colors = [base_color, "#E5E7EB"]
    
    # Créer le graphique
    fig = go.Figure(data=[go.Pie(
        values=[risk_percent, 100 - risk_percent],
        labels=["Risque", "Sécurisé"],
        hole=0.75,  # Taille du trou central (effet donut)
        marker=dict(colors=colors, line=dict(color=BG_CARD, width=2)),
        textinfo='none',
        hoverinfo='label+percent',
        direction='clockwise',
        sort=False
    )])
    
    # Ajouter le texte au centre
    fig.add_annotation(
        text=f"{risk_percent:.1f}%",
        x=0.5, y=0.5,
        font=dict(size=48, color=base_color, family="'DM Sans', sans-serif", weight="bold"),
        showarrow=False
    )
    
    fig.add_annotation(
        text="Risque de départ",
        x=0.5, y=0.35,
        font=dict(size=14, color=TEXT_BODY, family="'DM Sans', sans-serif"),
        showarrow=False
    )

    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        height=350,
        showlegend=False,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
    )
    
    return fig


# --- LAYOUT DE L'APPLICATION ---
app.layout = html.Div(
    style=page_style,
    children=[
        # HEADER
        html.Div(
            style=header_style,
            children=[
                html.H1("Simulateur d'Attrition", 
                        style={'margin': '0 0 8px 0', 'color': TEXT_HEADER, 'fontSize': '32px', 'fontWeight': '800'}),
                html.P("Analyse en temps réel du risque de départ de vos collaborateurs",
                        style={'margin': 0, 'color': TEXT_BODY, 'fontSize': '16px'}),
            ]
        ),

        html.Div(
            style={'maxWidth': '1200px', 'margin': '0 auto'},
            children=[
                html.Div(
                    style={'display': 'grid', 'gridTemplateColumns': '1fr 1fr', 'gap': '30px'},
                    children=[
                        
                        # --- COLONNE GAUCHE : PARAMÈTRES ---
                        html.Div(
                            style=card_style,
                            children=[
                                html.H3("Profil du Collaborateur", style={'color': TEXT_HEADER, 'marginTop': 0, 'marginBottom': '20px', 'fontSize': '18px'}),
                                
                                # Âge
                                html.Div(style=input_container_style, children=[
                                    html.Label("Âge", style=label_style),
                                    dcc.Slider(
                                        id="age", min=18, max=70, value=35, step=1,
                                        marks={18: '18', 35: '35', 50: '50', 70: '70'},
                                        tooltip={"placement": "bottom", "always_visible": True},
                                    ),
                                ]),

                                # Expérience totale
                                html.Div(style=input_container_style, children=[
                                    html.Label("Expérience totale (années)", style=label_style),
                                    dcc.Slider(
                                        id="total_working_years", min=0, max=40, value=5, step=1,
                                        marks={0: '0', 10: '10', 20: '20', 40: '40'},
                                        tooltip={"placement": "bottom", "always_visible": True},
                                    ),
                                ]),
                                
                                # Distance
                                html.Div(style=input_container_style, children=[
                                    html.Label("Distance domicile-travail (km)", style=label_style),
                                    dcc.Input(
                                        id="distance", type="number", value=10, min=0, max=100, step=1,
                                        style={'width': '100%', 'padding': '10px', 'border': 'none', 'borderRadius': '8px', 'background': 'white', 'fontSize': '14px'}
                                    ),
                                ]),

                                # Niveau d'études
                                html.Div(style=input_container_style, children=[
                                    html.Label("Niveau d'études (1-5)", style=label_style),
                                    dcc.Slider(
                                        id="education", min=1, max=5, value=3, step=1,
                                        marks={1: '1', 3: '3', 5: '5'},
                                        tooltip={"placement": "bottom", "always_visible": True},
                                    ),
                                ]),
                                
                                # Heures sup
                                html.Div(style=input_container_style, children=[
                                    html.Label("Heures supplémentaires", style=label_style),
                                    dcc.RadioItems(
                                        id="overtime",
                                        options=[{"label": " Non", "value": "No"}, {"label": " Oui", "value": "Yes"}],
                                        value="No", inline=True,
                                        style={'display': 'flex', 'gap': '20px', 'color': TEXT_BODY, 'fontWeight': '500'}
                                    ),
                                ]),
                                
                                # Déplacements
                                html.Div(style=input_container_style, children=[
                                    html.Label("Déplacements professionnels", style=label_style),
                                    dcc.Dropdown(
                                        id="businesstravel",
                                        options=[
                                            {"label": "Aucun", "value": "Non-Travel"},
                                            {"label": "Rares", "value": "Travel_Rarely"},
                                            {"label": "Fréquents", "value": "Travel_Frequently"},
                                        ],
                                        value="Non-Travel",
                                        clearable=False,
                                        style={'border': 'none', 'borderRadius': '8px', 'background': 'white'}
                                    ),
                                ]),

                                # Genre
                                html.Div(style=input_container_style, children=[
                                    html.Label("Genre", style=label_style),
                                    dcc.RadioItems(
                                        id="gender",
                                        options=[{"label": " Homme", "value": "Male"}, {"label": " Femme", "value": "Female"}],
                                        value="Male", inline=True,
                                        style={'display': 'flex', 'gap': '20px', 'color': TEXT_BODY, 'fontWeight': '500'}
                                    ),
                                ]),
                                
                                # Situation familiale
                                html.Div(style=input_container_style, children=[
                                    html.Label("Situation familiale", style=label_style),
                                    dcc.Dropdown(
                                        id="maritalstatus",
                                        options=[
                                            {"label": "Célibataire", "value": "Single"},
                                            {"label": "Marié(e)", "value": "Married"},
                                            {"label": "Divorcé(e)", "value": "Divorced"},
                                        ],
                                        value="Single",
                                        clearable=False,
                                        style={'border': 'none', 'borderRadius': '8px', 'background': 'white'}
                                    ),
                                ]),

                                # Salaire mensuel
                                html.Div(style=input_container_style, children=[
                                    html.Label("Salaire mensuel (DH)", style=label_style),
                                    dcc.Slider(
                                        id="monthly_income", min=1000, max=50000, value=5000, step=500,
                                        marks={1000: '1k', 10000: '10k', 25000: '25k', 50000: '50k'},
                                        tooltip={"placement": "bottom", "always_visible": True},
                                    ),
                                ]),
                            ]
                        ),

                        # --- COLONNE DROITE : VISUALISATION ---
                        html.Div(
                            children=[
                                
                                # CERCLE DE RISQUE
                                html.Div(
                                    style={**card_style, 'marginBottom': '30px', 'textAlign': 'center'},
                                    children=[
                                        html.H3("Niveau de Risque", style={'color': TEXT_HEADER, 'marginTop': 0, 'marginBottom': '10px', 'fontSize': '18px'}),
                                        dcc.Graph(id="risk-donut-chart", style={'height': '350px'}, config={'displayModeBar': False}),
                                        html.Div(id="risk-level-badge", style={'marginTop': '10px'})
                                    ]
                                ),
                                
                                # BLOC SALAIRE AFFICHÉ
                                html.Div(
                                    style=card_style,
                                    children=[
                                        html.H3("Simulation de Rémunération", style={'color': TEXT_HEADER, 'marginTop': 0, 'marginBottom': '20px', 'fontSize': '18px'}),
                                        
                                        html.Div(
                                            style={'background': BRAND_COLOR, 'borderRadius': '16px', 'padding': '20px', 
                                                   'color': 'white', 'textAlign': 'center', 'marginBottom': '20px',
                                                   'boxShadow': shadow_salary},
                                            children=[
                                                html.Div(id="salary-display", style={'fontSize': '32px', 'fontWeight': '800'}),
                                                html.Div("DH / mois", style={'fontSize': '12px', 'opacity': '0.8', 'marginTop': '4px'}),
                                            ]
                                        ),
                                    ]
                                ),
                                
                                # KPI GRID
                                html.Div(
                                    style={'display': 'grid', 'gridTemplateColumns': 'repeat(3, 1fr)', 'gap': '15px', 'marginTop': '30px'},
                                    children=[
                                        html.Div(style=kpi_style, children=[
                                            html.Div("Âge actuel", style={'color': TEXT_BODY, 'fontSize': '12px'}),
                                            html.Div(id="metric-age", style={'color': TEXT_HEADER, 'fontSize': '24px', 'fontWeight': '700'})
                                        ]),
                                        html.Div(style=kpi_style, children=[
                                            html.Div("Expérience", style={'color': TEXT_BODY, 'fontSize': '12px'}),
                                            html.Div(id="metric-exp", style={'color': TEXT_HEADER, 'fontSize': '24px', 'fontWeight': '700'})
                                        ]),
                                        html.Div(style=kpi_style, children=[
                                            html.Div("Distance", style={'color': TEXT_BODY, 'fontSize': '12px'}),
                                            html.Div(id="metric-dist", style={'color': TEXT_HEADER, 'fontSize': '24px', 'fontWeight': '700'})
                                        ]),
                                    ]
                                ),
                            ]
                        ),
                    ]
                ),
            ]
        ),
    ]
)


# --- CALLBACK POUR MISE À JOUR EN TEMPS RÉEL ---
@callback(
    [
        Output("risk-donut-chart", "figure"),
        Output("salary-display", "children"),
        Output("risk-level-badge", "children"),
        Output("risk-level-badge", "style"),
        Output("metric-age", "children"),
        Output("metric-exp", "children"),
        Output("metric-dist", "children"),
    ],
    [
        Input("age", "value"),
        Input("gender", "value"),
        Input("maritalstatus", "value"),
        Input("distance", "value"),
        Input("total_working_years", "value"),
        Input("monthly_income", "value"),
        Input("education", "value"),
        Input("overtime", "value"),
        Input("businesstravel", "value"),
    ],
)
def update_dashboard(age, gender, maritalstatus, distance, total_working_years, monthly_income, education, overtime, businesstravel):
    # Préparer les données
    data = {
        "AGE": age,
        "GENDER": gender,
        "MARITALSTATUS": maritalstatus,
        "DISTANCEFROMHOME": distance,
        "TOTALWORKINGYEARS": total_working_years,
        "MONTHLYINCOME": monthly_income,
        "EDUCATION": education,
        "OVERTIME": overtime,
        "BUSINESSTRAVEL": businesstravel,
    }

    base_badge_style = {
        'fontSize': '14px', 'fontWeight': '700', 'textAlign': 'center', 
        'padding': '10px', 'borderRadius': '10px'
    }

    # Prédiction
    try:
        if model:
            res = predict_risk(model, data)
            risk_score = res.get("risk_score", 0.0)
            risk_percent = risk_score * 100
        else:
            # Mode démo
            risk_percent = (distance * 0.5 + (40-total_working_years)*0.5 + (monthly_income/1000)*-0.1) + 15
            risk_percent = max(min(risk_percent, 95), 5)

        # Déterminer le niveau
        if risk_percent < 30:
            level = "Niveau de risque : FAIBLE"
            level_style = {**base_badge_style, 'background': 'rgba(22, 163, 74, 0.1)', 'color': SUCCESS_COLOR}
        elif risk_percent < 50:
            level = "Niveau de risque : MODÉRÉ"
            level_style = {**base_badge_style, 'background': 'rgba(217, 119, 6, 0.1)', 'color': WARNING_COLOR}
        else:
            level = "Niveau de risque : ÉLEVÉ"
            level_style = {**base_badge_style, 'background': 'rgba(220, 38, 36, 0.1)', 'color': DANGER_COLOR}

        donut_fig = create_risk_donut(risk_percent)
        
        return [
            donut_fig,
            f"{monthly_income:,.0f}",
            level,
            level_style,
            f"{age} ans",
            f"{total_working_years} ans",
            f"{distance} km",
        ]

    except Exception as e:
        error_fig = go.Figure()
        error_fig.add_annotation(text="Erreur", x=0.5, y=0.5, showarrow=False)
        return [
            error_fig,
            "Erreur",
            f"Erreur: {str(e)}",
            {**base_badge_style, 'background': 'rgba(220, 38, 36, 0.1)', 'color': DANGER_COLOR},
            "-", "-", "-",
        ]


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)