from anthropic import Anthropic
from dotenv import load_dotenv
import os

load_dotenv()
claude_client = Anthropic(api_key=os.getenv("CLAUDE_API_KEY")) 