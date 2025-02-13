import os
from dotenv import load_dotenv

load_dotenv()

from tavily import TavilyClient

tavily_ai_api_key = os.environ.get("TAVILY_API_KEY")

client = TavilyClient(api_key=tavily_ai_api_key)
result = client.search("What is in Nvidia's new Blackwell GPU?", include_answer=True)

print(result["answer"])