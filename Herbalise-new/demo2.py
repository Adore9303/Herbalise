#importing all the neccesary libraries and models for the app
import streamlit as st
import base64
import plotly.express as px
import streamlit_authenticator as stauth
import PyPDF2
import os 
import sqlite3
import yaml
import openai
from PyPDF2 import PdfFileReader
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings, HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
from langchain.chat_models import ChatOpenAI
from dotenv import load_dotenv
from yaml.loader import SafeLoader
from html_templet import css, bot_template, user_template
with open(r'credentials.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

logged_in = False

# Set the page configuration
st.set_page_config(
    page_title="Herbalize",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="collapsed",
)



# Load environment variables from .env file
load_dotenv()  
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # Get API key from environment variable

#user interface of the streamlit app
df = px.data.iris()
@st.cache_data
def get_img_as_base64(file):
    with open(file, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

#providing the image path for the background image
img = get_img_as_base64(r"bgtwo.png")
openai.api_key = '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'

#style section
page_bg_img = f"""
<style>
[data-testid="stAppViewContainer"] > .main {{
background-image: url("data:image/png;base64,{img}");
background-size: 100%;
background-position: top left;
background-repeat: no-repeat;
background-attachment: local;
}}

[data-testid="stSidebar"] > div:first-child {{
background-image: url("https://wallpapercave.com/wp/wp6845532.jpg"); 
background-repeat: no-repeat;
background-size: 100%;
background-attachment: fixed;
background-position: right;
font-color:Black;
}}

[data-testid="stHeader"] {{
background: rgba(0,0,0,0);
color: black;
}}


[data-testid="stToolbar"] {{
right: 2rem;
}}
</style>
"""

#creating a database to store the practioner's credentials
conn = sqlite3.connect('data.db')
c = conn.cursor()
def create_usertable(): 
    c.execute('CREATE TABLE IF NOT EXISTS userstable(username TEXT,password TEXT)')
def add_userdata(username,password):
    c.execute('INSERT INTO userstable(username,password) VALUES (?,?)', (username,password))
    conn.commit()
def login_user(username,password):
    c.execute('SELECT * FROM userstable WHERE username =? AND password = ?', (username,password))
    data = c.fetchall()
    return data
authenticator = stauth.Authenticate (
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
    config['preauthorized']
)
def login():
    username_input = st.text_input("Username")
    password_input = st.text_input("Password", type='password')
    if st.button("Login"):
        data=login_user(username_input, password_input)
        print("Data from the database:", data)
        if data:
            st.write(f'Welcome *{data[0][0]}*')
            st.success("You have successfully logined. Go to the Application")
            logged_in=True
            return True
        else:
            st.error('username/password is incorrect')
            return False

#creating a sidebar for navigation bwt various part of the streamlit app
st.markdown(page_bg_img, unsafe_allow_html=True)
st.sidebar.title('Configuration')

#providing the patients free access to answer their queries
def get_openai_answer(question):
    try:
        # Use a structured message with a system message and a user message
        messages = [
            {"role": "system", "content": "You are a helpful assistant that provides information about Ayurveda."},
            {"role": "user", "content": question}
        ]

        # Create a chat-based completion request
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-16k-0613",
            messages=messages,
            max_tokens=1000  # Allow some extra tokens for flexibility
        )

        # Extract the model's reply
        answer = response['choices'][0]['message']['content']

        # Find the farthest full stop (period) before the 1000th character
        last_period_index = answer[:1000].rfind('.')

        if last_period_index != -1:
            # Truncate at the farthest period
            answer = answer[:last_period_index + 1]

        # If the answer is too long, truncate it to 1000 characters
        if len(answer) > 1000:
            answer = answer[:1000]

        return answer.strip()
    except Exception as e:
        return f"An error occurred: {str(e)}"


#mail function of the streamlit app
def main():
    menu = ["Home", "Login", "SignUp","Application"]
    choice = st.sidebar.selectbox("Menu", menu)


    if choice == "Home":
        st.markdown(
        """
        <style>
        
        #root{
        height:800px;
        width: 1000px;
        }
        .block-container.css-1y4p8pa.ea3mdgi4{
        padding-top:0px !important;
        }
        .st-b3.st-b8.st-dh.st-b1.st-bq.st-ae.st-af.st-ag.st-ah.st-ai.st-aj.st-br.st-de{
            height: 40px !important;
        }
        .css-q8sbsg.e1nzilvr5{
        font-size:2em !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
        st.subheader("Home")
        blog = get_openai_answer("Write a blog about ayurveda")
        st.write(blog)
        st.subheader("Ask a question about Ayurveda")
        user_question = st.text_area("")
        initial_sidebar_state="collapsed"
        if st.button("Submit"):
            print("hello")
            # Perform question-answering using the extracted text
            answer = get_openai_answer(user_question)
            # Display the answer
            st.write("Answer:")
            st.write(answer)
        

    elif choice == "Login":
        st.subheader("Login Section")
        login()

    elif choice == "SignUp":
        st.subheader("Create an Account")
        username = st.text_input('Username')
        password = st.text_input('Password',type='password')
        if st.button('SignUp'):
            create_usertable()
            add_userdata(username,password)
            st.success("You have successfully created an account. Go to the Login Menu to login")

    elif choice == "Application" and logged_in:
        st.subheader("Application")
        
        application()
        

def extract_text_from_pdf(pdf_path):
    text = ""
    with open(pdf_path, "rb") as pdf_file:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        for page_num in range(len(pdf_reader.pages)):
            text += pdf_reader.pages[page_num].extract_text()
    return text

# Example usage:
pdf_path = r"C:\Users\mayan\Downloads\testrealrr.pdf"
extracted_text = extract_text_from_pdf(pdf_path)


def get_openai_answerr(question, context):
    try:
        # Combine the context and user message into one
        user_message = context + "\n" + question

        # Use a structured message with a system message and a combined user message
        messages = [
            {"role": "system", "content": "You are a helpful assistant that provides information."},
            {"role": "user", "content": user_message}
        ]

        # Create a chat-based completion request
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-0613",
            messages=messages,
            max_tokens=1000  # Allow some extra tokens for flexibility
        )

        # Extract the model's reply
        answer = response['choices'][0]['message']['content']

        # Find the farthest full stop (period) before the 1000th character
        last_period_index = answer[:1000].rfind('.')

        if last_period_index != -1:
            # Truncate at the farthest period
            answer = answer[:last_period_index + 1]

        # If the answer is too long, truncate it to 1000 characters
        if len(answer) > 1000:
            answer = answer[:1000]

        return answer.strip()
    except Exception as e:
        return f"An error occurred: {str(e)}"



def application():
#     if "chat_history" not in st.session_state:
#         st.session_state.chat_history = None
#     if "conversation" not in st.session_state:
#         st.session_state.conversation= None
    
    st.write(css, unsafe_allow_html=True)
    prompt = st.text_input("Enter the prompt for the medicine formulation")
    if st.button('submit'):
       answerr= get_openai_answerr(prompt, extracted_text)
       st.write("Answer:")
       st.write(answerr)
#         if prompt:
#             with st.spinner("processing"):
#                 # Get the texts from the pdf
#                 raw_data = extract_text_from_pdf(pdf_path)
#                 #get the text chunks
#                 text_chunks = get_text_chunks(raw_data)
#                 #create embedding of the text chunks
#                 vectorstore = get_vectorstore(text_chunks)
#                 #create conversation chain
#                 conversation= get_conversation_chain(vectorstore)
#                 st.write(conversation)

# #to extract the text from the pdf for procesing



# #converting all the text from the pdf into small chunks of data to process
# def get_text_chunks(raw_data):
#     text_slitter = CharacterTextSplitter(
#         separator="\n",
#         chunk_size=1000,
#         chunk_overlap=200,
#         length_function=len
#     )
#     chunks = text_slitter.split_text(raw_data)
#     return chunks

# def get_vectorstore(text_chunks):
#     embeddings = OpenAIEmbeddings( openai_api_key = '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')
#     #embeddings = HuggingFaceEmbeddings(model_name='hkunlp/instructor-xl')
#     vectorstore = FAISS.from_texts(texts=text_chunks, embedding=embeddings)
#     return vectorstore

# def get_conversation_chain(vectorstore):
#     llm = ChatOpenAI()
#     memory = ConversationBufferMemory(
#         memory_key='chat_history', return_messages=True
#     )
#     conversation_chain = ConversationalRetrievalChain.from_llm(
#         llm=llm,
#         retriever=vectorstore.as_retriever(),
#         memory=memory,
#     )
#     return conversation_chain


if __name__ == "__main__":
    main()