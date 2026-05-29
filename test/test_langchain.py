from dotenv import load_dotenv

from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

llm = ChatGoogleGenerativeAI(
    model="gemini-flash-latest",
    temperature=0.7
)

template = "{topic}에 대해 배울 수 있는 좋은 책 3권을 추천해줘."
prompt_template = PromptTemplate.from_template(template)

chain = prompt_template | llm | StrOutputParser()

response = chain.invoke({"topic": "인공지능"})
print(response)