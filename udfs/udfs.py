import enum
import json
import logging


default_log_args = {
    "level": logging.INFO,
    "format": "%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    "datefmt": "%d-%b-%y %H:%M",
    "force": True,
}


logging.basicConfig(**default_log_args)
logger = logging.getLogger()


def add_decimal_values(value1: int, value2: int) -> int:
    """Add two decimal values together.

    Args:
        value1 (int): The first value.
        value2 (int): The second value.

    Returns:
        int: The sum of the two values.
    """
    return value1 + value2


def add_hexadecimal_values(value1: str, value2: str) -> str:
    """Add two hexadecimal values together.

    Args:
        value1 (str): The first value.
        value2 (str): The second value.

    Returns:
        str: The sum of the two values.
    """
    decimal1 = int(value1, 16)
    decimal2 = int(value2, 16)
    return hex(decimal1 + decimal2)[2:]


class Unit(str, enum.Enum):
    FAHRENHEIT = "fahrenheit"
    CELSIUS = "celsius"


def get_current_weather(location: str, unit: Unit = Unit.FAHRENHEIT):
    """Get the current weather in a given location.
    
    Args:
        location (str): The location to get the weather for
        unit (Unit, optional): The unit to return the temperature in. Defaults to Unit.FAHRENHEIT.

    Returns:
        str: The current weather in the location
    """
    if "tokyo" in location.lower():
        return json.dumps({"location": "Tokyo", "temperature": "10", "unit": unit})
    elif "san francisco" in location.lower():
        return json.dumps({"location": "San Francisco", "temperature": "72", "unit": unit})
    elif "paris" in location.lower():
        return json.dumps({"location": "Paris", "temperature": "22", "unit": unit})
    else:
        return json.dumps({"location": location, "temperature": "unknown"})
