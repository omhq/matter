import logging


default_log_args = {
    "level": logging.INFO,
    "format": "%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    "datefmt": "%d-%b-%y %H:%M",
    "force": True,
}


logging.basicConfig(**default_log_args)
logger = logging.getLogger()


def fetch_customers() -> list[dict[str, str | int]]:
    """Fetches a list of customers from a database.

    Args:
        format (str): The format to return the data in. Defaults to "json".
    
    Returns:
        list: A list of dictionaries, each containing customer information.
    """
    return [
        {"name": "Alice", "age": 25, "city": "New York"},
        {"name": "Bob", "age": 30, "city": "San Francisco"},
        {"name": "Charlie", "age": 35, "city": "Chicago"},
        {"name": "David", "age": 40, "city": "New York"},
        {"name": "Eve", "age": 45, "city": "San Francisco"},
        {"name": "Frank", "age": 50, "city": "New York"},
        {"name": "Grace", "age": 55, "city": "Chicago"},
    ]


def fetch_products_sold_by_city(city: str) -> list[dict[str, str | float | int] | None]:
    """Fetches a list of products sold in a city.
    
    Args:
        city (str): The city to fetch products for.
    
    Returns:
        list: A list of dictionaries, each containing product information.
    """
    if city == "New York":
        return [
            {"name": "Apple", "price": 1.0, "quantity": 10},
            {"name": "Banana", "price": 2.0, "quantity": 20},
        ]
    
    if city == "San Francisco":
        return [
            {"name": "Orange", "price": 3.0, "quantity": 30},
            {"name": "Pear", "price": 4.0, "quantity": 40},
        ]
    
    if city == "Chicago":
        return [
            {"name": "Grape", "price": 5.0, "quantity": 50},
            {"name": "Kiwi", "price": 6.0, "quantity": 60},
        ]
