from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
from langchain.agents import  create_tool_calling_agent, AgentExecutor
from langchain_core.tools import tool
import uvicorn
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from langchain_community.document_loaders import WebBaseLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain.tools.retriever import create_retriever_tool
import os
from langchain import hub
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from mangum import Mangum

app = FastAPI()
handler = Mangum(app)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)

load_dotenv()
API_KEY = os.getenv("OPEN_WEATHER_API_KEY")



class QueryRequest(BaseModel):
    query: str
      
apikey = os.getenv("GOOGLE_API_KEY")
llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=apikey)
# Define your tools
@tool
def get_lat_lon(city: str) -> tuple:
    """Get the latitude and longitude of a city."""
    url = f"http://api.openweathermap.org/geo/1.0/direct?q={city}&limit=1&appid={API_KEY}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        lat = data[0]['lat']
        lon = data[0]['lon']
        return lat, lon
    except Exception as e:
        return None, None

@tool
def get_weather(city: str) -> str:
    """Get the current weather of a city by first finding its latitude and longitude."""
    lat, lon = get_lat_lon(city)
    if lat is None or lon is None:
        return "Could not retrieve latitude and longitude."

    weather_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY}&units=metric"
    try:
        weather_response = requests.get(weather_url)
        weather_response.raise_for_status()
        weather_data = weather_response.json()
        weather_description = weather_data['weather'][0]['description']
        temperature = weather_data['main']['temp']
        return f"The current weather in {city} is {weather_description} with a temperature of {temperature}°C."
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))




loader = WebBaseLoader("https://portfolio2-lime-alpha.vercel.app/")
docs = loader.load()
documents = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200).split_documents(docs)
vectorstore = FAISS.from_documents(documents, embedding=GoogleGenerativeAIEmbeddings(model="models/embedding-001", apikey=os.getenv("GOOGLE_API_KEY")))
retriever = vectorstore.as_retriever()

# Create the retriever tool without using @tool directive
retriever_tool = create_retriever_tool(retriever,
                                        "Khizar_Ahmad",
                                        "Search for information about Khizar Ahmad. For any question about Khizar Ahmad you must use this tool"
                                    )



tools=[get_weather, retriever_tool]
prompt=hub.pull("hwchase17/openai-functions-agent")
agent=create_tool_calling_agent(llm,tools,prompt)

agent_executor=AgentExecutor.from_agent_and_tools(agent,tools,verbose=True)
message_history=ChatMessageHistory()

agent_with_chat_history = RunnableWithMessageHistory(
    agent_executor,
    # This is needed because in most real world scenarios, a session id is needed
    # It isn't really used here because we are using a simple in memory ChatMessageHistory
    lambda session_id: message_history,
    input_messages_key="input",
    history_messages_key="chat_history",
)


@app.post("/query")  # New endpoint for user queries
async def answer_query(request: QueryRequest):
    """Endpoint to answer user queries using the agent executor."""
    try:
        # Wrap the input in a dictionary
        response = agent_with_chat_history.invoke(
            {"input": request.query},  # Wrap the query in a dictionary
            config={"configurable": {"session_id": "test123"}}  # Add your session ID here
        )
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


