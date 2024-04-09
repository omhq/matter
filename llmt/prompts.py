import inquirer

from typing import List
from halo import Halo
from llmt.openai_types import FunctionCall
from openai.types import CompletionChoice, CompletionUsage
from openai.types.chat import (
    ChatCompletion,
    ChatCompletionMessage,
    ChatCompletionMessageToolCall,
)

from .assistants import OpenAIAssistant
from .consts import EXIT_CODES


class Style:
    GREEN = "\033[32m"
    RESET = "\033[0m"
    YELLOW = "\033[33m"


def prompt_create_chat():
    """Prompt the user to create a new chat thread.

    Returns:
        str: Chat name.
    """
    questions = [inquirer.Text("chat_name", message="Enter a chat name")]
    answers = inquirer.prompt(questions)
    return answers["chat_name"]


def prompt_init(assistants, chats):
    """Prompt the user to select an assistant and chats.

    Args:
        assistants (list): The list of assistants.
        chats (list): The list of chats.

    Returns:
        dict: The user's selections.
    """
    questions = [
        inquirer.List(
            "assistant",
            message="Select an assistant to use",
            choices=[x["name"] for x in assistants],
        ),
        inquirer.List(
            "chat_name",
            message="Select a chat file",
            choices=chats,
        ),
    ]

    return inquirer.prompt(questions)


def get_usage_as_string(usage: CompletionUsage) -> str:
    """Get the usage information.

    Returns:
        str: The usage information.
    """
    return ", ".join(
        [
            f'completion tokens: {usage["completion_tokens"]}',
            f'prompt tokens: {usage["prompt_tokens"]}',
            f'total tokens: {usage["total_tokens"]}',
        ]
    )


def run_until_response(messages, assistant, chat_manager, function_manager):
    function_calls = []

    while True:
        function_schema = (
            function_manager.functions_schema if function_manager else None
        )
        chat_completion: ChatCompletion = assistant.generate_message(
            messages, function_schema
        )
        chat_completion_choice: CompletionChoice = chat_completion.choices[0]
        chat_completion_message: ChatCompletionMessage = chat_completion_choice.message
        usage: CompletionUsage = chat_completion.usage
        response: str = chat_completion_message.content

        if chat_completion_choice.finish_reason == "tool_calls":
            tool_calls: List[ChatCompletionMessageToolCall] = (
                chat_completion_message.tool_calls
            )
            message = {"role": "assistant", "tool_calls": tool_calls}
            messages.append(message)

            for tool_call in tool_calls:
                args = tool_call.function.arguments
                fn_name = tool_call.function.name
                function_call: FunctionCall = {
                    "name": fn_name,
                    "arguments": args,
                }
                result = function_manager.run_function(function_call)
                message = {
                    "role": "tool",
                    "content": str(result.content),
                    "tool_call_id": tool_call.id,
                    "name": fn_name,
                }
                template_message = {**message, "arguments": args}
                messages.append(message)
                chat_manager.save_to_chat(message)
                function_calls.append(template_message)

            continue

        if chat_completion_choice.finish_reason == "stop":
            break

    return {
        "response": response,
        "messages": messages,
        "function_calls": function_calls,
        "usage": {
            "completion_tokens": usage.completion_tokens,
            "prompt_tokens": usage.prompt_tokens,
            "total_tokens": usage.total_tokens,
        },
    }


def ask_once(
    input_text,
    chat_manager,
    function_manager,
    assistant: OpenAIAssistant,
):
    """Chat with the assistant once.

    Args:
        input_text (str): The input text.
        chat_manager (ChatManager): The chat manager.
        function_manager (FunctionManager): The function manager.
        assistant (OpenAIAssistant): The assistant.
        functions (module): The functions module.

    Returns:
        dict: The assistant, response, function calls, and usage information.
    """
    message = {"role": "user", "content": input_text}
    messages = [{"role": "system", "content": assistant.description}, message]
    chat_manager.save_to_chat(message)

    response = run_until_response(
        messages,
        assistant,
        chat_manager,
        function_manager,
    )
    messages = response["messages"]
    message = {"role": "assistant", "content": response["response"]}
    messages.append(message)
    chat_manager.save_to_chat(message)

    return {
        "assistant": assistant,
        "response": response["response"],
        "function_calls": response["function_calls"],
        "info": get_usage_as_string(response["usage"]),
    }


def ask(
    chat_manager,
    file_manager,
    function_manager,
    assistant: OpenAIAssistant,
):
    """Chat with the assistant.

    Args:
        chat_manager (ChatManager): The chat manager.
        file_manager (FileManager or None): The input file handler object or None.
        function_manager (FunctionManager): The function manager.
        assistant (OpenAIAssistant): The assistant.

    Returns:
        None

    Yields:
        str: The response.
    """
    input_text = ""
    response = ""
    messages = [{"role": "system", "content": assistant.description}]
    spinner = Halo(text="Working...", spinner="dots")

    while True:
        if file_manager:
            print(f"{Style.GREEN}You{Style.RESET}: using {file_manager.input_file}")

            for event in file_manager.events_generator():
                input_text = event
                break
        else:
            input_text = input(f"{Style.GREEN}You{Style.RESET}: ").strip()

        if len(input_text) == 0:
            continue

        if input_text.lower() in EXIT_CODES:
            break

        message = {"role": "user", "content": input_text}
        messages.append(message)
        chat_manager.save_to_chat(message)

        spinner.start()
        response = run_until_response(
            messages,
            assistant,
            chat_manager,
            function_manager,
        )
        messages = response["messages"]
        spinner.stop()

        message = {"role": "assistant", "content": response["response"]}
        messages.append(message)
        chat_manager.save_to_chat(message)
        to_user_response = {
            "assistant": assistant,
            "response": response["response"],
            "function_calls": response["function_calls"],
            "info": get_usage_as_string(response["usage"]),
        }

        if file_manager:
            file_manager.write_to_output(to_user_response)
        else:
            yield " ".join(
                [
                    f"{Style.GREEN}{assistant.name}{Style.RESET}:",
                    f"{response['response']}\n\n{Style.YELLOW}usage{Style.RESET}:",
                    f"{get_usage_as_string(response['usage'])}",
                ]
            )
