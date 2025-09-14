import os
import dash
from dash import html, Input, Output, State, dcc
import dash_bootstrap_components as dbc
from model_serving_utils import query_endpoint
from databricks import sql


class DatabricksChatbot:
    university = None
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
    @staticmethod
    def set_university(university1):
        DatabricksChatbot.university = university1
    
    @staticmethod
    def get_university():
        return DatabricksChatbot.university

    def _fetch_course_context(self, user_query):
        """
        Query Databricks Unity Catalog table for course codes found in any word of the user query.
        """
        try:
            context_list = []
            found_courses = set()  # Track courses to avoid duplicates
            
            # Split user query into individual words and check each one
            words = user_query.strip().split()
            
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    for word in words:
                        # Clean the word (remove punctuation, etc.)
                        clean_word = word.strip('.,!?;:"()[]{}')
                        
                        if not clean_word:
                            continue
                        # Select table based on global is_waterloo variable
                        if DatabricksChatbot.get_university() == "uwaterloo":
                            table_name = "workspace.augmented_courses_db.uw_posts_augmented"
                        elif DatabricksChatbot.get_university() == "ucalgary":
                            table_name = "workspace.augmented_courses_db.reddit_posts_augmented_2"
                        else:
                            table_name = "workspace.augmented_courses_db.uw_posts_augmented"
                        cur.execute(f"""
                            SELECT *
                            FROM {table_name}
                            WHERE LOWER(courseName) = LOWER(?)
                        """, (clean_word,))
                        
                        rows = cur.fetchall()
                        
                        for row in rows:
                            # Use courseName as unique identifier to avoid duplicates
                            if row.courseName not in found_courses:
                                found_courses.add(row.courseName)
                                context_list.append(
                                    f"Course: {row.courseName}\n"
                                    f"Description: {row.officialDesc}\n"
                                    f"Course Summary: {row.course_summary}\n"
                                )
                                print(f"Found course: {row.courseName}")
                                print(f"Course summary: {row.course_summary}")

            if not context_list:
                return "No relevant course info found."

            return "\n\n---\n\n".join(context_list)

        except Exception as e:
            print(f"Error fetching context: {e}")
            return "Error fetching course data."

    # ------------------ LLM Call -------------------
    def _call_model_endpoint(self, messages, max_tokens=256):
        try:
            from openai_helper import get_openai_response
            
            user_query = messages[-1]["content"].strip()
            if not user_query:
                return "Please enter a valid course code."

            # Pull external context from Databricks
            table_context = self._fetch_course_context(user_query)
            
            # Print the course context for debugging
            print("=== COURSE CONTEXT RETRIEVED ===")
            print(table_context)
            print("=== END COURSE CONTEXT ===")

            if table_context in ["No relevant course info found.", "Error fetching course data."]:
                # Use OpenAI with just the user query
                return get_openai_response(user_query, max_tokens)

            # Add context about multi-university course lookup capability
            university_context = """I can lookup university courses from University of Calgary (U of C) and University of Waterloo (UWaterloo). I have access to course information including descriptions, difficulty ratings, student discussions from Reddit, and practical insights from real students who have taken these courses."""

            # Combine table_context with user prompt
            combined_prompt = f"""You are Course Intelligence, an AI assistant that helps students with university courses.

SYSTEM CAPABILITIES:
{university_context}

COURSE INFORMATION:
{table_context}

USER QUESTION: {user_query}

Please provide a helpful response using the course information above to answer the user's question. Be conversational and include practical advice from the course data and student experiences."""

            print('Calling OpenAI API with combined prompt...')
            result = get_openai_response(combined_prompt, max_tokens)
            print(f"OpenAI Response: {result}")
            return result

        except Exception as e:
            print(f'Error calling OpenAI API: {str(e)}')
            return f"Error communicating with OpenAI: {str(e)}"

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

            try:
                assistant_response = self._call_model_endpoint(chat_history)
                
                # Ensure response is a string for React rendering
                if assistant_response is None:
                    assistant_response = "Sorry, I couldn't generate a response."
                elif not isinstance(assistant_response, str):
                    assistant_response = str(assistant_response)
                
                chat_history.append({'role': 'assistant', 'content': assistant_response})
                chat_display = self._format_chat_display(chat_history)
                
                print(chat_display)
                return chat_history, chat_display
                
            except Exception as e:
                print(f"Error in process_assistant_response: {e}")
                error_message = f"Error generating response: {str(e)}"
                chat_history.append({'role': 'assistant', 'content': error_message})
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
