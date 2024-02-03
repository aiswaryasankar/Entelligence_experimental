import functools
import json
import requests
import pandas as pd
import re

from typing import Optional
from pathlib import Path

API_JSON_PATH = Path(__file__).parent / 'api_key.json'


def get_api_key(key_name:Optional[str]=None):
    
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with open(API_JSON_PATH) as f:
                json_dict = json.load(f)

            api_key = json_dict if key_name is None else {key_name: json_dict.get(key_name, '')}
            
            return func(api_key, *args, **kwargs)
        return wrapper
    return decorator
