import json
from typing import Any

from app.config.settings import Settings, settings


class LLMConfigurationError(RuntimeError):
    pass


class LLMServiceError(RuntimeError):
    pass


class GeminiLLMService:
    def __init__(self, app_settings: Settings = settings, client: Any = None) -> None:
        self._settings = app_settings
        self._client = client

    def _get_client(self) -> Any:
        if not self._settings.gemini_api_key:
            raise LLMConfigurationError(
                "Gemini API key is not configured. Set GEMINI_API_KEY in backend/.env."
            )
        if self._client is None:
            try:
                from google import genai
                from google.genai import types

                self._client = genai.Client(
                    api_key=self._settings.gemini_api_key,
                    http_options=types.HttpOptions(
                        timeout=int(self._settings.gemini_timeout_seconds * 1000)
                    ),
                )
            except ImportError as error:
                raise LLMServiceError("The Gemini SDK is not installed.") from error
        return self._client

    def generate_json(self, prompt: str) -> dict[str, Any]:
        try:
            from google.genai import types

            response = self._get_client().models.generate_content(
                model=self._settings.gemini_model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.1,
                ),
            )
            text = getattr(response, "text", None)
            if not text:
                raise LLMServiceError("Gemini returned an empty response.")
            value = json.loads(text)
            if not isinstance(value, dict):
                raise LLMServiceError("Gemini returned a JSON value with the wrong shape.")
            return value
        except (LLMConfigurationError, LLMServiceError):
            raise
        except (ValueError, TypeError, json.JSONDecodeError) as error:
            raise LLMServiceError("Gemini returned invalid JSON.") from error
        except Exception as error:
            raise LLMServiceError("Gemini request failed.") from error

    def generate_text(self, prompt: str) -> str:
        try:
            response = self._get_client().models.generate_content(
                model=self._settings.gemini_model,
                contents=prompt,
            )
            text = getattr(response, "text", None)
            if not text:
                raise LLMServiceError("Gemini returned an empty response.")
            return text.strip()
        except (LLMConfigurationError, LLMServiceError):
            raise
        except Exception as error:
            raise LLMServiceError("Gemini request failed.") from error


def get_llm_service() -> GeminiLLMService:
    return GeminiLLMService()
