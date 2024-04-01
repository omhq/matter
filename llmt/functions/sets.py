from __future__ import annotations

import json
from abc import ABC, abstractmethod
from functools import partial
from typing import Any, Callable, TYPE_CHECKING, overload

from ..exceptions import FunctionNotFoundError, InvalidJsonError
from .functions import FunctionResult, OpenAIFunction, RawFunctionResult
from ..json_type import JsonType
from ..openai_types import FunctionCall
from .wrapper import FunctionWrapper, WrapperConfig

if TYPE_CHECKING:
    from ..json_type import JsonType
    from ..openai_types import FunctionCall


class FunctionSet(ABC):
    """A function set - a provider for a functions schema and a function runner"""

    @property
    @abstractmethod
    def functions_schema(self) -> list[JsonType]:
        """Get the functions schema"""

    @abstractmethod
    def run_function(self, input_data: FunctionCall) -> FunctionResult:
        """Run the function

        Args:
            input_data (FunctionCall): The function call

        Raises:
            FunctionNotFoundError: If the function is not found
        """

    def __call__(self, input_data: FunctionCall) -> JsonType:
        """Run the function with the given input data

        Args:
            input_data (FunctionCall): The input data from OpenAI

        Returns:
            JsonType: Your function's raw result
        """
        return self.run_function(input_data).result


class BaseFunctionSet(FunctionSet):
    """A function set that can be modified - functions can be added and removed"""

    @abstractmethod
    def _add_function(self, function: OpenAIFunction) -> None: ...

    @overload
    def add_function(self, function: OpenAIFunction) -> OpenAIFunction: ...

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
    ) -> Callable[..., Any]: ...

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
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]: ...

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
        """Add a function

        Args:
            function (OpenAIFunction | Callable[..., Any]): The function
            name (str): The name of the function. Defaults to the function's name.
            description (str): The description of the function. Defaults to getting
                the short description from the function's docstring.
            save_return (bool): Whether to send the return value of this
                function to the AI. Defaults to True.
            serialize (bool): Whether to serialize the return value of this
                function. Defaults to True. Otherwise, the return value must be a
                string.
            remove_call (bool): Whether to remove the function call from the AI's
                chat history. Defaults to False.
            interpret_as_response (bool): Whether to interpret the return
                value of this function as a response of the agent. Defaults to False.

        Returns:
            Callable[[Callable[..., Any]], Callable[..., Any]]: A decorator
            Callable[..., Any]: The original function
        """
        if isinstance(function, OpenAIFunction):
            self._add_function(function)
            return function
        if callable(function):
            self._add_function(
                FunctionWrapper(
                    function,
                    WrapperConfig(
                        None, save_return, serialize, remove_call, interpret_as_response
                    ),
                    name=name,
                    description=description,
                )
            )
            return function

        return partial(
            self.add_function,
            name=name,
            description=description,
            save_return=save_return,
            serialize=serialize,
            remove_call=remove_call,
            interpret_as_response=interpret_as_response,
        )


class OpenAIFunctionSet(BaseFunctionSet):
    """A tool set - a set of OpenAIFunction objects ready to be called.
    Inherited from `BaseFunctionSet`.

    Args:
        functions (list[OpenAIFunction] | None): The functions to initialize with.
    """

    def __init__(
        self,
        functions: list[OpenAIFunction] | None = None,
    ) -> None:
        self.functions = functions or []

    @property
    def functions_schema(self) -> list[JsonType]:
        """Get the functions schema, in the format OpenAI expects

        Returns:
            JsonType: The schema of all the available functions
        """
        return [function.schema for function in self.functions]

    def run_function(self, input_data: FunctionCall) -> FunctionResult:
        """Run the function

        Args:
            input_data (FunctionCall): The function call

        Returns:
            FunctionResult: The function output

        Raises:
            FunctionNotFoundError: If the function is not found
            InvalidJsonError: If the arguments are not valid JSON
        """
        function = self.find_function(input_data["name"])
        try:
            arguments = json.loads(input_data["arguments"])
        except json.decoder.JSONDecodeError as err:
            raise InvalidJsonError(input_data["arguments"]) from err
        result = self.get_function_result(function, arguments)
        return FunctionResult(
            function.name, result, function.remove_call, function.interpret_as_response
        )

    def find_function(self, function_name: str) -> OpenAIFunction:
        """Find a function in the functionset

        Args:
            function_name (str): The function name

        Returns:
            OpenAIFunction: The function of the given name

        Raises:
            FunctionNotFoundError: If the function is not found
        """
        for function in self.functions:
            if function.name == function_name:
                return function
        raise FunctionNotFoundError(function_name)

    def get_function_result(
        self, function: OpenAIFunction, arguments: dict[str, JsonType]
    ) -> RawFunctionResult | None:
        """Get the result of a function's execution

        Args:
            function (OpenAIFunction): The function to run
            arguments (dict[str, JsonType]): The arguments to run the function with

        Returns:
            RawFunctionResult | None: The result of the function, or None if the
                function does not save its return value
        """
        result = function(arguments)

        if function.save_return:
            return RawFunctionResult(result, serialize=function.serialize)
        return None

    def _add_function(self, function: OpenAIFunction) -> None:
        """Add a function to the functionset

        Args:
            function (OpenAIFunction): The function
        """
        self.functions.append(function)
