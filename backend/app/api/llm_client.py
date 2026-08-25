import os
import time
import logging
import requests
from typing import List, Optional
from google import genai
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("pmc_chatbot.llm")

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

def call_openrouter_api(contents: str, models: Optional[List[str]] = None) -> Optional[str]:
    """Calls OpenRouter unified AI endpoint with enterprise models."""
    if not OPENROUTER_API_KEY:
        return None

    # Enterprise Open-Source Models (Hosted via OpenRouter, Free Production/Commercial Licenses)
    model_candidates = models or [
        "meta-llama/llama-3.3-70b-instruct",     # Llama 3.3 Community License (Free Production/Enterprise)
        "qwen/qwen-2.5-coder-32b-instruct",       # Apache 2.0 License (100% Open Source Commercial License)
        "deepseek/deepseek-r1-distill-llama-70b", # MIT / Llama License (Free Commercial License)
        "meta-llama/llama-3.1-8b-instruct"        # Llama 3.1 Community License (Free Commercial)
    ]


    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY.strip()}",
        "HTTP-Referer": "http://localhost:3000",
        "X-Title": "PMC Officer Query System",
        "Content-Type": "application/json"
    }

    for model_name in model_candidates:
        try:
            payload = {
                "model": model_name,
                "messages": [{"role": "user", "content": contents}],
                "temperature": 0.1
            }
            resp = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=45)
            if resp.status_code == 200:
                data = resp.json()
                text_content = data["choices"][0]["message"]["content"]
                if text_content:
                    logger.info(f"OpenRouter API success using model '{model_name}'.")
                    return text_content
            else:
                logger.warning(f"OpenRouter model '{model_name}' returned status {resp.status_code}: {resp.text}")
        except Exception as err:
            logger.warning(f"OpenRouter attempt failed on '{model_name}': {str(err)}")
            continue

    return None

def get_api_keys() -> List[str]:
    keys = []
    k1 = os.getenv("GEMINI_API_KEY")
    k2 = os.getenv("GEMINI_API_KEY_2")
    k3 = os.getenv("GEMINI_API_KEY_3")
    if k1: keys.append(k1.strip())
    if k2: keys.append(k2.strip())
    if k3: keys.append(k3.strip())
    return keys

def call_gemini_with_key_rotation(contents: str, models: Optional[List[str]] = None) -> tuple[str, str]:
    """
    Calls OpenRouter API first (if key configured). If OpenRouter fails, falls back to direct Gemini key rotation.
    Returns (response_text, provider_info)
    """
    # 1. Try OpenRouter API first
    if OPENROUTER_API_KEY:
        openrouter_result = call_openrouter_api(contents, models)
        if openrouter_result:
            return openrouter_result, "OpenRouter Enterprise API"

    # 2. Fallback to direct Gemini key rotation pool
    keys = get_api_keys()
    if not keys:
        raise ValueError("No OPENROUTER_API_KEY or GEMINI_API_KEY configured in environment.")

    model_candidates = models or ["gemini-3.6-flash", "gemini-2.5-flash", "gemini-1.5-flash"]
    last_err = ""

    for key_idx, key in enumerate(keys):
        client = genai.Client(api_key=key)
        for model_name in model_candidates:
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=contents
                )
                if response and response.text:
                    logger.info(f"Gemini API success using Key #{key_idx + 1} and model '{model_name}'.")
                    return response.text, f"Key-{key_idx + 1}"
            except Exception as err:
                last_err = str(err)
                if "429" in last_err or "RESOURCE_EXHAUSTED" in last_err:
                    logger.warning(f"Key #{key_idx + 1} hit 429 rate limit on model '{model_name}'. Rotating key...")
                    time.sleep(1.0)
                    break
                else:
                    logger.warning(f"Key #{key_idx + 1} failed on model '{model_name}': {last_err}")
                    continue

    raise RuntimeError(f"All LLM providers and keys failed. Last error: {last_err}")
