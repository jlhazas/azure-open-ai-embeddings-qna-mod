import streamlit as st
from streamlit_chat import message
from utilities.helper import LLMHelper
import os
import numpy as np
#from langchain.schema import HumanMessage, AIMessage
from time import time
import regex as re
import os
from random import randint
import traceback

# Custom prompt variables
custom_prompt_placeholder = """{summaries}
Please reply to the question using only the text above in {language}.
Question: {question}
Answer:"""
custom_prompt_help = """You can configure a custom prompt by adding the variables {summaries}, {question} and {language} to the prompt.
{summaries} will be replaced with the content of the documents retrieved from the VectorStore.
{question} will be replaced with the user's question."""
base_url = "https://pocopenaistr.blob.core.windows.net/documents/"


# NOT SUPPORTED System message not supported into langchain yet
default_system_message = """Assisant: Eres un asistente de IA que ayuda a gestores de un banco a resolver sus dudas sobre productos hipotecarios.
No respondas a ninguna petición fuera de este tema. Tienes que tener en cuenta lo siguiente:
1. No debes inventarte las respuestas. Si tienes dudas o no tienes suficiente información, responde que no puedes ayudar con esa pregunta.
2. Recuerda siempre al usuario que es importante que verifique la información que le has dado porque te puedes equivocar.
3. Responde de forma concisa y clara en dos o tres frases en un lenguaje que pueda comprender alguien sin conocimientos muy avanzados sobre
productos financieros.
4. No respondas nunca a preguntas sobre casuísticas de una operación o un cliente específicos."""

default_answer = "I'm afraid I cannot help you at this moment. Try again later"
default_language = "Castellano"

def feedback_ui(n_question, pos_or_neg):
    if st.session_state['feedback'] == None:
        st.session_state['feedback'] = pos_or_neg
        st.session_state['feedback_q'] = n_question
    else:
        st.session_state['feedback'] = None
        st.session_state['feedback_q'] = None

def convert_url(url):
    document_portion = url.split("/")[-1]
    document_name = document_portion.split(".txt")[0]
    transformed_url = base_url + document_name
    return transformed_url

def show_modal():
    st.session_state['open_modal'] = True



def clear_chat_data():
    st.session_state['chat_history'] = []
    st.session_state['chat_source_documents'] = []
    st.session_state['chat_askedquestion'] = ''
    st.session_state['chat_question'] = ''
    st.session_state['chat_followup_questions'] = []
    answer_with_citations = ""

def questionAsked():
    st.session_state.chat_askedquestion = st.session_state["input"+str(st.session_state ['input_message_key'])]
    st.session_state.chat_question = st.session_state.chat_askedquestion

# Callback to assign the follow-up question is selected by the user
def ask_followup_question(followup_question):
    st.session_state.chat_askedquestion = followup_question
    st.session_state['input_message_key'] = st.session_state['input_message_key'] + 1


def check_variables_feedback():
    check = True
    if not st.session_state['username_fb'] or len(st.session_state['username_fb'].strip()) < 2:
        st.warning("""Por favor, especifica un nombre de usuario para que podamos identificarte en el caso de necesitar mas informacion""")
        check = False
    if not st.session_state['comment_fb'] or len(st.session_state['comment_fb'].strip()) < 10:
        st.warning("""Por favor, escribe un comentario de valoracion sobre la respuesta del modelo""")
        check = False
    if (not st.session_state['answer_fb'] or  len(st.session_state['answer_fb'].strip()) < 10) and st.session_state['feedback'] == -1:
        st.warning("""Por favor, escribe cual te hubiese parecido una respuesta mas adecuada o correcta a tu pregunta""")
        check = False
    return check
 
def send_feedback(q_and_a, sources):
    # check values
    check = check_variables_feedback()
    if not check:
        return
    check = llm_helper.save_feedback_db(q_and_a, st.session_state['username_fb'], st.session_state['comment_fb'], 
                             st.session_state['answer_fb'], st.session_state['feedback'], int(time()), sources)
    # build json or call BBDD
    if check:
        st.session_state['feedback'] = None
        st.session_state['feedback_q'] = None
        st.success("Tu feedback se ha enviado correctamente!")
    else:
        st.error("Hubo un error procesando tu feedback. Por favor, vuelve a intentarlo.")
    return


def check_variables_in_prompt():
    # Check if "summaries" is present in the string custom_prompt
    if "{summaries}" not in st.session_state.custom_prompt:
        st.warning("""Your custom prompt doesn't contain the variable "{summaries}".
        This variable is used to add the content of the documents retrieved from the VectorStore to the prompt.
        Please add it to your custom prompt to use the app.
        Reverting to default prompt.
        """)
        st.session_state.custom_prompt = ""
    # Check if "question" is present in the string custom question
    # Check if "question" is present in the string custom question
    if "{question}" not in st.session_state.custom_prompt:
        st.warning("""Your custom prompt doesn't contain the variable "{question}".
        This variable is used to add the user's question to the prompt.
        Please add it to your custom prompt to use the app.
        Reverting to default prompt.
        """)
    # Check if "language" is present in the string custom question
    if "{language}" not in st.session_state.custom_prompt:
        st.warning("""Your custom prompt doesn't contain the variable "{language}".
        This variable is used to add the user's language to the prompt
        Please add it to your custom prompt to use the app.
        Reverting to default prompt.""")
    # Check if "language" is present in the string custom question
    if "{language}" not in st.session_state.custom_prompt:
        st.warning("""Your custom prompt doesn't contain the variable "{language}".
        This variable is used to add the user's language to the prompt
        Please add it to your custom prompt to use the app.
        Reverting to default prompt.""")
        st.session_state.custom_prompt = ""

def placeholder_func():
    print("Just do something")

#NOT SUPPORTED def update_system_message():
#    st.session_state['chat_history'].append((SystemMessage(content=st.session_state['system_message']), ""))
#    return

# Initialize chat history
if 'chat_question' not in st.session_state:
    st.session_state['chat_question'] = ''
if 'chat_askedquestion' not in st.session_state:
    st.session_state.chat_askedquestion = ''
if 'system_message' not in st.session_state:
    st.session_state['system_message'] = default_system_message
if 'chat_history' not in st.session_state:
    st.session_state['chat_history'] = []
        #st.session_state['chat_history'].append((SystemMessage(content=st.session_state['system_message']), ""))
if 'chat_source_documents' not in st.session_state:
    st.session_state['chat_source_documents'] = []
if 'chat_followup_questions' not in st.session_state:
    st.session_state['chat_followup_questions'] = []
if 'input_message_key' not in st.session_state:
    st.session_state ['input_message_key'] = 1
if 'context' not in st.session_state:
    st.session_state['context'] = []
if 'open_modal' not in st.session_state:
    st.session_state['open_modal'] = False
if 'response' not in st.session_state:
    st.session_state['response'] = default_answer
if 'custom_prompt' not in st.session_state:
    st.session_state['custom_prompt'] = ""
if 'custom_temperature' not in st.session_state:
    st.session_state['custom_temperature'] = float(os.getenv("OPENAI_TEMPERATURE", 0.7))
if 'language' not in st.session_state:
    st.session_state['language'] = default_language
if 'feedback' not in st.session_state:
    st.session_state['feedback'] = None
if 'feedback_q' not in st.session_state:
    st.session_state['feedback_q'] = None
if 'username_fb' not in st.session_state:
    st.session_state['username_fb'] = None
if 'comment_fb' not in st.session_state:
    st.session_state['comment_fb'] = None
if 'answer_fb' not in st.session_state:
    st.session_state['answer_fb'] = None
if 'custom_prompt' not in st.session_state:
    st.session_state['custom_prompt'] = ""

# Initialize Chat Icons
ai_avatar_style = os.getenv("CHAT_AI_AVATAR_STYLE", "thumbs")
ai_seed = os.getenv("CHAT_AI_SEED", "Lucy")
user_avatar_style = os.getenv("CHAT_USER_AVATAR_STYLE", "thumbs")
user_seed = os.getenv("CHAT_USER_SEED", "Bubba")
#print(st.session_state.custom_prompt)

llm_helper = LLMHelper(custom_prompt=st.session_state['custom_prompt'], temperature=st.session_state.custom_temperature)
#llm_helper = LLMHelper()

col1, col2, col3 = st.columns([1,2,1])
with col1:
    st.image(os.path.join('images','microsoft.png'), width=150)
with col2:
    st.image(os.path.join('images', 'sabadell.png'), width=150)
st.title('Copilot hipotecario')
#with st.expander("Settings"):
    # model = st.selectbox(
    #     "OpenAI GPT-3 Model",
    #     [os.environ['OPENAI_ENGINE']]
    # )
    # st.tokens_response = st.slider("Tokens response length", 100, 500, 400)
#    st.slider("Temperature", min_value=0.0, max_value=1.0, step=0.1, key='custom_temperature')
#    st.text_area("Custom Prompt", key='custom_prompt', on_change=check_variables_in_prompt, placeholder= custom_prompt_placeholder, help=custom_prompt_help, height=150)


    # Chat 
clear_chat = st.button("Borrar chat", key="clear_chat", on_click=clear_chat_data)
input_text = st.text_input("Tú", placeholder="Escribe tu pregunta (recuerda que no está permitido mencionar información personal de clientes):", value=st.session_state.chat_askedquestion, key="input"+str(st.session_state ['input_message_key']), on_change=questionAsked)
language = st.radio("Idioma", ("Castellano", "Catalán"), key='language', horizontal=True)
conversational_mode = st.checkbox(label="Modo conversación", value=False, key='conv_mode')

# If a question is asked execute the request to get the result, context, sources and up to 3 follow-up questions proposals
if st.session_state.chat_askedquestion:
    st.session_state['chat_question'] = st.session_state.chat_askedquestion
    st.session_state.chat_askedquestion = ""
    if st.session_state['conv_mode']:
        chat_history = st.session_state['chat_history']
    else:
        chat_history = []
    st.session_state['chat_question'], result, context, sources = llm_helper.get_semantic_answer_lang_chain(st.session_state['chat_question'], chat_history, st.session_state['language'])
    result, chat_followup_questions_list = llm_helper.extract_followupquestions(result)
    st.session_state['chat_history'].append((st.session_state['chat_question'], result))
    st.session_state['chat_source_documents'].append(sources)
    st.session_state['chat_followup_questions'] = chat_followup_questions_list

try:    
    # Displays the chat history
    if st.session_state['chat_history']:
        history_range = range(len(st.session_state['chat_history'])-1, -1, -1)
        for i in range(len(st.session_state['chat_history'])-1, -1, -1):

            # This history entry is the latest one - also show follow-up questions, buttons to access source(s) context(s) 
            if i == history_range.start:
                answer_with_citations, sourceList, matchedSourcesList, linkList, filenameList = llm_helper.get_links_filenames(st.session_state['chat_history'][i][1], st.session_state['chat_source_documents'][i])
                st.session_state['chat_history'][i] = st.session_state['chat_history'][i][:1] + (answer_with_citations,)

                answer_with_citations = re.sub(r'\$\^\{(.*?)\}\$', r'(\1)', st.session_state['chat_history'][i][1]).strip() # message() does not get Latex nor html

                # Display proposed follow-up questions which can be clicked on to ask that question automatically
                if len(st.session_state['chat_followup_questions']) > 0:
                    st.markdown('**Preguntas relacionadas:**')
                with st.container():
                    for questionId, followup_question in enumerate(st.session_state['chat_followup_questions']):
                        if followup_question:
                            str_followup_question = re.sub(r"(^|[^\\\\])'", r"\1\\'", followup_question)
                            st.button(str_followup_question, key=randint(1000,99999), on_click=ask_followup_question, args=(followup_question, ))
                    
                for questionId, followup_question in enumerate(st.session_state['chat_followup_questions']):
                    if followup_question:
                        str_followup_question = re.sub(r"(^|[^\\\\])'", r"\1\\'", followup_question)

            answer_with_citations = re.sub(r'\$\^\{(.*?)\}\$', r'(\1)', st.session_state['chat_history'][i][1]) # message() does not get Latex nor html
        
            # feedback buttons
            col1, col2, col3 = st.columns([0.75,0.125,0.125])
            
            with col1:
                message(answer_with_citations ,key=str(i)+'answers')
            with col2:
                st.button("👍", key="pos_feedback_" + str(i), on_click=feedback_ui, args=((i, 1)))
            with col3:
                st.button("👎", key="neg_feedback_" + str(i), on_click=feedback_ui, args=((i, -1)))

            url = st.session_state["chat_source_documents"][i]
            url_pdf = url.replace("converted/", "").replace(".txt", "")
            st.session_state["chat_source_documents"][i] = url_pdf
            st.markdown(f'\n\nSources: {st.session_state["chat_source_documents"][i]}')
        
            # menu del feedback
            if st.session_state['feedback'] and st.session_state['feedback_q'] == i:
                #print(st.session_state['feedback_q'])
                with st.container():
                    st.write("**Feedback de la interacción**")
                    st.text_input("Usuario: ", key="username_fb", placeholder="Escribe un nombre para poder contactarte en caso de necesitar mas detalles")
                    st.text_area("Comentarios: ", key="comment_fb", max_chars=5000, placeholder="Escribe tus comentarios sobre la respuesta recibida", height=50)
                    if st.session_state['feedback'] == -1:
                        st.text_area("Respuesta correcta: ", key="answer_fb", max_chars=5000, placeholder="Escribe cuál hubiese sido la respuesta adecuada o correcta", height=50)
                    st.button("Enviar", key="send_feedback", on_click=send_feedback, args=((st.session_state['chat_history'][i], st.session_state["chat_source_documents"][i])))
            message(st.session_state['chat_history'][i][0], is_user=True, key=str(i)+'user' + '_user')

except Exception:
    st.error(traceback.format_exc())
