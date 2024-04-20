import os
import time

from .managers import ChatManager, ContextManager, FileManager, FunctionManager
from .utils import load_config
from .assistants import OpenAIAssistant
from .prompts import prompt_create_chat, prompt_init, ask, ask_once, get_usage_as_string


class LLMT:
    def __init__(self, **kwargs):
        self.configs = None
        self.chat = None
        self.assistant = None
        self.file_manager = None
        self.function_manager = None
        self.config_file = kwargs.get("config_file", None)
        self.root_path = kwargs.get("root_path", os.getcwd())
        self.chat_manager = ChatManager(self.root_path)
        self.context_manager = ContextManager(self.root_path)

        if self.config_file:
            self.configs = load_config(self.config_file)

        self.init_file_manager()

    def get_chats(self):
        return list(self.chat_manager.list())

    def prompt_create_chat(self):
        return prompt_create_chat()

    def init_prompt(self):
        if not self.configs:
            raise ValueError("No configuration file provided.")

        return prompt_init(
            self.configs["assistants"], (["Create new chat file"] + self.get_chats())
        )

    def find_assistant(self, assistant_name):
        return next(
            (x for x in self.configs["assistants"] if x["name"] == assistant_name),
            None,
        )

    def init_assistant(self, assistant_name, **kwargs):
        if not self.configs:
            self.assistant = OpenAIAssistant(
                kwargs.get("api_key"),
                kwargs.get("model"),
                assistant_name,
                kwargs.get("assistant_description"),
            )

        if self.configs:
            selected_assistant = self.find_assistant(assistant_name)

            self.assistant = OpenAIAssistant(
                selected_assistant["api_key"],
                selected_assistant["model"],
                selected_assistant["assistant_name"],
                selected_assistant["assistant_description"],
            )

    def init_functions(self, paths):
        self.function_manager = FunctionManager(paths)

    def init_chat(self, chat_name):
        self.chat = chat_name
        self.chat_manager.create(chat_name)

    def init_context(self, chat_name):
        self.chat = chat_name
        self.context_manager.create(chat_name)

    def init_file_manager(self, **kwargs):
        if not self.configs:
            input_file = kwargs.get("input_file", None)
            output_file = kwargs.get("output_file", None)

        if self.configs:
            input_file = self.configs.get("input_file", None)
            output_file = self.configs.get("output_file", None)

        if input_file or output_file:
            self.file_manager = FileManager(self.root_path, input_file, output_file)

    def init_first_messages(self):
        if not self.assistant:
            raise ValueError("No assistant initialized.")
        if not self.chat:
            raise ValueError("No chat initialized.")

        if self.context_manager.list_messages() == 0:
            self.context_manager.save(
                {"role": "system", "content": self.assistant.description}
            )

    def init_chat_history(self):
        messages = self.chat_manager.get_history()
        for message in messages:
            self.file_manager.prepend_to_output(message)

    def run_forever(self):
        self.init_first_messages()

        if self.file_manager:
            self.init_chat_history()

        yield from ask(
            self.chat_manager,
            self.context_manager,
            self.file_manager,
            self.function_manager,
            self.assistant,
        )

    def run(self, message):
        self.init_first_messages()

        if self.file_manager:
            self.init_chat_history()

        return ask_once(
            message,
            self.context_manager,
            self.function_manager,
            self.assistant,
        )
