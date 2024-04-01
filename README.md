# LLMT

[![PyPI version](https://badge.fury.io/py/llmt.svg)](https://badge.fury.io/py/llmt)

## Overview

Convenient LLM chat wrapper for data pipelines, CI/CD, or personal workspaces.

Supports local function calling, chat history retention, and can run anywhere. Chat using a terminal, input/output files, or directly through LLMT API.

### Usage

Use the package in directly in your python code (`pip install llmt`), or as a local workspace running a container to interact with ChatGPT.

### Module import

```python
from llmt import LLMT


llmt = LLMT()
llmt.init_assistant(
    "dataengineer",
    api_key="...",
    model="gpt-3.5-turbo",
    assistant_description="You are a data engineer, and a python expert.",)
llmt.init_functions(["./my_functions.py"])
llmt.init_chat("single_chat")

response = llmt.run(
    "What's the result of 22 plus 5 in decimal added to the hexadecimal number A?"
)
```

### Local workspace

Install Docker and make command. Make is not required since you can use docker compose.

- Clone this repo.
- If using custom functions, create your functions in the udf/ directory and import them in cli.py.
- Update the default configuration file, or create a new one in configs/.
- Run `make run`. Default config will let you use input and output files.
- Use files/input.md to send messages.
- Use files/output.md to receive messages.
- CTRL + C to quit out of the container and clean up orphans.

### Configuration file

If both (input_file, output_file) are ommited, then the default terminal will be used.
Using the input and output files to converse with an LLM is easier than using the terminal.

- **input_file**: specify a file for user input
- **output_file**: specify a file for LLM response
- **assistants**:
    - **type**: Assistant type, currently only OpenAI.
    - **assistant_name**: Assistant name.
    - **assistant_description**: Assistant description which OpenAI will use for assistant context.
    - **api_key**: OpenAI API key.
    - **model**: OpenAI model.
    - **tools**: Function definitions. For now, in addition to creating functions, functions must be also defined in a format which OpenAI API can understand. Functions take one object argument which must be unpacked to extract arguments within each function. Hopefully this changes in the future.

The image used for running this code has some common tools installed which I use daily in my custom functions:

- awscli
- cloudquery
- numpy
- pandas
- psycopg2-binary
- SQLAlchemy

Build and use your own image with additional tools for whatever your functions need.

## Need help?

I help organizations build data pipelines with AI integrations. If your organization needs help building or exploring solutions, feel free to reach me at artem at outermeasure.com. The general workflow is:

1. **Fine tune** a curated model with proprietary data to perform tasks specific to your pipeline.
2. **Deploy** the model in your cloud environment.
3. **Connect your pipeline** to the deployment via an API.
4. **Iterate and improve** the model.
