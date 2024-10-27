from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.output_parsers import JsonOutputParser
from pymongo import MongoClient
from flask import Flask, request
import re  # Import regex for parsing sender name
import json

class JsonCreater(BaseModel):
    sender: str = Field(description="Sender of the email")
    context: str = Field(description="Context of the email content")

# MongoDB setup
print("Connecting to MongoDB...")
client = MongoClient('mongodb://root:example@localhost:27017/')
db = client['Summary']
collection = db['Content']
print("Connected to MongoDB.")

# Language model setup
print("Setting up the language model...")
llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key="AIzaSyALFGatMOXVieZL2htkKgGxrFoK15EHrgI")
template = """ 
You are a personal assistant who summarizes the mail contents and provides a summary based on the given content.
sender should only contain text.
Respond with a JSON object using the following instructions: 
{{
    "sender":"<Sender of the email>",
    "context":"<1 line describing the content of the email>"
}}

content: {content}
"""
prompt = ChatPromptTemplate.from_template(template)
parser = JsonOutputParser(pydantic_object=JsonCreater)
chain = prompt | llm | parser
print("Language model setup complete.")

# Flask app setup
app = Flask(__name__)

# Helper function to extract plain text name from "sender" field
def extract_sender_name(sender_text):
    # Regex to match name before any '<' or other non-name characters
    match = re.match(r"^[^<]+", sender_text)
    return match.group(0).strip() if match else sender_text.strip()

@app.route("/summary", methods=['POST'])
def summary():
    print("Received request at /summary endpoint.")

    user = request.json.get('user')
    emails = request.json.get('emails')  # Expecting a list of dictionaries with sender and content keys

    if not isinstance(emails, list):
        print("Invalid input: 'emails' should be a list.")
        return "Please provide 'emails' as a list."

    if request.method == 'POST':
        try:
            summaries = []
            print("Processing emails...")

            # Summarize each email and store the result
            for index, email in enumerate(emails):
                content = email.get('content')
                raw_sender = email.get('sender')
                sender_name = extract_sender_name(raw_sender)  # Extract plain text name
                print(f"Summarizing email {index + 1} from {sender_name}...")

                msg = chain.invoke({"content": content}, timeout=10)
                summaries.append({"user": user, "sender": sender_name, "context": msg["context"]})
                print(f"Summary for email {index + 1}: {msg['context']}")

            print(f"Deleting previous summaries for this user from MongoDB...")
            previous_entries = collection.find({"user": user}).sort("_id", -1).limit(len(summaries))
            previous_ids = [entry['_id'] for entry in previous_entries]
            collection.delete_many({"_id": {"$in": previous_ids}})
            print("Deleted previous summaries.")

            # Insert the new summaries into the database
            print("Inserting new summaries into MongoDB...")
            collection.insert_many(summaries)
            print("Summaries successfully loaded to the server.")

            return f"Summaries loaded to the server: {summaries}"

        except json.JSONDecodeError as e:
            print(f"Error parsing JSON: {e}")
            return f"Error parsing JSON: {e}"

    else:
        print("Invalid request format.")
        return "Not in the specific request format"


if __name__ == "__main__":
    print("Starting Flask server...")
    app.run()
