import requests
import re
import json
from config import ANTHROPIC_API_KEY
from src.llm.openai_client import OpenAIClient

class ClaudeClient:
    """Lightweight Claude (Anthropic) client wrapper.

    Behavior:
    - Mirrors the `OpenAIClient` interface: `extract_skills(text)` and
      `extract_comprehensive_details(text)`.
    - On failure or parsing errors, falls back to `OpenAIClient`'s
      enhanced fallback extractors (instantiates an internal `OpenAIClient`).
    Note: Install `requests` (already in `requirements.txt`) and set
    `ANTHROPIC_API_KEY` in env/.env to enable.
    """

    API_URL = "https://api.anthropic.com/v1/complete"

    def __init__(self):
        self.api_key = ANTHROPIC_API_KEY
        self.fallback = OpenAIClient()

    def call_anthropic(self, prompt, model="claude-haiku-4.5", max_tokens=1500, temperature=0.1):
        if not self.api_key:
            raise RuntimeError("ANTHROPIC_API_KEY not set")

        headers = {
            'x-api-key': self.api_key,
            'Content-Type': 'application/json'
        }

        payload = {
            'model': model,
            'prompt': prompt,
            'max_tokens_to_sample': max_tokens,
            'temperature': temperature
        }

        resp = requests.post(self.API_URL, headers=headers, json=payload, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def _parse_completion_text(self, resp_json):
        # Anthropic may return text under different keys; try common ones
        for key in ('completion', 'text', 'response', 'output'):
            if isinstance(resp_json, dict) and key in resp_json:
                return resp_json[key]

        # Some responses nest the completion
        if isinstance(resp_json, dict) and 'completion' in resp_json.get('completion', {}):
            return resp_json.get('completion')

        # Fallback to stringifying response
        return json.dumps(resp_json)

    def extract_skills(self, text):
        try:
            system_prompt = (
                "You are an expert HR technical analyst. Extract ALL technical skills, programming languages, "
                "frameworks, tools, and technologies from the CV text. Return ONLY a comma-separated list of skills."
            )

            user_prompt = f"{system_prompt}\n\n{text[:3500]}"
            resp_json = self.call_anthropic(user_prompt, max_tokens=800, temperature=0.3)
            completion = self._parse_completion_text(resp_json)
            # Extract first JSON-like/content block
            skills_text = str(completion).strip()
            skills = [s.strip() for s in re.split(r',|\n', skills_text) if s.strip()]
            return skills
        except Exception as e:
            print(f"⚠️ Claude client failed, falling back to OpenAIClient extractors: {e}")
            return self.fallback.advanced_fallback_skills(text)

    def extract_comprehensive_details(self, text):
        try:
            system_prompt = (
                "You are an expert CV analyst. Extract COMPLETE details from the CV in JSON format. "
                "Return exactly the JSON structure requested: personal_info, professional_info, education, technical_skills."
            )

            user_prompt = f"{system_prompt}\n\n{text[:4000]}"
            resp_json = self.call_anthropic(user_prompt, max_tokens=1500, temperature=0.1)
            completion = self._parse_completion_text(resp_json)
            result_text = str(completion).strip()

            try:
                json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
                if json_match:
                    json_str = json_match.group()
                    details = json.loads(json_str)
                    # Validate email with fallback
                    email = details.get('personal_info', {}).get('email', '')
                    if not self.fallback.is_valid_email(email):
                        details['personal_info']['email'] = self.fallback.enhanced_email_extraction(text)
                    return details
                else:
                    print("❌ No JSON found in Claude response; using fallback analysis")
                    return self.fallback.enhanced_fallback_analysis(text)
            except json.JSONDecodeError as e:
                print(f"❌ JSON parsing failed for Claude response: {e}")
                return self.fallback.enhanced_fallback_analysis(text)

        except Exception as e:
            print(f"⚠️ Claude analysis failed, using fallback: {e}")
            return self.fallback.enhanced_fallback_analysis(text)
