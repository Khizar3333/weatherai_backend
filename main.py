# main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
from langchain.agents import initialize_agent, AgentType
from langchain_core.tools import tool
import uvicorn
from langchain_google_genai import GoogleGenerativeAI
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
import os
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Allow your Next.js frontend
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)
load_dotenv()
API_KEY = "8f7419767519cc63cbb44e192b8cce60"  # Replace with your OpenWeatherMap API key
class CityRequest(BaseModel):
    city: str

# Define your tools (assuming get_weather is already defined)
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

# Initialize the agent
  # Initialize your language model here

apikey=os.getenv("GEMINI_API_KEY")
llm=GoogleGenerativeAI(model="gemini-1.5-flash", api_key=apikey)
agent = initialize_agent(
    tools=[get_weather],
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,
    max_iterations=2
)




@app.post("/get_weather")
async def get_weather_info(request: CityRequest):
    """Endpoint to get weather information for a city using the agent."""
    city = request.city
    if "weather" not in city.lower():  # Check if the request is about weather
        return {"response": "I can only provide information related to weather."}
    try:
        # Use the agent to get the weather information
        response = agent.invoke(f"What is the weather in {city}?")
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))