import os
import sys
import json
import time
import jinja2
import importlib.util

from typing import Any, Callable, overload
from inspect import getmembers, isfunction
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from .functions.functions import FunctionResult, OpenAIFunction
from .functions.sets import OpenAIFunctionSet
from .json_type import JsonType
from .openai_types import FunctionCall
from .utils import logger
from .consts import RESPONSE_TEMPLATE


class EventHandler(FileSystemEventHandler):
    """Event handler for the input file system events."""

    def __init__(self):
        super().__init__()

        self.contents = ""
        self.event_queue = []

    def read_file(self, file_path: str) -> str:
        with open(file_path, "r") as file:
            return file.read()

    def on_modified(self, event):
        if not event.is_directory:
            content_updates = self.read_file(event.src_path).strip()

            if content_updates != self.contents:
                self.contents = content_updates

                if self.contents != "":
                    self.event_queue.append(content_updates)

    def events_generator(self):
        while True:
            if self.event_queue:
                yield self.event_queue.pop(0)
            else:
                time.sleep(0.1)


class FileManager:
    def __init__(self, root_path, input_file: str, output_file: str):
        self.input_file = os.path.join(root_path, "files", input_file)
        self.output_file = os.path.join(root_path, "files", output_file)

        self.init()

        self.event_handler = EventHandler()
        self.observer = Observer()
        self.observer.schedule(self.event_handler, self.input_file, recursive=False)
        self.observer.start()
        self.env = jinja2.Environment(
            trim_blocks=True,
            lstrip_blocks=True,
            loader=jinja2.FileSystemLoader(searchpath=os.path.join(root_path, "llmt")),
        )

    def init(self):
        if not os.path.exists(self.input_file):
            with open(self.input_file, "w") as f:
                f.write("")

        if not os.path.exists(self.output_file):
            with open(self.output_file, "w") as f:
                f.write("")

    def output_file_contents(self):
        with open(self.output_file, "r") as f:
            return f.read()

    def write_to_output(self, data):
        template = self.env.get_template(RESPONSE_TEMPLATE)
        file_contents = self.output_file_contents()
        date = time.strftime("%Y-%m-%d %I:%M%p")
        data["date"] = date
    
        with open(self.output_file, "w") as f:
            f.write(template.render(**data))

            if file_contents:
                f.write("\n\n")
                f.write("---")
                f.write("\n\n")
                f.write(file_contents)

    def events_generator(self):
        yield from self.event_handler.events_generator()
        self.observer.join()

    def __del__(self):
        self.observer.stop()


class ChatManager:
    def __init__(self, path):
        self.path = f"{path}/chats"

        if not os.path.exists(self.path):
            os.makedirs(self.path)

    def init_chat(self, chat_name):
        self.chat_name = chat_name
        self.file_path = os.path.join(self.path, f"{self.chat_name}.json")

        if not os.path.exists(self.file_path):
            with open(self.file_path, "w") as f:
                json.dump([], f)

    def save_to_chat(self, message):
        chat_list = []

        with open(self.file_path) as f:
            chat_list = json.load(f)

        chat_list.append(message)

        with open(self.file_path, "w") as f:
            json.dump(chat_list, f, indent=4)

    def list_chats(self):
        return [x.split(".")[0] for x in os.listdir(self.path) if x.endswith(".json")]

    def list_messages(self):
        with open(os.path.join(self.path, f"{self.chat_name}.json")) as f:
            return len(json.load(f))


class FunctionManager():
    def __init__(self, paths):
        self._paths = []
        self.functions = OpenAIFunctionSet(*([]))

        for path in paths:
            if not os.path.exists(path):
                logger.warning(f"Path {path} does not exist.")
                continue
            self._paths.append(path)
            self._init_functions(path)
    
    def _path_exists(self, path):
        return os.path.exists(path)
    
    def _module_functions(self, path):
        spec = importlib.util.spec_from_file_location("llmt.udfs", path)
        module = importlib.util.module_from_spec(spec)
        sys.modules["llmt.udfs"] = module
        spec.loader.exec_module(module)
        return getmembers(module, isfunction)

    def _init_functions(self, path):
        functions = self._module_functions(path)
        for _, function in functions:
            self.add_function(function)

    @property
    def functions_schema(self) -> list[JsonType]:
        """Get the functions schema for the conversation.

        Returns:
            list[JsonType]: The functions schema.
        """
        return self.functions.functions_schema

    @overload
    def add_function(self, function: OpenAIFunction) -> OpenAIFunction:
        ...

    @overload
    def add_function(
        self,
        function: Callable[..., Any],
        *,
        name: str | None = None,
        description: str | None = None,
        save_return: bool = True,
        serialize: bool = True,
        remove_call: bool = False,
        interpret_as_response: bool = False,
    ) -> Callable[..., Any]:
        ...

    @overload
    def add_function(
        self,
        *,
        name: str | None = None,
        description: str | None = None,
        save_return: bool = True,
        serialize: bool = True,
        remove_call: bool = False,
        interpret_as_response: bool = False,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        ...

    def add_function(
        self,
        function: OpenAIFunction | Callable[..., Any] | None = None,
        *,
        name: str | None = None,
        description: str | None = None,
        save_return: bool = True,
        serialize: bool = True,
        remove_call: bool = False,
        interpret_as_response: bool = False,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]] | Callable[..., Any]:
        """Make a function available to the AI.

        Args:
            function (OpenAIFunction | Callable[..., Any]): The function to add
            name (str): The name of the function. Defaults to the function's name.
            description (str): The description of the function. Defaults to getting
                the short description from the function's docstring.
            save_return (bool): Whether to send the return value of this function back
                to the AI. Defaults to True.
            serialize (bool): Whether to serialize the return value of this function.
                Otherwise, the return value must be a string.
            remove_call (bool): Whether to remove the function call itself from the chat
                history.
            interpret_as_response (bool): Whether to interpret the return value of this
                function as the natural language response of the AI.

        Returns:
            Callable[[Callable[..., Any]], Callable[..., Any]]: A decorator.
            Callable[..., Any]: The original function.
        """
        if function is None:
            return self.functions.add_function(
                name=name,
                description=description,
                save_return=save_return,
                serialize=serialize,
                remove_call=remove_call,
                interpret_as_response=interpret_as_response,
            )
        return self.functions.add_function(
            function,
            name=name,
            description=description,
            save_return=save_return,
            serialize=serialize,
            remove_call=remove_call,
            interpret_as_response=interpret_as_response,
        )

    def run_function(
        self,
        function_call: FunctionCall,
    ) -> FunctionResult:
        """Run a function.

        Args:
            function_call (FunctionCall): The function call.

        Raises:
            TypeError: If the function returns a None value.

        Returns:
            FunctionResult: The function output.
        """
        return self.functions.run_function(function_call)
