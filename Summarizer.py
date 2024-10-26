import uuid
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_community.document_loaders.parsers.pdf import PDFMinerParser
from langchain_community.document_loaders.parsers.generic import MimeTypeBasedParser
from langchain_community.document_loaders.parsers.txt import TextParser
from langchain_community.document_loaders import Blob
from pydantic import BaseModel, Field
from pymongo import MongoClient
import json
from flask import Flask, request, jsonify
import magic

HANDLERS = {
    "application/pdf": PDFMinerParser(),
    "text/plain": TextParser(),
}

MIMETYPE_BASED_PARSER = MimeTypeBasedParser(
    handlers=HANDLERS,
    fallback_parser=None,
)


class JsonCreater(BaseModel):
    sender: str = Field(description="Sender of the mail")
    content: str = Field(description="Content of the mail")


client = MongoClient('mongodb://127.0.0.1:27017/')
db = client['Summary']
collection = db['Content']

llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro", google_api_key="")
template = """ 
You are a personal assisstant who summarizes the mail contents and provides a summary based on the given content.
Respond with a JSON object using the following instructions : 
{{
    "sender":"<Sender of the email>"
    "context":"<1 line describing the content of the email>"
}}

content : {content}
"""

prompt = ChatPromptTemplate.from_template(template)

parser = JsonOutputParser(pydantic_object=JsonCreater)

chain = prompt | llm | parser

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 1e10
app.config['UPLOAD_EXTENSIONS'] = ['.png']

# removed request.method == 'post' since it's redundant with route definition
@app.route("/summary", methods=['POST'])
def summary():
    content = request.form.get('content')
    for filename, file in request.files.items():
        data = file.read()
        mime = magic.Magic(mime=True)
        mime_type = mime.from_buffer(data)
        blob = Blob.from_data(data=data, mime_type=mime_type)
        if mime_type in HANDLERS:
            parser = HANDLERS[mime_type]
            attachment_content = parser.parse(blob=blob)[0]
            content += f"Attachment: {file.filename}, content: {attachment_content.page_content}"
        # elif 'image' in mime_type:
        #     id = uuid.uuid4()
        #     file.save(f'/tmp/{id}')
        #     loader = UnstructuredImageLoader(f'/tmp/{id}')
        #     data = loader.load()
        #     return data
    try:
        msg = chain.invoke({"content": content})
        collection.insert_one(msg)
        return jsonify({'message': 'ok', 'summary': msg}), 200

    except json.JSONDecodeError as e:
        return jsonify({'message': "Malformed JSON"}), 400


if __name__ == "__main__":
    app.run(debug=True)
