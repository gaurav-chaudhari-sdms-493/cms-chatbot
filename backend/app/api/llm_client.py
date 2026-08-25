import os
import time
import logging
from typing import List, Optional
from google import genai
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("pmc_chatbot.llm")

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
    Calls Gemini API with automatic key rotation and model fallbacks.
    Returns (response_text, key_used_index)
    """
    keys = get_api_keys()
    if not keys:
        raise ValueError("No GEMINI_API_KEY configured in environment.")

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
                    break  # Break inner model loop, try next API key immediately
                else:
                    logger.warning(f"Key #{key_idx + 1} failed on model '{model_name}': {last_err}")
                    continue

    raise RuntimeError(f"All Gemini API keys and models failed. Last error: {last_err}")
