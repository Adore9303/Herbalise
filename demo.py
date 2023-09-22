#importing all the neccesary libraries and models for the app
import streamlit as st
import base64
import plotly.express as px
import streamlit_authenticator as stauth
import sqlite3
import yaml
import os 
from PyPDF2 import PdfReader
from dotenv import load_dotenv
from yaml.loader import SafeLoader
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

#
df = px.data.iris()
@st.cache_data
def get_img_as_base64(file):
    with open(file, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

img = get_img_as_base64(r"C:\Users\Abhishek\OneDrive\Desktop\pexels-nataliya-vaitkevich-7615574.jpg")

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


def application():
    prompt = st.text_input("Enter the prompt for the medicine formulation")
    if st.button('submit'):
        
        with st.spinner("processing"):
            folder_path = r'C:\Users\Abhishek\Desktop\Herbalise\Datassets'
            if os.path.isdir(folder_path):
                # List all PDF files in the directory
                pdf_files = [f for f in os.listdir(folder_path) if f.endswith('.pdf')]
                #get pdf text
                raw_data = get_pdf_text([pdf_files])
                st.write(raw_data)

def get_pdf_text(pdf_files):
    text=""
    for pdf in pdf_files:
        pdf_reader = PdfReader(pdf)
        for page in pdf_reader.pages:
            text += page.extract_text()
    return text    
    

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
                application()
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
    
            
if __name__ == "__main__":
    main()
