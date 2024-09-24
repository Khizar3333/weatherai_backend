from langchain.agents import AgentExecutor, AgentType, initialize_agent
from langchain_google_genai import GoogleGenerativeAI
from langchain_core.tools import tool
import os
import requests
from dotenv import load_dotenv

load_dotenv()
apikey=os.getenv("GEMINI_API_KEY")
llm=GoogleGenerativeAI(model="gemini-1.5-flash", api_key=apikey)

@tool
def add_two_numbers(input_data:str) -> str:
    """addition of two numbers"""
   
    try:
        numbers=input_data.split(",")
    except Exception as e:
        return "Error: "+str(e)
    num1,num2=int(numbers[0]),int(numbers[1])
    result=num1+num2
    return f"the sum of {num1} and {num2} is {result}"
 
 
 
 
 # tools to get live weather of a city

def get_lat_lon(city: str) -> tuple:
    """Get the latitude and longitude of a city."""
    API_key = "8f7419767519cc63cbb44e192b8cce60"  # Replace with your OpenWeatherMap API key
    url = f"http://api.openweathermap.org/geo/1.0/direct?q={city}&limit=1&appid={API_key}"

    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        lat = data[0]['lat']
        lon = data[0]['lon']
        
        return lat, lon
    
    except Exception as e:
        return None, None  # Return None if there's an error


@tool
def get_weather(city: str) -> str:
    """Get the current weather of a city by first finding its latitude and longitude."""
    lat, lon = get_lat_lon(city)  # Call the get_lat_lon tool

    if lat is None or lon is None:
        return "Could not retrieve latitude and longitude."

    API_key = "8f7419767519cc63cbb44e192b8cce60"  # Replace with your OpenWeatherMap API key
    weather_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_key}&units=metric"

    try:
        weather_response = requests.get(weather_url)
        weather_response.raise_for_status()
        weather_data = weather_response.json()
        
        weather_description = weather_data['weather'][0]['description']
        temperature = weather_data['main']['temp']
        
        return f"The current weather in {city} is {weather_description} with a temperature of {temperature}°C."
    
    except Exception as e:
        return f"Error: {str(e)}"

# @tool
# def get_weather(city:str) -> str:
#     """Get the current weather of a city ."""
    
#     API_key = "8f7419767519cc63cbb44e192b8cce60"  # Replace with your OpenWeatherMap API key
#     # base_url = f"""https://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_key}&units=metric"""
#     url=f"""http://api.openweathermap.org/geo/1.0/direct?q={city}&limit=5&appid={API_key}&units=metric"""
    
#     # Construct the complete API URL
#     # url = f"{base_url}?&appid={API_key}&units=metric"  # Using metric for Celsius

#     try:
#         response = requests.get(url)
#         response.raise_for_status()  # Raise an error for bad responses
#         data = response.json()
        
       

#         # extract relevent information according to the url
#         lat=data[0]['lat']
#         lon=data[0]['lon']

#         final_url=f"""https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_key}&units=metric"""
#         response=requests.get(final_url)
#         data=response.json()
#         weather_description=data['weather'][0]['description']
#         temperature=data['main']['temp']
#         coordinates=data['coord']


#         return f"The current weather in {city} is {weather_description} with a temperature of {temperature}°C and coordinates {coordinates}."
#         # return f"the weather is {weather_description} with a temperature of {temperature}°C."
    
#     except Exception as e:
#         return f"Error: {str(e)}"
    

    

agent=initialize_agent(
    tools=[get_weather],
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,
    max_iterations=2
)

agent.invoke("what is the weather in lahore")

