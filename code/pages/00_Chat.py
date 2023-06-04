import streamlit as st
from streamlit_chat import message
from utilities.helper import LLMHelper
import os
import numpy as np
from langchain.schema import HumanMessage, AIMessage
from streamlit_modal import Modal
from time import time

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

def clear_text_input():
    st.session_state['question'] = st.session_state['input']
    st.session_state['input'] = ""


def clear_chat_data():
    st.session_state['input'] = ""
    st.session_state['chat_history'] = []
    # NOT SUPPORTED st.session_state['chat_history'].append(SystemMessage(content=st.session_state['system_message']))
    st.session_state['source_documents'] = []

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
        st.session_state.custom_prompt = ""

def placeholder_func():
    print("Just do something")

#NOT SUPPORTED def update_system_message():
#    st.session_state['chat_history'].append((SystemMessage(content=st.session_state['system_message']), ""))
#    return

# Initialize chat history
if 'question' not in st.session_state:
    st.session_state['question'] = None
if 'system_message' not in st.session_state:
    st.session_state['system_message'] = default_system_message
if 'chat_history' not in st.session_state:
    st.session_state['chat_history'] = []
    #st.session_state['chat_history'].append((SystemMessage(content=st.session_state['system_message']), ""))
if 'source_documents' not in st.session_state:
    st.session_state['source_documents'] = []
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
#print(st.session_state.custom_prompt)
llm_helper = LLMHelper(custom_prompt=st.session_state['custom_prompt'], temperature=st.session_state.custom_temperature)
#llm_helper = LLMHelper()

with st.expander("Settings"):
    # model = st.selectbox(
    #     "OpenAI GPT-3 Model",
    #     [os.environ['OPENAI_ENGINE']]
    # )
    # st.tokens_response = st.slider("Tokens response length", 100, 500, 400)
    st.slider("Temperature", min_value=0.0, max_value=1.0, step=0.1, key='custom_temperature')
    st.text_area("Custom Prompt", key='custom_prompt', on_change=check_variables_in_prompt, placeholder= custom_prompt_placeholder, help=custom_prompt_help, height=150)

    # NOT SUPPORTED st.text_area("System Message", key='system_message', on_change=update_system_message, placeholder=default_system_message, height=150)

# Chat
st.text_input("Tú: ", placeholder="Escribe tu pregunta", key="input", on_change=clear_text_input)
clear_chat = st.button("Borrar historial del chat", key="clear_chat", on_click=clear_chat_data)


language = st.radio("Idioma", ("Castellano", "Catalán"), key='language', horizontal=True)
#prueba = st.button("Prueba", key="prueba button", on_click=clear_chat_data)

if st.session_state['question']:
    #question, result, context, sources = llm_helper.get_semantic_answer_lang_chain(st.session_state['question'], st.session_state['chat_history'], st.session_state['language'])
    question, result, context, sources = llm_helper.get_semantic_answer_lang_chain(st.session_state['question'], [], st.session_state['language'])

    #question = st.session_state['question']
    #result = "Hello, this is not ChatGPT, just a placeholder."
    #sources = "https://pocopenaistr.blob.core.windows.net/documents/converted/manual.pdf.txt\nhttps://pocopenaistr.blob.core.windows.net/documents/converted/manual.pdf.txt"
    #context = "Answer context"
    #sources = list(map(convert_url, sources.split("\n")))
    human_message = HumanMessage(content=question)
    ai_message = AIMessage(content=result)
    #print(human_message.type)

    #ai_message =
    st.session_state['chat_history'].append((human_message, ai_message))
    st.session_state['source_documents'].append(sources)
    st.session_state['context'].append([context])

    st.session_state['question'] = None
    #print(st.session_state['chat_history'])

if len(st.session_state['chat_history']):
    #print(st.session_state['chat_history'])
    for i in range(len(st.session_state['chat_history'])-1, -1, -1):
        q_and_a = st.session_state['chat_history'][i]
        
        # feedback buttons
        col1, col2, col3 = st.columns([0.75,0.125,0.125])
        
        with col1:
            message(q_and_a[1].content, key=str(i))
        with col2:
            st.button("👍", key="pos_feedback_" + str(i), on_click=feedback_ui, args=((i, 1)))
        with col3:
            st.button("👎", key="neg_feedback_" + str(i), on_click=feedback_ui, args=((i, -1)))
        #print(st.session_state["source_documents"][i])
        # sources and context
        st.markdown(f'\n\nSources: {st.session_state["source_documents"][i]}')
        with st.expander("Información en la que se basa la respuesta"):
            st.markdown(st.session_state['context'][i].replace('$', '\$'))
        
        # menu del feedback
        if st.session_state['feedback'] and st.session_state['feedback_q'] == i:
            #print(st.session_state['feedback_q'])
            with st.container():
                st.write("**Feedback de la interacción**")
                st.text_input("Usuario: ", key="username_fb", placeholder="Escribe un nombre para poder contactarte en caso de necesitar mas detalles")
                st.text_area("Comentarios: ", key="comment_fb", max_chars=5000, placeholder="Escribe tus comentarios sobre la respuesta recibida", height=50)
                if st.session_state['feedback'] == -1:
                    st.text_area("Respuesta correcta: ", key="answer_fb", max_chars=5000, placeholder="Escribe cuál hubiese sido la respuesta adecuada o correcta", height=50)
                st.button("Enviar", key="send_feedback", on_click=send_feedback, args=((q_and_a, st.session_state["source_documents"][i])))
        message(q_and_a[0].content, is_user=True, key=str(i) + '_user')
# modificacion para que no mantenga historial de mensajes


#if st.session_state['open_modal']:
#modal.open()
#if modal.is_open():
#    with modal.container():
#        st.write("Text goes here")
#        html_string = '''
#    <h1>HTML string in RED</h1>

#    <script language="javascript">
#      document.querySelector("h1").style.color = "red";
#    </script>
#    '''
#        components.html(html_string)

#        st.write("Some fancy text")
#        value = st.checkbox("Check me")
#        st.write(f"Checkbox checked: {value}")
