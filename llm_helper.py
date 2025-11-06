"""
LLM Helper Module
Handles interactions with OpenAI and Google Gemini APIs

This module provides:
- Universal LLM interface for multiple providers
- OpenAI GPT integration (GPT-4, GPT-3.5-turbo)
- Google Gemini integration (Gemini Pro, Gemini Flash)
- Error handling and retry logic
- Token management and cost tracking
- Fallback mechanisms
"""

import os
import time
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Determine which provider to use
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai").lower()

# Configuration
DEFAULT_MAX_TOKENS = 1000
DEFAULT_TEMPERATURE = 0.7
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds

class LLMError(Exception):
    """Custom exception for LLM-related errors"""
    pass

class RateLimitError(LLMError):
    """Exception for rate limit errors"""
    pass

class LLMHelper:
    """
    Helper class for LLM operations with state tracking
    """
    def __init__(self, provider: str = None):
        self.provider = provider or LLM_PROVIDER
        self.total_tokens_used = 0
        self.total_calls = 0
        self.total_cost = 0.0
        self.call_history = []
    
    def call(self, prompt: str, max_tokens: int = DEFAULT_MAX_TOKENS, 
             temperature: float = DEFAULT_TEMPERATURE, **kwargs) -> str:
        """
        Call the LLM with retry logic
        
        Args:
            prompt: The prompt to send
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature
            **kwargs: Additional provider-specific parameters
            
        Returns:
            str: The LLM response
        """
        for attempt in range(MAX_RETRIES):
            try:
                if self.provider == "openai":
                    response = self._call_openai(prompt, max_tokens, temperature, **kwargs)
                elif self.provider == "gemini":
                    response = self._call_gemini(prompt, max_tokens, temperature, **kwargs)
                else:
                    raise LLMError(f"Unsupported LLM provider: {self.provider}")
                
                # Track usage
                self.total_calls += 1
                self.call_history.append({
                    'provider': self.provider,
                    'prompt_length': len(prompt),
                    'response_length': len(response),
                    'timestamp': time.time()
                })
                
                return response
            
            except RateLimitError as e:
                if attempt < MAX_RETRIES - 1:
                    wait_time = RETRY_DELAY * (attempt + 1)
                    print(f"Rate limit hit. Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    raise LLMError(f"Rate limit exceeded after {MAX_RETRIES} attempts: {str(e)}")
            
            except Exception as e:
                if attempt < MAX_RETRIES - 1:
                    print(f"Attempt {attempt + 1} failed: {str(e)}. Retrying...")
                    time.sleep(RETRY_DELAY)
                else:
                    raise LLMError(f"LLM call failed after {MAX_RETRIES} attempts: {str(e)}")
    
    def _call_openai(self, prompt: str, max_tokens: int, temperature: float, **kwargs) -> str:
        """Internal method for OpenAI API calls"""
        return call_openai(prompt, max_tokens, temperature, **kwargs)
    
    def _call_gemini(self, prompt: str, max_tokens: int, temperature: float, **kwargs) -> str:
        """Internal method for Gemini API calls"""
        return call_gemini(prompt, max_tokens, temperature, **kwargs)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get usage statistics"""
        return {
            'provider': self.provider,
            'total_calls': self.total_calls,
            'total_tokens_used': self.total_tokens_used,
            'total_cost': self.total_cost,
            'call_history': self.call_history
        }

def call_llm(prompt: str, max_tokens: int = DEFAULT_MAX_TOKENS, 
             temperature: float = DEFAULT_TEMPERATURE, **kwargs) -> str:
    """
    Call the configured LLM provider (simple interface)
    
    Args:
        prompt: The prompt to send
        max_tokens: Maximum tokens in response
        temperature: Sampling temperature
        **kwargs: Additional parameters
    
    Returns:
        str: The LLM response
    
    Raises:
        LLMError: If the LLM call fails
    """
    if LLM_PROVIDER == "openai":
        return call_openai(prompt, max_tokens, temperature, **kwargs)
    elif LLM_PROVIDER == "gemini":
        return call_gemini(prompt, max_tokens, temperature, **kwargs)
    else:
        raise LLMError(f"Unsupported LLM provider: {LLM_PROVIDER}")

def call_openai(prompt: str, max_tokens: int = DEFAULT_MAX_TOKENS, 
                temperature: float = DEFAULT_TEMPERATURE, 
                model: str = None, **kwargs) -> str:
    """
    Call OpenAI API with comprehensive error handling
    
    Args:
        prompt: The prompt to send
        max_tokens: Maximum tokens in response
        temperature: Sampling temperature
        model: Model to use (default: gpt-3.5-turbo)
        **kwargs: Additional OpenAI parameters
    
    Returns:
        str: The LLM response
    
    Raises:
        LLMError: If the API call fails
        RateLimitError: If rate limit is exceeded
    """
    try:
        from openai import OpenAI, RateLimitError as OpenAIRateLimitError
        
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise LLMError("OPENAI_API_KEY not found in environment variables. "
                          "Please set it in your .env file.")
        
        # Initialize client
        client = OpenAI(api_key=api_key)
        
        # Determine model
        if model is None:
            model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
        
        # Prepare messages
        messages = kwargs.get('messages', [
            {"role": "system", "content": "You are a helpful technical documentation assistant. "
                                         "Provide clear, concise, and accurate responses."},
            {"role": "user", "content": prompt}
        ])
        
        # Make API call
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=kwargs.get('top_p', 1.0),
            frequency_penalty=kwargs.get('frequency_penalty', 0.0),
            presence_penalty=kwargs.get('presence_penalty', 0.0)
        )
        
        # Extract response
        content = response.choices[0].message.content
        
        # Track token usage
        if hasattr(response, 'usage'):
            tokens_used = response.usage.total_tokens
            print(f"[OpenAI] Tokens used: {tokens_used}")
        
        return content
    
    except OpenAIRateLimitError as e:
        raise RateLimitError(f"OpenAI rate limit exceeded: {str(e)}")
    
    except ImportError:
        raise LLMError("OpenAI library not installed. Run: pip install openai")
    
    except Exception as e:
        error_msg = str(e)
        
        # Check for specific error types
        if "api_key" in error_msg.lower():
            raise LLMError("Invalid OpenAI API key. Please check your .env file.")
        elif "rate" in error_msg.lower() or "limit" in error_msg.lower():
            raise RateLimitError(f"OpenAI rate limit: {error_msg}")
        elif "timeout" in error_msg.lower():
            raise LLMError(f"OpenAI request timed out: {error_msg}")
        else:
            raise LLMError(f"OpenAI API error: {error_msg}")

def call_gemini(prompt: str, max_tokens: int = DEFAULT_MAX_TOKENS, 
                temperature: float = DEFAULT_TEMPERATURE,
                model: str = None, **kwargs) -> str:
    """
    Call Google Gemini API with comprehensive error handling
    
    Args:
        prompt: The prompt to send
        max_tokens: Maximum tokens in response
        temperature: Sampling temperature
        model: Model to use (default: gemini-1.5-flash)
        **kwargs: Additional Gemini parameters
    
    Returns:
        str: The LLM response
    
    Raises:
        LLMError: If the API call fails
        RateLimitError: If rate limit is exceeded
    """
    try:
        import google.generativeai as genai
        
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise LLMError("GEMINI_API_KEY not found in environment variables. "
                          "Please set it in your .env file.")
        
        # Configure API
        genai.configure(api_key=api_key)
        
        # Determine model
        if model is None:
            model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
        
        # Initialize model
        gemini_model = genai.GenerativeModel(model)
        
        # Configure generation
        generation_config = genai.types.GenerationConfig(
            max_output_tokens=max_tokens,
            temperature=temperature,
            top_p=kwargs.get('top_p', 0.95),
            top_k=kwargs.get('top_k', 40)
        )
        
        # Safety settings (optional)
        safety_settings = kwargs.get('safety_settings', [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            }
        ])
        
        # Make API call
        response = gemini_model.generate_content(
            prompt,
            generation_config=generation_config,
            safety_settings=safety_settings
        )
        
        # Extract text
        if hasattr(response, 'text'):
            return response.text
        elif hasattr(response, 'parts'):
            return ''.join(part.text for part in response.parts)
        else:
            raise LLMError("Unexpected Gemini response format")
    
    except ImportError:
        raise LLMError("Google Generative AI library not installed. "
                      "Run: pip install google-generativeai")
    
    except Exception as e:
        error_msg = str(e)
        
        # Check for specific error types
        if "api_key" in error_msg.lower() or "api key" in error_msg.lower():
            raise LLMError("Invalid Gemini API key. Please check your .env file.")
        elif "quota" in error_msg.lower() or "rate" in error_msg.lower():
            raise RateLimitError(f"Gemini rate limit: {error_msg}")
        elif "timeout" in error_msg.lower():
            raise LLMError(f"Gemini request timed out: {error_msg}")
        elif "safety" in error_msg.lower():
            raise LLMError(f"Content blocked by Gemini safety filters: {error_msg}")
        else:
            raise LLMError(f"Gemini API error: {error_msg}")

def summarize_code(code_snippet: str, language: str = "python", 
                   max_length: int = 500) -> str:
    """
    Summarize a code snippet using LLM
    
    Args:
        code_snippet: The code to summarize
        language: Programming language of the code
        max_length: Maximum length of the code snippet to process
        
    Returns:
        str: Code summary
    """
    # Truncate if too long
    if len(code_snippet) > max_length:
        code_snippet = code_snippet[:max_length] + "\n... [truncated]"
    
    prompt = f"""Analyze this {language} code and provide a concise summary (2-3 sentences) of what it does:
```{language}
{code_snippet}
```

Focus on:
1. The main purpose of this code
2. Key functionality it provides
3. Any notable patterns or techniques used

Provide ONLY the summary, no additional commentary."""

    try:
        return call_llm(prompt, max_tokens=200, temperature=0.5)
    except Exception as e:
        print(f"Error summarizing code: {e}")
        return "Unable to generate code summary."

def generate_docstring(function_name: str, code: str, 
                       parameters: List[str], language: str = "python") -> str:
    """
    Generate a docstring for a function using LLM
    
    Args:
        function_name: Name of the function
        code: Function code
        parameters: List of parameter names
        language: Programming language
        
    Returns:
        str: Generated docstring
    """
    param_list = ", ".join(parameters) if parameters else "none"
    
    # Truncate code if too long
    if len(code) > 800:
        code = code[:800] + "\n... [truncated]"
    
    prompt = f"""Generate a comprehensive docstring for this {language} function:

Function name: {function_name}
Parameters: {param_list}

Code:
```{language}
{code}
```

Generate a docstring that includes:
1. Brief description of what the function does
2. Args section describing each parameter
3. Returns section describing the return value
4. Any important notes or examples

Format the docstring according to {language} conventions (Google style for Python).
Return ONLY the docstring text, no code blocks or extra formatting."""

    try:
        return call_llm(prompt, max_tokens=400, temperature=0.6)
    except Exception as e:
        print(f"Error generating docstring: {e}")
        return f"Function to {function_name.replace('_', ' ')}."

def improve_documentation(existing_doc: str, code_context: str = "") -> str:
    """
    Improve existing documentation using LLM
    
    Args:
        existing_doc: Current documentation text
        code_context: Additional code context
        
    Returns:
        str: Improved documentation
    """
    prompt = f"""Improve this technical documentation to make it clearer and more comprehensive:

Current Documentation:
{existing_doc}

{f"Code Context:\n{code_context[:500]}" if code_context else ""}

Please:
1. Clarify any ambiguous statements
2. Add missing important details
3. Improve structure and readability
4. Fix any grammar or formatting issues
5. Keep the same general structure

Return the improved documentation in markdown format."""

    try:
        return call_llm(prompt, max_tokens=600, temperature=0.7)
    except Exception as e:
        print(f"Error improving documentation: {e}")
        return existing_doc

def explain_code_relationship(entity1: str, entity2: str, 
                              relationship_type: str) -> str:
    """
    Generate natural language explanation of code relationships
    
    Args:
        entity1: First entity name
        entity2: Second entity name
        relationship_type: Type of relationship (calls, inherits, etc.)
        
    Returns:
        str: Natural language explanation
    """
    prompt = f"""Explain the relationship between these two code entities in one clear sentence:

Entity 1: {entity1}
Entity 2: {entity2}
Relationship: {relationship_type}

Provide a concise, technical explanation suitable for documentation."""

    try:
        return call_llm(prompt, max_tokens=100, temperature=0.5)
    except Exception as e:
        print(f"Error explaining relationship: {e}")
        return f"{entity1} {relationship_type} {entity2}"

def generate_usage_example(function_name: str, parameters: List[Dict[str, str]], 
                          description: str) -> str:
    """
    Generate usage examples for a function
    
    Args:
        function_name: Name of the function
        parameters: List of parameter dictionaries with 'name' and 'type'
        description: Function description
        
    Returns:
        str: Code example
    """
    param_info = "\n".join([f"- {p['name']}: {p.get('type', 'any')}" for p in parameters])
    
    prompt = f"""Generate a practical code example showing how to use this function:

Function: {function_name}
Description: {description}

Parameters:
{param_info}

Provide:
1. A realistic use case
2. Complete code example with comments
3. Expected output or result

Format as a code block with explanatory comments."""

    try:
        return call_llm(prompt, max_tokens=300, temperature=0.7)
    except Exception as e:
        print(f"Error generating usage example: {e}")
        return f"# Example usage:\nresult = {function_name}()"

def batch_process_prompts(prompts: List[str], max_tokens: int = 200) -> List[str]:
    """
    Process multiple prompts efficiently
    
    Args:
        prompts: List of prompts to process
        max_tokens: Max tokens per response
        
    Returns:
        List of responses
    """
    responses = []
    
    for i, prompt in enumerate(prompts):
        try:
            print(f"Processing prompt {i+1}/{len(prompts)}...")
            response = call_llm(prompt, max_tokens=max_tokens)
            responses.append(response)
            
            # Rate limiting: small delay between requests
            if i < len(prompts) - 1:
                time.sleep(0.5)
        
        except Exception as e:
            print(f"Error processing prompt {i+1}: {e}")
            responses.append(f"Error: {str(e)}")
    
    return responses

def test_llm_connection() -> bool:
    """
    Test LLM connection and configuration
    
    Returns:
        bool: True if connection successful
    """
    print(f"Testing LLM connection (Provider: {LLM_PROVIDER})...")
    
    test_prompt = "Say 'Hello, I am working correctly!' if you receive this message."
    
    try:
        response = call_llm(test_prompt, max_tokens=50)
        print(f"✅ LLM Response: {response}")
        return True
    except Exception as e:
        print(f"❌ LLM Connection Failed: {e}")
        return False

# Cost tracking (approximate)
COST_PER_1K_TOKENS = {
    "gpt-4": {"input": 0.03, "output": 0.06},
    "gpt-4-turbo": {"input": 0.01, "output": 0.03},
    "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
    "gemini-1.5-pro": {"input": 0.00125, "output": 0.005},
    "gemini-1.5-flash": {"input": 0.000125, "output": 0.0005}
}

def estimate_cost(prompt: str, response: str, model: str = None) -> float:
    """
    Estimate API call cost
    
    Args:
        prompt: Input prompt
        response: LLM response
        model: Model used
        
    Returns:
        float: Estimated cost in USD
    """
    if model is None:
        model = "gpt-3.5-turbo" if LLM_PROVIDER == "openai" else "gemini-1.5-flash"
    
    # Rough token estimation (1 token ≈ 4 characters)
    input_tokens = len(prompt) / 4
    output_tokens = len(response) / 4
    
    if model in COST_PER_1K_TOKENS:
        costs = COST_PER_1K_TOKENS[model]
        input_cost = (input_tokens / 1000) * costs["input"]
        output_cost = (output_tokens / 1000) * costs["output"]
        return input_cost + output_cost
    
    return 0.0

# Module-level helper instance
_helper_instance = None

def get_helper() -> LLMHelper:
    """Get singleton LLM helper instance"""
    global _helper_instance
    if _helper_instance is None:
        _helper_instance = LLMHelper()
    return _helper_instance