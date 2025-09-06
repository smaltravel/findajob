from . import LLM
from logging import Logger
from typing import List, Union, Optional
from google.genai.types import Content, GenerateContentConfig, Part
from google import genai
from pydantic import BaseModel, ValidationError
from app.schemas.search import AIProviderConfig


class GoogleAIProvider(LLM):
    """Google AI provider implementation with CV and job context management."""

    def __init__(self, config: AIProviderConfig, logger: Logger):
        super().__init__(config, logger)

        if not self.config.api_key:
            raise ValueError("Google AI API key is required")

        self.__client = genai.Client(
            api_key=self.config.api_key,
        )

        self.__history: List[Content] = []

    def _update_history(self, role: str, content: Union[List[Part], str]) -> List[Content]:
        if isinstance(content, str):
            self.__history.append(Content(role=role, parts=[Part(text=l.strip()) for l in content.split(
                "\n") if len(l.strip()) > 0]))
        elif isinstance(content, list) and all(isinstance(item, Part) for item in content):
            self.__history.append(Content(role=role, parts=content))
        else:
            raise ValueError(f"Invalid content type: {type(content)}")
        return self.__history

    def _get_system_instructions(self) -> Content:
        return Content(role="system", parts=[Part(text=l) for l in self.system_prompt.split(
            "\n") if len(l.strip()) > 0])

    def clear_history(self) -> None:
        self.__history.clear()

    def generate(self, prompt: str, format: BaseModel) -> Optional[str]:
        """Generate text using Google AI API."""

        self.logger.info(f"Using generate mode")

        response = self.__client.models.generate_content(
            model=self.config.model,
            contents=self._update_history("user", prompt),
            config=GenerateContentConfig(
                system_instruction=self._get_system_instructions(),
                response_schema=format.model_json_schema(),
                response_mime_type='application/json',
            )
        )

        self._update_history("model", response.text)

        try:
            return format.model_validate_json(response.text).model_dump_json()
        except ValidationError as e:
            self.logger.warning("Unsupported response format")
            self.logger.debug(f"Response text: {response.text}")
            return None

    def agent(self, prompt: str, format: BaseModel) -> Optional[str]:
        """Generate text using Google AI API with tools."""

        if self.tools is None and self.callable_tools is None:
            raise ValueError("Tools are required for agent mode")

        self.logger.info(f"Using agent mode")

        config = GenerateContentConfig(
            system_instruction=self._get_system_instructions(),
            tools=self.tools,
        )

        response = self.__client.models.generate_content(
            model=self.config.model,
            contents=self._update_history("user", prompt),
            config=config
        )

        use_tools = response.candidates[0].content.parts[0].function_call

        while use_tools:
            self.logger.info(f"Requested tools: {[t.name for t in use_tools]}")
            self._update_history(
                response.candidates[0].content.role, response.candidates[0].content.parts)

            tools_response = {}
            for tool in use_tools:
                tools_response[tool.name] = self.callable_tools[tool.name](
                    **tool.args)

            response = self.__client.models.generate_content(
                model=self.config.model,
                contents=self._update_history("function_response", [Part.from_function_response(
                    name=n, response={"result": r}) for n, r in tools_response.items()]),
                config=config
            )
            use_tools = response.candidates[0].content.parts[0].function_call

        self._update_history(
            response.candidates[0].content.role, response.candidates[0].content.parts)

        try:
            return format.model_validate_json(response.text).model_dump_json()
        except ValidationError as e:
            self.logger.warning("Unsupported response format")
            return self.generate("Regenerate job summary in JSON format, strictly follow the schema", format)
