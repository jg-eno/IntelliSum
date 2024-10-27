# import streamlit as st
# import base64


# # Setting page configuration
# st.set_page_config(page_title="Gmail Summarization", layout="wide")

# def get_base64_of_bin_file(bin_file):
#     with open(bin_file, 'rb') as f:
#         data = f.read()
#     return base64.b64encode(data).decode()


# # Function to create a modern style for the page
# def set_styles():
#     img_base64 = get_base64_of_bin_file('./landingBackground.jpg')
#     st.markdown(f"""
#       <style>
#       .main {{
#         background:  linear-gradient(to right, gray , black);;
        
       
#       }}
#       .title {{
#         font-size: 4em;
#         background: linear-gradient(to right, blue, red);
#         -webkit-background-clip: text;
#         color: transparent;
#         font-weight: bold;
#         shadow: 2px 2px white;
#         display: flex;
#         justify-content: center;
#         font-weight: 600;
#         margin-bottom: 0.3em;
#       }}
#       .header {{
#         font-size: 1.2em;
#         color: #e74c3c;
#         font-weight: bold;
#         margin-bottom: 0.5em;
#       }}
#       .sender, .content {{
#         background-color: seashell;
#         padding: 1em;
#         border-radius: 10px;
#         box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.1);
#         margin-bottom: 1em;
#         width: auto;
#         height: auto;
#         color: #34495E;
#       }}
#       .header-container {{
#         display: flex;
#         justify-content: space-between;
#         align-items: center;
#         padding: 1em;
#         background-color:  #34495E;
#         box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.1);
#         border-radius: 10px;
#       }}

#       .header-title {{
#           font-size: 1.5em;
#           font-weight: bold;
#           color: tan;
#       }}

#       .nav-container {{
#           display: flex;
#           align-items: center;
#       }}

#       .nav-item {{
#           margin-right: 1em;
#       }}

#       .nav-link {{
#           text-decoration: none;
#           color: #34495E;
#           font-weight: bold;
#       }}

#       .nav-link:hover {{
#           color: #e74c3c;
#           fontsize: 1.2em;
#           font-weight: bold;
          
#       }}
#       .profile-picture {{
#           border-radius: 50%;
#           width: 45px;
#           height: 40px;
#       }}
#       .profile-picture:hover {{
#           cursor: pointer;
#       }}
    
#       </style>
#     """, unsafe_allow_html=True)

# # Applying styles
# set_styles()

# # Header with options and profile picture
# st.markdown("""
#  <div class="header-container">
#         <div class="header-title">Gmail Summarization</div>
#         <div class="nav-container">
#             <div class="nav-item">
#                 <a href="#" class="nav-link">Home</a>
#             </div>
#             <div class="nav-item">
#                 <a href="#" class="nav-link">Settings</a>
#             </div>
#             <div class="nav-item">
#                 <a href="#" class="nav-link">Logout</a>
#             </div>
#             <img src="https://www.shutterstock.com/shutterstock/photos/2195809163/display_1500/stock-vector-n-logo-letter-design-on-luxury-background-nn-logo-monogram-initials-letter-concept-n-nn-icon-2195809163.jpg" alt="Profile Picture" class="profile-picture">
#         </div>
#     </div>
# """, unsafe_allow_html=True)


# st.markdown(f"<div class='title'>Welcome, Niranjan!</div>", unsafe_allow_html=True)

# col1, col2 = st.columns(2)


# sender_data = ["Sender 1", "Sender 2", "Sender 3"]
# content_data = ["Content 1 - summary of email 1", "Content 2 - summary of email 2", "Content 3 - summary of email 3"]

# # Displaying sender and content in columns
# col1.markdown("<div class='header'>Sender</div>", unsafe_allow_html=True)
# col2.markdown("<div class='header'>Content</div>", unsafe_allow_html=True)

# # Display data in respective columns
# for sender, content in zip(sender_data, content_data):
#     col1.markdown(f"<div class='sender'>{sender}</div>", unsafe_allow_html=True)
#     col2.markdown(f"<div class='content'>{content}</div>", unsafe_allow_html=True)
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

# Setting page configuration
st.set_page_config(page_title="Gmail Summarization", layout="wide")

def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

# Function to create a modern style for the page
def set_styles():
    img_base64 = get_base64_of_bin_file('./landingBackground.jpg')
    st.markdown(f"""
      <style>
      .main {{
        background:  linear-gradient(to right, gray , black);
      }}
      .title {{
        font-size: 4em;
        background: linear-gradient(to right, blue, red);
        -webkit-background-clip: text;
        color: transparent;
        font-weight: bold;
        shadow: 2px 2px white;
        display: flex;
        justify-content: center;
        font-weight: 600;
        margin-bottom: 0.3em;
      }}
      .header {{
        font-size: 1.2em;
        color: #e74c3c;
        font-weight: bold;
        margin-bottom: 0.5em;
      }}
      .sender, .content {{
        background-color: seashell;
        padding: 1em;
        border-radius: 10px;
        box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.1);
        margin-bottom: 1em;
        width: auto;
        height: auto;
        color: #34495E;
      }}
      .header-container {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 1em;
        background-color:  #34495E;
        box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.1);
        border-radius: 10px;
      }}
      .header-title {{
          font-size: 1.5em;
          font-weight: bold;
          color: tan;
      }}
      .nav-container {{
          display: flex;
          align-items: center;
      }}
      .nav-item {{
          margin-right: 1em;
      }}
      .nav-link {{
          text-decoration: none;
          color: #34495E;
          font-weight: bold;
      }}
      .nav-link:hover {{
          color: #e74c3c;
          fontsize: 1.2em;
          font-weight: bold;
      }}
      .profile-picture {{
          border-radius: 50%;
          width: 45px;
          height: 40px;
      }}
      .profile-picture:hover {{
          cursor: pointer;
      }}
      </style>
    """, unsafe_allow_html=True)

# Applying styles
set_styles()

# Header with options and profile picture
st.markdown(""" 
 <div class="header-container">
        <div class="header-title">Gmail Summarization</div>
        <div class="nav-container">
            <div class="nav-item">
                <a href="#" class="nav-link">Home</a>
            </div>
            <div class="nav-item">
                <a href="#" class="nav-link">Settings</a>
            </div>
            <div class="nav-item">
                <a href="#" class="nav-link">Logout</a>
            </div>
            <img src="https://www.shutterstock.com/shutterstock/photos/2195809163/display_1500/stock-vector-n-logo-letter-design-on-luxury-background-nn-logo-monogram-initials-letter-concept-n-nn-icon-2195809163.jpg" alt="Profile Picture" class="profile-picture">
        </div>
    </div>
""", unsafe_allow_html=True)

st.markdown(f"<div class='title'>Welcome, Niranjan!</div>", unsafe_allow_html=True)

# GmailReader Class
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

        text = base64.urlsafe_b64decode(data).decode('utf-8', errors='replace')
        if 'html' in message['payload'].get('mimeType', ''):
            h = html2text.HTML2Text()
            h.ignore_links = True
            h.ignore_images = True
            text = h.handle(text)

        text = re.sub(r'http\S+', '', text)
        text = re.sub(r'\[.*?\]', '', text)
        text = re.sub(r'[^A-Za-z0-9\s]+', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text[:1000] if len(text) > 1000 else text

    def get_recent_emails(self, count=10):
        email_data = []
        results = self.service.users().messages().list(userId='me', maxResults=count, labelIds=['INBOX']).execute()
        messages = results.get('messages', [])
        for message in messages:
            msg = self.service.users().messages().get(userId='me', id=message['id'], format='full').execute()
            sender = next(header['value'] for header in msg['payload']['headers'] if header['name'].lower() == 'from')
            body = self.get_email_body(msg)
            email_data.append({"sender": sender, "content": body})
        return email_data

# Button to fetch emails
if st.button("Fetch Latest Emails"):
    st.info("Fetching the latest emails. Please wait...")
    gmail_reader = GmailReader(credentials_path='credentials.json', user="Niranjan")
    emails = gmail_reader.get_recent_emails(10)

    if emails:
        col1, col2 = st.columns(2)
        col1.markdown("<div class='header'>Sender</div>", unsafe_allow_html=True)
        col2.markdown("<div class='header'>Content</div>", unsafe_allow_html=True)
        for email in emails:
            col1.markdown(f"<div class='sender'>{email['sender']}</div>", unsafe_allow_html=True)
            col2.markdown(f"<div class='content'>{email['content']}</div>", unsafe_allow_html=True)

        # Summary API Integration
        try:
            response = requests.post("http://localhost:5000/summary", json={"user": "Niranjan", "emails": emails})
            if response.status_code == 200:
                st.success("Emails summarized successfully!")
            else:
                st.error(f"Failed to summarize emails. Status code: {response.status_code}")
        except requests.exceptions.RequestException as e:
            st.error(f"Request failed: {e}")
    else:
        st.warning("No emails found.")
