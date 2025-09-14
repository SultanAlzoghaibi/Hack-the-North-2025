# Ensure environment variable is set correctly
import os
import dash
import dash_bootstrap_components as dbc
from dash import html, dcc, Input, Output, State
from DatabricksChatbot import DatabricksChatbot
from model_serving_utils import is_endpoint_supported

# ==========================================================
# 🔗 DATABASE CONNECTION (Databricks)
# Replace with your own Databricks SQL / Unity Catalog connection
#
# def query_databricks(university, user_question):
#     """
#     Run a query against Databricks (Reddit + RMP + other data) for the given university
#     and combine with LLM context to answer the user's question. Yes.
#     """
#     pass
# ==========================================================

# Ensure environment variable is set correctly
serving_endpoint = os.getenv('SERVING_ENDPOINT')
assert serving_endpoint, (
    "Unable to determine serving endpoint to use for chatbot app. If developing locally, "
    "set the SERVING_ENDPOINT environment variable to the name of your serving endpoint. If "
    "deploying to Databricks, include a serving endpoint resource named "
    "'serving_endpoint' with CAN_QUERY permissions."
)

# Check if the endpoint is supported
endpoint_supported = is_endpoint_supported(serving_endpoint)

# Initialize the Dash app with a clean theme
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.FLATLY], suppress_callback_exceptions=True)
app.title = "Course Intelligence"

# ==========================================================
# Layouts
# ==========================================================

# Homepage layout inspired by ForagerProject’s style
home_layout = html.Div(
    style={"minHeight": "100vh", "display": "flex", "flexDirection": "column"},
    children=[
        # Hero / Header section
        html.Div(
            style={
                "flex": "1",
                "display": "flex",
                "alignItems": "center",
                "justifyContent": "center",
                "backgroundColor": "#f8f9fa",  # light background
                "padding": "80px 20px",
            },
            children=[
                html.Div(
                    children=[
                        html.H1("Course Intelligence", style={"fontSize": "4rem", "marginBottom": "0.5rem"}),
                        html.P(
                            "Get insights from student reviews and course data to help you choose professors and courses wisely.",
                            style={"fontSize": "1.5rem", "color": "#555"}
                        ),
                    ],
                    style={"textAlign": "center", "maxWidth": "800px"},
                )
            ]
        ),

        # University selection section
        html.Div(
            style={"padding": "40px 20px"},
            children=[
                dbc.Row(
                    dbc.Col(
                        html.Div([
                            html.H4("Select Your University", className="mb-4", style={"textAlign": "center"}),
                            dcc.Dropdown(
                                id="university-dropdown",
                                options=[
                                    {"label": "University of Toronto", "value": "uoft"},
                                    {"label": "University of Waterloo", "value": "uw"},
                                    {"label": "University of Calgary", "value": "calgary"},
                                    # Add more here later easily
                                ],
                                placeholder="Choose a university...",
                                style={"width": "60%", "margin": "0 auto"}
                            ),
                            dbc.Button("Go", id="go-button", color="primary", className="mt-3", n_clicks=0, style={"display": "block", "margin": "20px auto"})
                        ]),
                        width=12
                    )
                )
            ]
        ),

        # Footer / optional additional info
        html.Div(
            style={"padding": "20px 0", "backgroundColor": "#343a40", "color": "white"},
            children=[
                html.Div(
                    style={"textAlign": "center"},
                    children=[
                        html.P("Powered by Databricks • Data from Reddit & RateMyProfessor", style={"margin": "0"}),
                        html.P("© 2025 Course Intelligence", style={"margin": "0", "fontSize": "0.9rem"})
                    ]
                )
            ]
        )
    ]
)

# Chatbot page layout (without the placeholder text)
if not endpoint_supported:
    chatbot_layout = dbc.Container([
        dbc.Row([
            dbc.Col([
                html.H2("Ask about courses and professors", className="mb-3"),
                dbc.Alert(
                    "The specified endpoint is not compatible with this chatbot template. "
                    "Please ensure you have a chat-completions-compatible endpoint.",
                    color="info",
                    className="mt-4"
                )
            ], width={'size': 8, 'offset': 2})
        ])
    ], fluid=True)
else:
    chatbot = DatabricksChatbot(app=app, endpoint_name=serving_endpoint, height='600px')
    chatbot_layout = dbc.Container([
        dbc.Row([
            dbc.Col([
                html.H2("Ask about courses & professors", className="mb-4", style={"textAlign": "center"}),
                chatbot.layout
            ], width={'size': 8, 'offset': 2})
        ])
    ], fluid=True)

# ==========================================================
# App layout with page navigation
# ==========================================================
app.layout = dbc.Container([
    dcc.Location(id="url", refresh=False),
    html.Div(id="page-content")
], fluid=True, style={"padding": "0", "margin": "0"})

# ==========================================================
# Callbacks for navigation
# ==========================================================
@app.callback(
    Output("url", "pathname"),
    Input("go-button", "n_clicks"),
    State("university-dropdown", "value"),
    prevent_initial_call=True
)
def navigate_to_chat(n_clicks, university):
    if n_clicks and university:
        return f"/chat/{university}"
    return dash.no_update

@app.callback(
    Output("page-content", "children"),
    Input("url", "pathname")
)
def display_page(pathname):
    if pathname and pathname.startswith("/chat"):
        return chatbot_layout
    return home_layout

# ==========================================================
# Run the app
# ==========================================================
if __name__ == '__main__':
    app.run(debug=True)

serving_endpoint = os.getenv('SERVING_ENDPOINT')
assert serving_endpoint, (
    "Unable to determine serving endpoint to use for chatbot app. If developing locally, "
    "set the SERVING_ENDPOINT environment variable to the name of your serving endpoint. If "
    "deploying to a Databricks app, include a serving endpoint resource named "
    "'serving_endpoint' with CAN_QUERY permissions."
)

# Check if the endpoint is supported
endpoint_supported = is_endpoint_supported(serving_endpoint)

# Initialize the Dash app with a clean theme
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.FLATLY], suppress_callback_exceptions=True)
app.title = "Course Intelligence"

# ==========================================================
# Layouts
# ==========================================================

# Home page layout
home_layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.H1("Course Intelligence", className="text-center mb-4"), width=12)
    ]),
    dbc.Row([
        dbc.Col([
            html.H5("Select your university:"),
            dcc.Dropdown(
                id="university-dropdown",
                options=[
                    {"label": "University of Toronto (UofT)", "value": "uoft"},
                    {"label": "University of Waterloo (UW)", "value": "uw"},
                    {"label": "University of Calgary", "value": "calgary"},
                ],
                placeholder="Choose a university...",
                className="mb-3"
            ),
            dbc.Button("Go", id="go-button", color="primary", className="mt-2")
        ], width={"size": 6, "offset": 3})
    ])
], fluid=True)

# Chatbot page layout (default placeholder)
if endpoint_supported:
    chatbot = DatabricksChatbot(app=app, endpoint_name=serving_endpoint, height='600px')
    chatbot_layout = dbc.Container([
        dbc.Row([
            dbc.Col([
                html.H2("Ask about courses & professors", className="mb-4"),
                chatbot.layout
            ], width={'size': 8, 'offset': 2})
        ])
    ], fluid=True)

# ==========================================================
# App layout with page navigation
# ==========================================================
app.layout = dbc.Container([
    dcc.Location(id="url", refresh=False),
    html.Div(id="page-content")
], fluid=True)

# ==========================================================
# Callbacks for navigation
# ==========================================================
@app.callback(
    Output("url", "pathname"),
    Input("go-button", "n_clicks"),
    State("university-dropdown", "value"),
    prevent_initial_call=True
)
def navigate_to_chat(n_clicks, university):
    if university:
        return f"/chat/{university}"
    return dash.no_update

@app.callback(
    Output("page-content", "children"),
    Input("url", "pathname")
)
def display_page(pathname):
    if pathname and pathname.startswith("/chat"):
        return chatbot_layout
    return home_layout

# ==========================================================
# Run the app
# ==========================================================
if __name__ == '__main__':
    app.run(debug=True)
