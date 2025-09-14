import os
import dash
from dash import html, Input, Output, State, dcc
import dash_bootstrap_components as dbc
from model_serving_utils import query_endpoint
from databricks import sql


class DatabricksChatbot:
    def __init__(self, app, endpoint_name, height='600px'):
        self.app = app
        self.endpoint_name = endpoint_name
        self.height = height
        self.layout = self._create_layout()
        self._create_callbacks()
        self._add_custom_css()

    # ------------------ Databricks Connection ------------------
    def _get_connection(self):
        """
        Create a Databricks SQL connection.
        Picks up credentials from environment variables.
        """
        server = os.getenv("databricks_server_name")
        http_path = os.getenv("databricks_http_path")
        token = os.getenv("databricks_access_token")

        if not all([server, http_path, token]):
            raise ValueError("Databricks environment variables are not set properly.")

        return sql.connect(
            server_hostname=server,
            http_path=http_path,
            access_token=token
        )

    def _fetch_course_context(self, user_query):
        """
        Query Databricks Unity Catalog table for exact course code matches only.
        """
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT *
                        FROM workspace.default.reddit_posts
                        WHERE LOWER(course_code) = LOWER(%s)
                    """, (user_query.strip(),))
                    
                    rows = cur.fetchall()

            if not rows:
                return "No relevant course info found."

            context_list = []
            for row in rows:
                context_list.append(
                    f"Course: {row.course_code} — {row.course_name}\n"
                    f"Difficulty: {row.how_hard}\n"
                    f"Time Consuming: {row.time_consuming}\n"
                    f"Project vs Theory: {row.project_vs_theory}\n"
                    f"Resume Value: {row.resume_value}\n"
                    f"Best Professors: {row.best_professors}\n"
                    f"Complaints: {row.worst_professors}"
                )
            return "\n\n---\n\n".join(context_list)

        except Exception as e:
            print(f"Error fetching context: {e}")
            return "Error fetching course data."

    # ------------------ LLM Call -------------------
    def _call_model_endpoint(self, messages, max_tokens=256):
        try:
            user_query = messages[-1]["content"].strip()
            if not user_query:
                return "Please enter a valid course code."

            # Pull external context from Databricks
            table_context = self._fetch_course_context(user_query)

            if table_context in ["No relevant course info found.", "Error fetching course data."]:
                return table_context

            # Add system prompt with context
            system_prompt = {
                "role": "system",
                "content": f"Use the following course information when answering:\n{table_context}"
            }

            enriched_messages = [system_prompt] + messages

            print('Calling model endpoint with enriched context...')
            return query_endpoint(self.endpoint_name, enriched_messages, max_tokens)["content"]

        except Exception as e:
            print(f'Error calling model endpoint: {str(e)}')
            return f"Error communicating with the model: {str(e)}"

    # ------------------ Dash Layout + Callbacks ------------------
    def _create_layout(self):
        return html.Div([
            dbc.Card([
                dbc.CardBody([
                    html.Div(id='chat-history', className='chat-history'),
                ], className='d-flex flex-column chat-body')
            ], className='chat-card mb-3 flex-grow-1 d-flex flex-column'),
            dbc.InputGroup([
                dbc.Input(id='user-input', placeholder='Enter course code...', type='text'),
                dbc.Button('Send', id='send-button', color='success', n_clicks=0, className='ms-2'),
                dbc.Button('Clear', id='clear-button', color='danger', n_clicks=0, className='ms-2'),
            ], className='mb-3'),
            dcc.Store(id='assistant-trigger'),
            dcc.Store(id='chat-history-store'),
            html.Div(id='dummy-output', style={'display': 'none'}),
        ], className='d-flex flex-column chat-container p-3')

    def _create_callbacks(self):
        @self.app.callback(
            Output('chat-history-store', 'data', allow_duplicate=True),
            Output('chat-history', 'children', allow_duplicate=True),
            Output('user-input', 'value'),
            Output('assistant-trigger', 'data'),
            Input('send-button', 'n_clicks'),
            Input('user-input', 'n_submit'),
            State('user-input', 'value'),
            State('chat-history-store', 'data'),
            prevent_initial_call=True
        )
        def update_chat(send_clicks, user_submit, user_input, chat_history):
            if not user_input:
                return dash.no_update, dash.no_update, dash.no_update, dash.no_update

            chat_history = chat_history or []
            chat_history.append({'role': 'user', 'content': user_input.strip()})
            chat_display = self._format_chat_display(chat_history)
            chat_display.append(self._create_typing_indicator())

            return chat_history, chat_display, '', {'trigger': True}

        @self.app.callback(
            Output('chat-history-store', 'data', allow_duplicate=True),
            Output('chat-history', 'children', allow_duplicate=True),
            Input('assistant-trigger', 'data'),
            State('chat-history-store', 'data'),
            prevent_initial_call=True
        )
        def process_assistant_response(trigger, chat_history):
            if not trigger or not trigger.get('trigger'):
                return dash.no_update, dash.no_update

            chat_history = chat_history or []
            if not chat_history or chat_history[-1]['role'] != 'user':
                return dash.no_update, dash.no_update

            assistant_response = self._call_model_endpoint(chat_history)
            chat_history.append({'role': 'assistant', 'content': assistant_response})
            chat_display = self._format_chat_display(chat_history)

            return chat_history, chat_display

        @self.app.callback(
            Output('chat-history-store', 'data', allow_duplicate=True),
            Output('chat-history', 'children', allow_duplicate=True),
            Input('clear-button', 'n_clicks'),
            prevent_initial_call=True
        )
        def clear_chat(n_clicks):
            if n_clicks:
                return [], []
            return dash.no_update, dash.no_update

    def _format_chat_display(self, chat_history):
        return [
            html.Div([
                html.Div(msg['content'], className=f"chat-message {msg['role']}-message")
            ], className=f"message-container {msg['role']}-container")
            for msg in chat_history if isinstance(msg, dict) and 'role' in msg
        ]

    def _create_typing_indicator(self):
        return html.Div([
            html.Div(className='chat-message assistant-message typing-message', children=[
                html.Div(className='typing-dot'),
                html.Div(className='typing-dot'),
                html.Div(className='typing-dot')
            ])
        ], className='message-container assistant-container')

    def _add_custom_css(self):
        custom_css = '''
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700&display=swap');
        body { font-family: 'DM Sans', sans-serif; background-color: #F9F7F4; }
        .chat-container { max-width: 800px; margin: 40px auto; background: #FFF; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); display: flex; flex-direction: column; flex: 1 1 auto; }
        .chat-card { border: none; background-color: #EEEDE9; flex-grow: 1; display: flex; flex-direction: column; overflow: hidden; }
        .chat-body { flex-grow: 1; overflow: hidden; display: flex; flex-direction: column; }
        .chat-history { flex-grow: 1; overflow-y: auto; padding: 15px; max-height: 70vh; }
        .message-container { display: flex; margin-bottom: 15px; }
        .user-container { justify-content: flex-end; }
        .chat-message { max-width: 80%; padding: 10px 15px; border-radius: 20px; font-size: 16px; line-height: 1.4; }
        .user-message { background-color: #FF3621; color: white; }
        .assistant-message { background-color: #1B3139; color: white; }
        .typing-message { background-color: #2D4550; color: #EEEDE9; display: flex; justify-content: center; align-items: center; min-width: 60px; }
        .typing-dot { width: 8px; height: 8px; background-color: #EEEDE9; border-radius: 50%; margin: 0 3px; animation: typing-animation 1.4s infinite ease-in-out; }
        .typing-dot:nth-child(1) { animation-delay: 0s; }
        .typing-dot:nth-child(2) { animation-delay: 0.2s; }
        .typing-dot:nth-child(3) { animation-delay: 0.4s; }
        @keyframes typing-animation { 0% { transform: translateY(0px); } 50% { transform: translateY(-5px); } 100% { transform: translateY(0px); } }
        #user-input { border-radius: 20px; border: 1px solid #DCE0E2; }
        #send-button, #clear-button { border-radius: 20px; width: 100px; }
        #send-button { background-color: #00A972; border-color: #00A972; }
        #clear-button { background-color: #98102A; border-color: #98102A; }
        .input-group { flex-wrap: nowrap; margin-top: auto; }
        '''
        self.app.index_string = self.app.index_string.replace(
            '</head>',
            f'<style>{custom_css}</style></head>'
        )

        self.app.clientside_callback(
            """
            function(children) {
                var chatHistory = document.getElementById('chat-history');
                if(chatHistory) { chatHistory.scrollTop = chatHistory.scrollHeight; }
                return '';
            }
            """,
            Output('dummy-output', 'children'),
            Input('chat-history', 'children'),
            prevent_initial_call=True
        )
