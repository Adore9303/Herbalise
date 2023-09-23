#importing all the neccesary libraries and models for the app
import streamlit as st
import base64
import plotly.express as px
import streamlit_authenticator as stauth
import PyPDF2
from PyPDF2 import PdfReader
import os 
import sqlite3
import yaml
from dotenv import load_dotenv
from yaml.loader import SafeLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings, HuggingFaceInstructEmbeddings
from langchain.vectorstores import FAISS
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
from langchain.chat_models import ChatOpenAI
from html_templet import css, bot_template, user_template
with open(r'C:\Users\Abhishek\Desktop\Herbalise\credentials.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

# Set the page configuration
st.set_page_config(
    page_title="Ayurvedic Practitioner's Portal",
    page_icon="🌿",
    layout="centered",  
    initial_sidebar_state="expanded",
)

load_dotenv()  # Load environment variables from .env file
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # Get API key from environment variable

#user interface of the streamlit app
df = px.data.iris()
@st.cache_data
def get_img_as_base64(file):
    with open(file, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

img = get_img_as_base64(r"C:\Users\Abhishek\Desktop\pexels-nataliya-vaitkevich-7615574.jpg")

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

st.markdown(page_bg_img, unsafe_allow_html=True)
st.sidebar.title("Configuration")


def main():
    st.title("Ayurvedic Practitioner's Portal")
    menu = ["Home", "Login", "SignUp","Application"]
    choice = st.sidebar.selectbox("Menu", menu)

    if choice == "Home":
        st.subheader("Home")
        

    elif choice == "Login":
        st.subheader("Login Section")
        username_input = st.text_input("Username")
        password_input = st.text_input("Password", type='password')
        if st.button("Login"):
            data=login_user(username_input, password_input)
            print("Data from the database:", data)
            if data:
                st.write(f'Welcome *{data[0][0]}*')
                
            else:
                st.error('username/password is incorrect')
    elif choice == "SignUp":
        st.subheader("Create an Account")
        username = st.text_input('Username')
        password = st.text_input('Password',type='password')
        if st.button('SignUp'):
            create_usertable()
            add_userdata(username,password)
            st.success("You have successfully created an account. Go to the Login Menu to login")

    elif choice == "Application":
        st.subheader("Application")
        application()

def application():
    if "conversation" not in st.session_state:
        st.session_state.conversation = None
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = None
    
    st.write(css, unsafe_allow_html=True)
    prompt = st.text_input("Enter the prompt for the medicine formulation")
    if st.button('submit'):
        if prompt:
            handle_userinput(prompt)

        with st.spinner("processing"):
            #get the texts from the pdf
            raw_data = extract_text_from_pdf(pdf_path)
            #converting the texts into chunks of texts
            text_chunks = get_text_chunks(raw_data)
            #Creating a vectorstore
            vectorstore = get_vectorstore(text_chunks)
            #create conversation chain
            st.session_state.conversation = get_conversation_chain(vectorstore)
    

def extract_text_from_pdf(pdf_path):
    text = ""
    with open(pdf_path, "rb") as pdf_file:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        for page_num in range(len(pdf_reader.pages)):
            text += pdf_reader.pages[page_num].extract_text()
    return text

# Example usage:
pdf_path = r"C:\Users\Abhishek\Desktop\Herbalise\Datasets\Data_Communications_and_Networking_Behro.pdf"
extracted_text = extract_text_from_pdf(pdf_path)

def get_text_chunks(raw_data):
    text_splitter = CharacterTextSplitter(
        separator="\n",
        chunk_size=1000,
        chunk_overlap=200,
        lenght_function=len
    )

def get_vectorstore(text_chunks):
    #embeddings = OpenAIEmbeddings()
    embeddings = HuggingFaceInstructEmbeddings(model_name="hkunlp/instructor-xl")
    vectorstore = FAISS.from_text(texts=text_chunks, embedding= embeddings)
    return vectorstore

def get_conversation_chain(vectorstore):
    llm = ChatOpenAI
    memory = ConversationBufferMemory("chat_history",rerturn_memory=True)
    conversation_chain = ConversationalRetrievalChain.from_llm(
        llm= llm,
        retriever= vectorstore.as_retriever(),
        memory=memory    
    )
    return conversation_chain

def handle_userinput(prompt):
    response = st.session_state.conversation({'question': prompt})
    st.session_state.chat_history = response['chat_history']

    for i, message in enumerate(st.session_state.chat_history):
        if i % 2 == 0:
            st.write(user_template.replace(
                "{{MSG}}", message.content), unsafe_allow_html=True)
        else:
            st.write(bot_template.replace(
                "{{MSG}}", message.content), unsafe_allow_html=True)

if __name__ == "__main__":
    main()
