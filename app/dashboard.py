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
                html.H1("Simulateur de risque d’attrition", style={"color": "#f8fafc", "marginBottom": "8px"}),
                html.P(
                    "Remplissez les informations de l'employé. Attrition est la cible prédite par le modèle, pas une valeur à saisir.",
                    style={"color": "#cbd5e1", "marginBottom": "18px"},
                ),
                html.Div(
                    style={"display": "grid", "gridTemplateColumns": "repeat(2, minmax(0, 1fr))", "gap": "18px", "marginTop": "18px"},
                    children=[
                        section(
                            "Identité",
                            [
                                field_block("Age", "Âge de l'employé en années.", dcc.Input(id="age", type="number", value=35, min=18, max=70, style=input_style)),
                                field_block(
                                    "Gender",
                                    "Genre de l'employé.",
                                    dropdown_control(
                                        id="gender",
                                        options=[{"label": "Male", "value": "Male"}, {"label": "Female", "value": "Female"}],
                                        value="Male",
                                    ),
                                ),
                                field_block(
                                    "MaritalStatus",
                                    "Situation familiale telle que déclarée dans le jeu de données.",
                                    dropdown_control(
                                        id="maritalstatus",
                                        options=[
                                            {"label": "Single", "value": "Single"},
                                            {"label": "Married", "value": "Married"},
                                            {"label": "Divorced", "value": "Divorced"},
                                        ],
                                        value="Single",
                                    ),
                                ),
                                field_block(
                                    "EducationLevel",
                                    "Niveau d'études de 1 à 5.",
                                    dcc.Input(id="educationlevel", type="number", value=3, min=1, max=5, style=input_style),
                                ),
                            ],
                        ),
                        section(
                            "Poste et ancienneté",
                            [
                                field_block(
                                    "JobRole",
                                    "Fonction occupée par l'employé.",
                                    dropdown_control(
                                        id="jobrole",
                                        options=[
                                            {"label": "Research Scientist", "value": "Research Scientist"},
                                            {"label": "Sales Executive", "value": "Sales Executive"},
                                            {"label": "Manager", "value": "Manager"},
                                            {"label": "Human Resources", "value": "Human Resources"},
                                        ],
                                        value="Research Scientist",
                                    ),
                                ),
                                field_block(
                                    "Department",
                                    "Département ou service d'appartenance.",
                                    dropdown_control(
                                        id="department",
                                        options=[
                                            {"label": "Sales", "value": "Sales"},
                                            {"label": "Research & Development", "value": "Research & Development"},
                                            {"label": "Human Resources", "value": "Human Resources"},
                                        ],
                                        value="Research & Development",
                                    ),
                                ),
                                field_block("JobLevel", "Niveau hiérarchique, de 1 à 5.", dcc.Input(id="job_level", type="number", value=2, min=1, max=5, style=input_style)),
                                field_block("YearsAtCompany", "Nombre d'années dans l'entreprise.", dcc.Input(id="years_company", type="number", value=3, min=0, style=input_style)),
                                field_block("YearsInCurrentRole", "Nombre d'années dans le poste actuel.", dcc.Input(id="years_current_role", type="number", value=2, min=0, style=input_style)),
                                field_block("YearsSinceLastPromotion", "Nombre d'années depuis la dernière promotion.", dcc.Input(id="years_since_promo", type="number", value=1, min=0, style=input_style)),
                                field_block("NumCompaniesWorked", "Nombre total d'entreprises déjà connues.", dcc.Input(id="num_companies_worked", type="number", value=1, min=0, style=input_style)),
                            ],
                        ),
                        section(
                            "Rémunération et satisfaction",
                            [
                                field_block("MonthlyIncome", "Salaire mensuel brut.", dcc.Input(id="monthly_income", type="number", value=5000, min=0, style=input_style)),
                                field_block("SalaryIncreasePercent", "Pourcentage de hausse salariale annuel.", dcc.Input(id="salary_increase_percent", type="number", value=11, min=0, max=100, style=input_style)),
                                field_block("JobSatisfaction", "Niveau de satisfaction au travail, de 1 à 4.", dcc.Input(id="job_satisfaction", type="number", value=3, min=1, max=4, style=input_style)),
                                field_block("EnvironmentSatisfaction", "Satisfaction vis-à-vis de l'environnement, de 1 à 4.", dcc.Input(id="environment_satisfaction", type="number", value=3, min=1, max=4, style=input_style)),
                                field_block("WorkLifeBalance", "Équilibre vie professionnelle / vie personnelle, de 1 à 4.", dcc.Input(id="work_life_balance", type="number", value=3, min=1, max=4, style=input_style)),
                                field_block("PerformanceRating", "Note de performance, généralement entre 3 et 4.", dcc.Input(id="perf_rating", type="number", value=3, min=3, max=4, style=input_style)),
                                field_block("TrainingTimesLastYear", "Nombre de formations suivies l'année dernière.", dcc.Input(id="training_times_last_year", type="number", value=2, min=0, style=input_style)),
                            ],
                        ),
                        section(
                            "Mobilité et conditions",
                            [
                                field_block("DistanceFromHome", "Distance entre le domicile et le lieu de travail, en km.", dcc.Input(id="distance", type="number", value=10, min=0, style=input_style)),
                                field_block(
                                    "BusinessTravel",
                                    "Fréquence habituelle des déplacements professionnels.",
                                    dropdown_control(
                                        id="businesstravel",
                                        options=[
                                            {"label": "Travel_Rarely", "value": "Travel_Rarely"},
                                            {"label": "Travel_Frequently", "value": "Travel_Frequently"},
                                            {"label": "Non-Travel", "value": "Non-Travel"},
                                        ],
                                        value="Non-Travel",
                                    ),
                                ),
                                field_block(
                                    "OverTime",
                                    "Indique si l'employé effectue régulièrement des heures supplémentaires.",
                                    dropdown_control(
                                        id="overtime",
                                        options=[{"label": "Yes", "value": "Yes"}, {"label": "No", "value": "No"}],
                                        value="No",
                                    ),
                                ),
                                field_block("Attrition (target)", "La cible est prédite par le modèle et affichée après analyse.", html.Div("Non saisissable manuellement", style={"color": "#f8fafc", "fontWeight": "700"})),
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
                            },
                        ),
                    ],
                ),

                html.Hr(style={"marginTop": "20px", "borderColor": "rgba(255,255,255,0.06)"}),

                html.Div(id="result", style={"marginTop": "18px", "fontSize": "18px"}),
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
    State("educationlevel", "value"),
    State("jobrole", "value"),
    State("department", "value"),
    State("job_level", "value"),
    State("years_company", "value"),
    State("years_current_role", "value"),
    State("years_since_promo", "value"),
    State("monthly_income", "value"),
    State("salary_increase_percent", "value"),
    State("job_satisfaction", "value"),
    State("environment_satisfaction", "value"),
    State("work_life_balance", "value"),
    State("overtime", "value"),
    State("distance", "value"),
    State("perf_rating", "value"),
    State("businesstravel", "value"),
    State("num_companies_worked", "value"),
    State("training_times_last_year", "value"),
)
def run_simulation(
    n,
    age,
    gender,
    maritalstatus,
    educationlevel,
    jobrole,
    department,
    job_level,
    years_company,
    years_current_role,
    years_since_promo,
    monthly_income,
    salary_increase_percent,
    job_satisfaction,
    environment_satisfaction,
    work_life_balance,
    overtime,
    distance,
    perf_rating,
    businesstravel,
    num_companies_worked,
    training_times_last_year,
):
    if n == 0:
        return "Remplissez les champs et cliquez sur « Analyser le risque »."

    data = {
        "AGE": age or 0,
        "GENDER": gender,
        "MARITALSTATUS": maritalstatus,
        "EDUCATION": educationlevel or 0,
        "JOBROLE": jobrole,
        "DEPARTMENT": department,
        "JOBLEVEL": job_level or 1,
        "YEARSATCOMPANY": years_company or 0,
        "YEARSINCURRENTROLE": years_current_role or 0,
        "YEARSSINCELASTPROMOTION": years_since_promo or 0,
        "MONTHLYINCOME": monthly_income or 0,
        "PERCENTSALARYHIKE": salary_increase_percent or 0,
        "JOBSATISFACTION": job_satisfaction or 0,
        "ENVIRONMENTSATISFACTION": environment_satisfaction or 0,
        "WORKLIFEBALANCE": work_life_balance or 0,
        "OVERTIME": overtime,
        "DISTANCEFROMHOME": distance or 0,
        "PERFORMANCERATING": perf_rating or 3,
        "BUSINESSTRAVEL": businesstravel,
        "NUMCOMPANIESWORKED": num_companies_worked or 0,
        "TRAININGTIMESLASTYEAR": training_times_last_year or 0,
    }

    res = predict_risk(model, data)
    risk_score = res.get("risk_score", 0)
    risk_percent = risk_score * 100 if risk_score <= 1 else risk_score

    color = "#f87171" if risk_percent >= 50 else "#4ade80"
    verdict = "L’employé risque probablement de quitter l’entreprise." if risk_percent >= 50 else "L’employé a un risque faible de départ."

    return html.Div([
        html.Div(f"{risk_percent:.1f}%", style={"fontSize": "48px", "fontWeight": "800", "color": color}),
        html.Div(verdict, style={"marginTop": "8px", "fontSize": "18px"}),
        html.Div(f"Classe prédite: {res.get('prediction', 'N/A')}", style={"marginTop": "6px", "color": "#cbd5e1"})
    ])

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=False)