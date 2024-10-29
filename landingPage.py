import streamlit as st
import base64
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import os
import pickle
import requests
import html2text
import re
from email.header import decode_header
from pymongo import MongoClient
import time  # Import time for the waiting mechanism

# Setting page configuration
def show_page(user_email):
    # Database connection setup for MongoDB
    client = MongoClient('mongodb://root:example@localhost:27017/')
    db = client['Summary']
    collection = db['Content']

    def get_base64_of_bin_file(bin_file):
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()

    def set_styles():
        st.markdown(f"""
          <style>
          .main {{
            background: linear-gradient(to right, gray, black);
          }}
          .title {{
            font-size: 4em;
            background: linear-gradient(to right, #FF6500, #FFAA00);
            -webkit-background-clip: text;
            color: transparent;
            font-weight: bold;
            display: flex;
            justify-content: center;
            margin-bottom: 0.3em;
          }}
          .email-box {{
            background-color: #FFF8E1;
            padding: 1em;
            border-radius: 10px;
            box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.1);
            margin-bottom: 1em;
            color: #34495E;
          }}
          .sender {{
            font-weight: bold;
          }}
          .content {{
            margin-top: 0.5em;
          }}
          </style>
        """, unsafe_allow_html=True)

    # Applying styles
    set_styles()

    st.markdown("<div class='title'>Welcome to Gmail Summarization!</div>", unsafe_allow_html=True)

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

    # Button to fetch emails
    if st.button("Fetch Latest Emails"):
        st.info("Fetching the latest emails. Please wait...")
        gmail_reader = GmailReader(credentials_path='credentials.json', user=user_email)

        try:
            emails = gmail_reader.get_recent_emails(10)  # Fetch emails
            if emails:
                st.success(f"Fetched {len(emails)} emails!")
                for email in emails:
                    st.markdown(f"<div class='email-box'><div class='sender'>{email['sender']}</div><div class='content'>{email['content']}</div></div>", unsafe_allow_html=True)

                # Send emails to summarization service
                response = requests.post("http://localhost:5000/summary", json={"user": user_email, "emails": emails})
                if response.status_code == 200:
                    st.success("Emails sent for summarization. Waiting for summaries...")
                    summaries = response.json().get("summaries", [])
                    for summary in summaries:
                        st.write(summary)
                else:
                    st.error(f"Failed to summarize emails. Status code: {response.status_code}")
            else:
                st.warning("No emails found.")
        except Exception as e:
            st.error(f"An error occurred: {e}")

    st.markdown("### Logout")
    if st.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.user_email = None
        st.session_state.page = None
        st.success("You have logged out successfully.")
