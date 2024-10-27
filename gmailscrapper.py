from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import os.path
import pickle
import base64
import requests
from email.header import decode_header
import html2text
import re

class GmailReader:
    def __init__(self, credentials_path='credentials.json',user="default"):
        self.SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
        self.credentials_path = credentials_path
        self.user = user
        self.service = self.authenticate()

    def authenticate(self):
        """Handles Gmail API authentication"""
        creds = None
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, self.SCOPES)
                creds = flow.run_local_server(port=8080)
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)

        return build('gmail', 'v1', credentials=creds)

    def decode_email_subject(self, subject):
        """Properly decodes email subject with various encodings"""
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
        """Extracts and processes email body: removes images, links, and truncates content."""
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
        text = text.replace('\r', '')
        text = text.replace('\n', ' ')
        text = text.replace('\t', ' ')
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()

        max_length = 1000
        text = text[:max_length] if len(text) > max_length else text

        return text

    def get_header_value(self, headers, name):
        """Gets value of specific header from email headers"""
        for header in headers:
            if header['name'].lower() == name.lower():
                return self.decode_email_subject(header['value'])
        return ""

    def get_recent_emails(self, count=10):
        """Fetches the most recent emails and sends the body content to a local API in one batch."""
        try:
            email_data = []
            next_page_token = None

            while len(email_data) < count:
                results = self.service.users().messages().list(
                    userId='me',
                    maxResults=10,  
                    labelIds=['INBOX'],
                    pageToken=next_page_token
                ).execute()

                messages = results.get('messages', [])
                next_page_token = results.get('nextPageToken')  
                if not messages:
                    print("No more messages found.")
                    break

                for message in messages:
                    msg = self.service.users().messages().get(
                        userId='me', id=message['id'], format='full'
                    ).execute()

                    headers = msg['payload']['headers']
                    sender = self.get_header_value(headers, 'from')
                    body = self.get_email_body(msg)

                    # Only include emails with non-empty body content
                    if body.strip():
                        email_data.append({
                            "sender": sender,
                            "content": body
                        })
                        print(f"Retrieved email from: {sender}")

                    if len(email_data) >= count:
                        break 

                if not next_page_token:
                    print("Reached the end of available messages.")
                    break 
       
            if len(email_data) < count:
                print(f"Only found {len(email_data)} valid emails. Attempted to fetch {count}.")

            if email_data:
                data = {
                    "user": self.user,
                    "emails": email_data
                }
                try:
                    response = requests.post('http://localhost:5000/summary', json=data)
                    if response.status_code == 200:
                        print("Batch of summaries sent successfully!")
                    else:
                        print(f"Failed to send summaries. Status code: {response.status_code}")
                except requests.exceptions.RequestException as e:
                    print(f"Request failed: {e}")

        except Exception as error:
            print(f'An error occurred: {error}')

def main():
    try:
        user = "vijay"
        gmail_reader = GmailReader('credentials.json',user)
        gmail_reader.get_recent_emails(10)

    except Exception as e:
        print(f"Error: {str(e)}")
        print("\nPlease make sure:")
        print("1. credentials.json is in the current directory")
        print("2. Gmail API is enabled in Google Cloud Console")
        print("3. You have authorized the application")

if __name__ == '__main__':
    main()
