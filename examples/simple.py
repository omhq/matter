import os
import logging
from llmt import LLMT


default_log_args = {
    "level": (logging.DEBUG if os.environ.get("DEBUG", None) else logging.WARN),
    "format": "%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    "datefmt": "%d-%b-%y %H:%M",
    "force": True,
}

logging.basicConfig(**default_log_args)
logger = logging.getLogger()


if __name__ == "__main__":
    llmt = LLMT()
    llmt.init_assistant(
        "snowflake",
        api_key="",
        model="gpt-3.5-turbo",
        assistant_description="You are a snowflake expert. Answer questions briefly in a sentence or less."
    )

    llmt.init_functions(["/workspace/udfs/udfs.py"])
    llmt.init_context("snowflake")
    response = llmt.run("generate an example merge dml")

    logger.info(response)
