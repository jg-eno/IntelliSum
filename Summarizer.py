from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.output_parsers import JsonOutputParser
from langchain_community.document_loaders.parsers.pdf import PDFMinerParser
from langchain_community.document_loaders.parsers.generic import MimeTypeBasedParser
from langchain_community.document_loaders.parsers.txt import TextParser
from langchain_community.document_loaders import Blob
import magic
from langchain_core.messages import HumanMessage
from pymongo import MongoClient
from flask import Flask, request
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

HANDLERS = {
    "application/pdf": PDFMinerParser(),
    "text/plain": TextParser(),
}

# Language model setup
print("Setting up the language model...")
llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key="")
template = """ 
You are a personal assistant who summarizes the mail contents and provides a summary based on the given content.
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
app.config['MAX_CONTENT_LENGTH'] = 1e10
app.config['UPLOAD_EXTENSIONS'] = []

@app.route("/summary", methods=['POST'])
def summary():
    print("Received request at /summary endpoint.")

    user = request.json.get('user')
    emails = request.json.get('emails')  # Expecting a list of dictionaries with sender and content keys
    json = json.loads(request.form.get('json'))

    
    if not isinstance(emails, list):
        print("Invalid input: 'emails' should be a list.")
        return jsonify({"message": "Expected list of emails"}), 400

    try:
        summaries = []
        print("Processing emails...")

        # Summarize each email and store the result
        for index, email in enumerate(emails):
            content = email.get('content')
            sender = email.get('sender')
            files = email.get('attachments')
            images = []
            for filename in files:
                file = request.files.get(filename, 0)
                if file == 0: 
                    return jsonify({'message': 'Filename mismatch in json and form'}), 400
                data = file.read()
                mime = magic.Magic(mime=True)
                mime_type = mime.from_buffer(data)
                blob = Blob.from_data(data=data, mime_type=mime_type)
                if mime_type in HANDLERS:
                    parser = HANDLERS[mime_type]
                    attachment_content = parser.parse(blob=blob)[0]
                    content += f"Attachment: {file.filename}, content: {attachment_content.page_content}"
                elif 'image' in mime_type:
                    images.append(base64.b64encode(file.read()).decode("utf-8"))

            message = HumanMessage(
                content=[
                    {"type": "text", "text": content},
                    *[{
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{image_data}"},
                    } for image_data in images
                    ]
                ]
            )
            print(f"Summarizing email {index + 1} from {sender}...")
            msg = chain.invoke(message, timeout=5)
            summaries.append({"user": user, "sender": sender, "context": msg["context"]})
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


if __name__ == "__main__":
    print("Starting Flask server...")
    app.run()
