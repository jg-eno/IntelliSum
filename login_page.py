import streamlit as st
import base64
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import os
import pickle
import requests
import html2text
import re
from email.header import decode_header
from pymongo import MongoClient
import time

# Setting page configuration
st.set_page_config(page_title="IntelliSum - Email Summarizer", page_icon="✉️", layout="wide")

# MongoDB setup
client = MongoClient('mongodb://root:example@localhost:27017/')  # Update with your MongoDB URI

db_summary = client['Summary']
collection_content = db_summary['Content']

db_intellisum = client['intellisum_db']
users_collection = db_intellisum['users']


def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

def set_styles():
    st.markdown("""
        <style>
        .main {
            background: linear-gradient(to right, gray, black);
        }
        .title-text {
            font-family: 'Arial', sans-serif;
            text-align: center;
            margin-top: 20px;
            font-size: 4em;
            background: linear-gradient(to right, #FF6500, #FFAA00);
            -webkit-background-clip: text;
            color: transparent;
            font-weight: bold;
        }
        .subheader-text {
            text-align: center;
            font-size: 20px;
            color: #7f8c8d;
            margin-top: -10px;
            margin-bottom: 20px;
        }
        .email-box {
            background-color: #FFF8E1;
            padding: 1em;
            border-radius: 10px;
            box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.1);
            margin-bottom: 1em;
            color: #34495E;
        }
        .sender {
            font-weight: bold;
        }
        .content {
            margin-top: 0.5em;
        }
        .stButton > button {
            background-color: #263238;
            color: white;
            border-radius: 5px;
            font-size: 18px;
            padding: 10px;
        }
        .stTextInput > div > input {
            border: 2px solid #ccc;
            border-radius: 5px;
            padding: 10px;
        }
        .custom-form-container input {
            width: 100%;
            padding: 12px;
            border-radius: 5px;
            border: 1px solid #ccc;
            margin-bottom: 20px;
            font-size: 16px;
        }
        [data-testid="stForm"] {
            background: #202020;
        }
        [data-testid="stMain"] {
            background: black;
        }
        [data-testid="stHeader"] {
            background: black;
        }
        h3 {
            color: white;
        }
        </style>
    """, unsafe_allow_html=True)

class GmailReader:
    def __init__(self, credentials_path='credentials.json', user="default"):
        self.SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
        self.credentials_path = credentials_path
        self.user = user
        self.service = self.authenticate()

    def authenticate(self):
        creds = None
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(self.credentials_path, self.SCOPES)
                creds = flow.run_local_server(port=8080)
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)
        return build('gmail', 'v1', credentials=creds)

    def decode_email_subject(self, subject):
        if subject is None:
            return ""
        decoded_parts = []
        for part, encoding in decode_header(subject):
            if isinstance(part, bytes):
                decoded_parts.append(part.decode(encoding or 'utf-8', errors='replace'))
            else:
                decoded_parts.append(str(part))
        return ' '.join(decoded_parts)

    def get_email_body(self, message):
        if 'parts' in message['payload']:
            parts = message['payload']['parts']
            data = None
            for part in parts:
                if part['mimeType'] in ['text/plain', 'text/html']:
                    if 'data' in part['body']:
                        data = part['body']['data']
                    if data:
                        break
        else:
            if 'body' in message['payload'] and 'data' in message['payload']['body']:
                data = message['payload']['body']['data']
            else:
                return ""

        if not data:
            return ""

        text = base64.urlsafe_b64decode(data).decode('utf-8', errors='replace')

        if 'html' in message['payload'].get('mimeType', ''):
            h = html2text.HTML2Text()
            h.ignore_links = True
            h.ignore_images = True
            text = h.handle(text)

        text = re.sub(r'http\S+', '', text)  
        text = re.sub(r'\[.*?\]', '', text)
        text = re.sub(r'[^A-Za-z0-9\s]+', '', text)
        text = text.replace('\r', '').replace('\n', ' ').replace('\t', ' ').strip()
        return text[:1000]

    def get_header_value(self, headers, name):
        for header in headers:
            if header['name'].lower() == name.lower():
                return self.decode_email_subject(header['value'])
        return ""

    def get_recent_emails(self, count=10):
        email_data = []
        results = self.service.users().messages().list(userId='me', maxResults=count, labelIds=['INBOX']).execute()
        messages = results.get('messages', [])
        for message in messages:
            msg = self.service.users().messages().get(userId='me', id=message['id'], format='full').execute()
            headers = msg['payload']['headers']
            sender = self.get_header_value(headers, 'from')
            body = self.get_email_body(msg)
            if body:
                email_data.append({"sender": sender, "content": body})
        return email_data

def login(email, password):
    user = users_collection.find_one({"email": email, "password": password})
    return user is not None

def login_page():
    st.markdown("<div class='custom-form-container'>", unsafe_allow_html=True)
    st.write("### Login")
    with st.form(key='login_form'):
        email = st.text_input("Email", placeholder="Enter your email", key="email_input")
        password = st.text_input("Password", type="password", placeholder="Enter your password", key="password_input")
        submit_button = st.form_submit_button(label="Login")
    
    if submit_button:
        if login(email, password):
            st.session_state.logged_in = True
            st.session_state.user_email = email
            st.success("Login successful!")
            st.rerun()
        else:
            st.error("Invalid email or password. Please try again.")
    st.markdown("</div>", unsafe_allow_html=True)

def email_dashboard(user_email):
    st.markdown("<h1 class='title-text'>IntelliSum Dashboard</h1>", unsafe_allow_html=True)
    st.markdown("<h4 class='subheader-text'>Your Email Summaries</h4>", unsafe_allow_html=True)

    if st.button("Fetch Latest Emails"):
        st.info("Fetching the latest emails. Please wait...")
        gmail_reader = GmailReader(credentials_path='credentials.json', user=user_email)
        emails = gmail_reader.get_recent_emails(10)

        if emails:
            try:
                # Send the request for summarization
                response = requests.post("http://localhost:5000/summary", 
                                          json={"user": user_email, "emails": emails}, timeout=10)  # Added timeout

                if response.status_code == 200:
                    timeout = 15  # Adjust if necessary
                    start_time = time.time()
                    
                    while time.time() - start_time < timeout:
                        summaries = list(collection_content.find({"user": user_email}))
                        if summaries:
                            for summary in summaries:
                                st.markdown(
                                    f"""<div class='email-box'>
                                        <div class='sender'>{summary['sender']}</div>
                                        <div class='content'>{summary['context']}</div>
                                    </div>""", 
                                    unsafe_allow_html=True
                                )
                            break
                        time.sleep(1)
                    else:
                        st.error("Timed out waiting for summaries.")
                else:
                    st.error(f"Failed to summarize emails. Status code: {response.status_code}")
            except requests.exceptions.Timeout:
                st.error("Request to summarization service timed out. Please check the service.")
            except requests.exceptions.RequestException as e:
                st.error(f"Request failed: {e}")
        else:
            st.warning("No emails found.")

    if st.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.user_email = None
        st.rerun()

def main():
    set_styles()

    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        login_page()
    else:
        email_dashboard(st.session_state.user_email)

if __name__ == "__main__":
    main()
