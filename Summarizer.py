from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.pydantic_v1 import BaseModel,Field
from langchain_core.output_parsers import JsonOutputParser
from pymongo import MongoClient
import json
from flask import Flask, request

class JsonCreater(BaseModel):
    sender: str = Field(description="Sender of the mail")
    content: str = Field(description="Content of the mail")

client = MongoClient('mongodb://127.0.0.1:27017/')
db = client['Summary']
collection = db['Content']


llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro",google_api_key="AIzaSyCwuqAWSAUgADtijYmJqPjtUZa6_yWkK4w")
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
@app.route("/summary",methods=['POST'])
def summary():
    content = request.json.get('content')
    if request.method == 'POST':
        try:
            msg = chain.invoke({"content":content})
            collection.insert_one(msg)
            return(f"Data loaded to the server : {msg}")

        except json.JSONDecodeError as e:
            return(f"Error parsing JSON : {e}")
    
    else:
        return "Not in the specific request format"
        


if __name__ == "__main__":
    app.run(debug=True)