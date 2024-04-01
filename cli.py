import argparse

from llmt import LLMT


def parse_args() -> argparse.Namespace:
    """Parse the command line arguments.

    Returns:
        argparse.Namespace: The parsed command line arguments.
    """
    parser = argparse.ArgumentParser(description="Data Assistant")
    parser.add_argument(
        "-f" "--config-file",
        type=str,
        dest="config_file",
        required=True,
        help="The path to the configuration file.",
    )
    parser.add_argument(
        "--create-chat",
        action="store_true",
        dest="create_chat",
        help="Create chat.",
    )

    return parser.parse_args()


if __name__ == "__main__":
    args: argparse.Namespace = parse_args()
    config_file = args.config_file
    create_chat = args.create_chat

    llmt = LLMT(
        config_file=config_file,
        root_path=".",
    )

    if create_chat or len(llmt.get_chats()) == 0:
        chat_name = llmt.prompt_create_chat()
        llmt.init_chat(chat_name)

    init_answers = llmt.init_prompt()
    selected_assistant = llmt.find_assistant(init_answers["assistant"])
    llmt.init_assistant(selected_assistant["assistant_name"])
    llmt.init_functions(selected_assistant["functions"])
    llmt.init_chat(init_answers["chat_name"])

    for response in llmt.run_forever():
        print(f"\n{response}\n")
