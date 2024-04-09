from typing import List

from openai import OpenAI
from openai.types.chat import ChatCompletion, ChatCompletionMessage


from .utils import logger


class OpenAIAssistant:
    def __init__(
        self,
        api_key: str,
        model: str,
        assistant_name: str,
        assistant_description: str,
    ) -> None:
        """Initialize the assistant.

        Args:
            api_key (str): The OpenAI API key.
            model (str): The model to use.
            assistant_name (str): The name of the assistant.
            assistant_description (str): The description of the assistant.
        """
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.assistant_name = assistant_name
        self.assistant_description = assistant_description

    def chat_completions_create(
        self, messages: List[ChatCompletionMessage], tools=None
    ) -> ChatCompletion:
        """Create a chat completion.

        Args:
            messages (list): List of ChatCompletionMessage objects.

        Returns:
            ChatCompletion: The chat completion.
        """
        if not tools:
            return self.client.chat.completions.create(
                messages=messages, model=self.model
            )

        return self.client.chat.completions.create(
            messages=messages, model=self.model, tools=tools
        )
    
    def wrap_functions(self, functions):
        return [
            {"type": "function", "function": function} for function in functions
        ] if functions else None

    def generate_message(
        self, messages: List[ChatCompletionMessage], functions=None
    ) -> ChatCompletion:
        """Generate a response from the assistant.

        Args:
            messages (list): List of ChatCompletionMessage objects.
            functions (list): List of functions to use.

        Returns:
            ChatCompletion: The chat completion.
        """
        logger.debug(f"Request: {messages}")
        return self.chat_completions_create(messages, tools=self.wrap_functions(functions))

    @property
    def name(self):
        return self.assistant_name

    @property
    def description(self):
        return self.assistant_description
