"""
Base Agent Class
Provides common functionality for all calendar management agents
"""

import os
import json
from typing import Dict, Any, List, Optional
from anthropic import Anthropic
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class BaseAgent:
    """Base class for all calendar management agents"""
    
    def __init__(self, name: str, description: str):
        """
        Initialize the base agent
        
        Args:
            name: Name of the agent
            description: Description of what this agent does
        """
        self.name = name
        self.description = description
        self.api_key = os.getenv('CLAUDE_API_KEY')
        
        if not self.api_key:
            raise ValueError("CLAUDE_API_KEY not found in environment variables")
        
        self.client = Anthropic(api_key=self.api_key)
        self.conversation_history: List[Dict[str, str]] = []
    
    def get_system_prompt(self) -> str:
        """Get the system prompt for this agent - to be overridden by subclasses"""
        return f"""You are {self.name}, a specialized AI agent for calendar management. 
{self.description}

You should be helpful, professional, and focused on your specific area of expertise.
Always provide clear, actionable responses."""
    
    def chat(self, message: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Send a message to Claude and get response
        
        Args:
            message: The user message
            context: Additional context data for the agent
            
        Returns:
            Claude's response as a string
        """
        # Build the full prompt with context
        full_prompt = self._build_prompt(message, context)
        
        try:
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1000,
                messages=[
                    {
                        "role": "user",
                        "content": full_prompt
                    }
                ]
            )
            
            response_text = response.content[0].text
            
            # Store conversation history
            self.conversation_history.append({
                "role": "user",
                "content": message,
                "context": context
            })
            self.conversation_history.append({
                "role": "assistant", 
                "content": response_text
            })
            
            return response_text
            
        except Exception as e:
            return f"Error communicating with Claude: {str(e)}"
    
    def _build_prompt(self, message: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Build the full prompt including system prompt and context
        
        Args:
            message: User message
            context: Additional context
            
        Returns:
            Complete prompt string
        """
        system_prompt = self.get_system_prompt()
        
        prompt_parts = [system_prompt]
        
        if context:
            context_str = json.dumps(context, indent=2)
            prompt_parts.append(f"\nContext:\n{context_str}")
        
        prompt_parts.append(f"\nUser Message: {message}")
        
        return "\n".join(prompt_parts)
    
    def get_agent_info(self) -> Dict[str, str]:
        """Get information about this agent"""
        return {
            "name": self.name,
            "description": self.description,
            "conversation_count": len(self.conversation_history) // 2
        }
    
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = [] 