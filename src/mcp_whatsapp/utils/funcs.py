
import io
import json
import operator
import random
import re
from collections import deque
from collections.abc import Callable, Iterable, Mapping, Sequence
from collections.abc import Set as AbstractSet
from dataclasses import asdict, is_dataclass
from datetime import date, datetime, time
from enum import Enum
from functools import reduce, wraps
from inspect import isfunction
from itertools import groupby, zip_longest
from pathlib import Path
from time import sleep
from typing import Any, TypeVar
from urllib.parse import unquote, urlparse
from uuid import UUID
from zoneinfo import ZoneInfo

import fitz
import numpy as np
import requests as req
import torch
from inputimeout import TimeoutOccurred, inputimeout
from PIL import Image
from pydoll.browser.tab import Tab
from pydoll.commands.page_commands import PageCommands
from tqdm.auto import tqdm


def safe_list_get(l: list, idx: int, default = None):
    """
    Safely retrieves an element from a list or numpy array at the specified index.

    Args:
        l (list or numpy.ndarray): The list or numpy array from which to retrieve the element.
        idx (int): The index of the element to retrieve.
        default (optional): The default value to return if the list or numpy array is None or the index is out of range. Defaults to None.

    Returns:
        The element at the specified index if the list or numpy array is not None and the index is within range. Otherwise, returns the default value.
    """
    if l is None or not isinstance(l, (list, np.ndarray)) or len(l)<=idx:
        return default
    else:
        return l[idx]

def is_obj(obj):
    """
    Check if the given object is not a primitive data type.

    Parameters:
        obj (any): The object to be checked.

    Returns:
        bool: True if the object is not a primitive data type, False otherwise.
    """
    return not is_primitive(obj)
    
    
T = TypeVar('T')
def first(the_iterable:Iterable[T], condition = lambda x: True)->T|None:
    """
    Returns the first element in the iterable that satisfies the given condition.

    Args:
        the_iterable (iterable): An iterable object containing elements to search through.
        condition (function, optional): A function that takes an element as input and returns a boolean value. The default condition is a lambda function that always returns True.

    Returns:
        The first element in the iterable that satisfies the given condition. If no element satisfies the condition, None is returned.
    """
    for i in the_iterable:
        if condition(i):
            return i
        


def is_primitive(var):
    """
    Check if the given variable is a primitive data type.

    Parameters:
        var (any): The variable to check.

    Returns:
        bool: True if the variable is a primitive data type, False otherwise.
    """
    primitive = (int, float, str, bool, type(None), np.number)
    return isinstance(var, primitive)
    
def empty_list_or_dict(var):
        """
        Returns an empty list if the input variable is a list or a numpy array, otherwise returns an empty dictionary.

        Parameters:
            var (any): The input variable to check.

        Returns:
            list or dict: An empty list if the input variable is a list or a numpy array, otherwise an empty dictionary.
        """
        return [] if isinstance(var, (list, np.ndarray)) else {}
    
def is_etarable_contaner(objects: Any):
        """
        Check if the given object is an iterable container.

        Parameters:
            objects (any): The object to be checked.

        Returns:
            bool: True if the object is a list or a numpy array, False otherwise.
        """
        return isinstance(objects, (list, np.ndarray))

def switch_or_find_and_call_func(data:Any, switch_dict:dict[str, Callable[[Any], Any]], current_name):
        """
        Executes a function based on the given `current_name` from the `switch_dict` dictionary.

        Args:
            data (Any): The input data to be passed to the function.
            switch_dict (Dict[str, Callable[[Any], Any]]): A dictionary mapping `current_name` to a function.
            current_name (str): The name of the function to be executed.

        Returns:
            Any: The result of the executed function.

        Raises:
            Exception: If the `current_name` is not found in the `switch_dict` dictionary.
        """
        if  current_name in switch_dict:
            return switch_dict[current_name](data)
        else:
            for keys, vals in switch_dict.items():
                if current_name.find(keys) != -1:
                    return vals(data)
                
        return Exception(f"Error: '{current_name}' not found in {json.dumps(switch_dict, default=json_default, indent=4)}.")
        
        
        
        
def json_default(obj):
    """
    Converts an object to a JSON serializable format.
    Карочь функция фиксит добалбанутый json на python, вставляется на место default в json.dumps
    Args:
        obj (Any): The object to be converted.

    Returns:
        Any: The converted object. If the input object is a set, it is converted to a sorted list of primitive values.
        If the input object is a function, its name is returned. Otherwise, the input object is returned as is.

    Raises:
        None
    """
    if isinstance(obj, set):
        listObj = list(obj)
        def is_not_object(x):
            if is_primitive(x) and not isinstance(x, np.number):
                return x
            elif isinstance(x, np.number):
                return float(x)
        
        listprimitive = map(is_not_object, listObj)
        return sorted(listprimitive, key=lambda x:x if not x is None else 0)
    elif isinstance(obj, (np.ndarray, torch.Tensor)):
        return obj.tolist()
    elif isinstance(obj, np.number):
        return obj.item()
    elif isfunction(obj):
        return obj.__name__+'(...)'
    return obj

def make_flat_dict(dict, list_select=None):
    if list_select is None:
        list_select = dict.keys()
        
    for name in list_select:
        for i, val in zip(range(len(dict[name])),dict[name]):
            yield name+str(i), val
            
            
def unzip(zipped_list):  
  return zip_longest(*zipped_list)

def if_can_to_int(val):
    if isinstance(val, (np.number, float)) and not np.isnan(val):
        if round(val) == val: # type: ignore
            return int(val)
    else:
        return val



def set_like(func, *set_like):    
    return list(func(*(set(i) for i in set_like)))


def set_like_order(func, *set_likes):
    all = reduce(operator.iadd, (list(set_like) for set_like in set_likes), [])
    after_func = set_like(func, *set_likes)
    return [i for i in all if i in after_func]



def init_accuracy_leap(val):
    i = 0
    while True:
        if val*10**i >= 1:
            return 10**i
        i+=1

TObj = TypeVar('TObj')
def raise_none(obj: None| TObj) -> TObj: 
    if obj is None:
        raise TypeError(obj)
    else:
        return obj
    
def raise_as(obj, type_):
    if not isinstance(obj, type_):
        raise TypeError(obj)
    else:
        return obj
    
def sort_dict(index:dict, axis: int):
    lst = list(index.items())
    lst.sort(key=lambda x: x[axis])
    return {k:v for k,v in lst}

def get_len(obj):
    if isinstance(obj, (list, np.ndarray, tuple, Sequence)):
        return len(obj)
    else:
        return 1
    
def search(arr, element):
    for i, arr_item in enumerate(arr):
        if arr_item == element:
            return i
    return -1
    
    
def to_value(element):
    if isinstance(element, Sequence) and len(element) == 1 and not isinstance(element, str):
        return to_value(element[0])
    elif isinstance(element, np.ndarray) and np.prod(np.array(element.shape)) == 1:  # noqa: SIM114
        return to_value(element.item())
    elif isinstance(element, np.generic):  # noqa: SIM114
        return to_value(element.item())
    elif isinstance(element, torch.Tensor) and element.numel() == 1:
        return to_value(element.item())
    elif isinstance(element, set):
        return to_value(list(element))
    elif isinstance(element, (int, float, complex)):
        return element
    else:
        raise TypeError(f"Unsupported type: {type(element)}")
    
    
def inverce_dict(dict_)->dict:
    if isinstance(next(iter(dict_.values())), (Iterable)):
        inverce_couple = ((a_v,k) for k,v in dict_.items() for a_v in v)
        inverce_couple = sorted(inverce_couple, key=lambda x: x[0])
        grouped_inverce_couple = ((key, sequence) for key, sequence in groupby(inverce_couple, key=lambda x: x[0]))
        return {k:[x[1] for x in v] for k,v in grouped_inverce_couple}
    else:
        return {v:k for k,v in dict_.items()}
    
    
    
class cached_classproperty:
    def __init__(self, func):
        self.func = func
        self.attr = "_"+func.__name__
    def __get__(self, instance, owner):
        # cache result on owner (the class) to avoid recomputation
        if self.attr not in owner.__dict__:
            value = self.func(owner)
            setattr(owner, self.attr, value)
        return getattr(owner, self.attr)
    
        
        
def is_subdict(dict_1, dict_2):
    for key, value in dict_2.items():
        if key not in dict_1 or dict_1[key] != value:
            return False
    return True


def subdict_report(dict_1, dict_2):
    for key, value in dict_2.items():
        if key not in dict_1 or dict_1[key] != value:
            yield f"{f"{key} not in dict_1" if key not in dict_1 else f"dict_1[{key}]:{dict_1[key]} != dict_2[{key}]:{value}"}"


def is_sublist(list_1, list_2):
    return set(list_1).issubset(set(list_2))

def sublist_report(list_1, list_2):
    delta_1 = set(list_2) - set(list_1)
    for value in delta_1:
        yield f"{value} not exist in dict_1"
        
def get_max_len_key(dict_:dict):
    max_key = next(iter(dict_.keys()))
    for key, val in dict_.items():
        if len(val) > len(dict_[max_key]):
            max_key = key
    return max_key


def get_min_len_key(dict_:dict):
    min_key = next(iter(dict_.keys()))
    for key, val in dict_.items():
        if len(val) < len(dict_[min_key]):
            min_key = key
    return min_key


def get_seed(rng: np.random.Generator):
    return rng.integers(0, np.iinfo(np.int32).max)

def exclude(m, exclude):
    return list(set(m) - set(exclude))


class ProgressiveTryError(Exception):
    pass


def progresive_try(func, n_tries, max_s = 60, base = 4, final_raise = True, error_type = Exception):
    for i in range(n_tries):
        try:
            return func()
        except error_type as e:
            s = abs(min(base**(i+1), max_s) + random.normalvariate(0, base))
            tqdm.write(f"[progresive_try] Error: {e}. Retrying...({s}s)")
            sleep(s)
    
    if final_raise:
        raise ProgressiveTryError(f"[progresive_try] Failed {n_tries} times.")
        
def fac_progresive_try(n_tries, max_s = 100, base = 4, final_raise = True):
    def dec_progresive_try(func):
        @wraps(func)
        def _progresive_try_wrap():
            return progresive_try(func, n_tries, max_s, base, final_raise)
        return _progresive_try_wrap
    return dec_progresive_try

        
def fac_progresive_try_with_params(n_tries, max_s = 100, base = 4, final_raise = True):
    def dec_progresive_try(func):
        @wraps(func)
        def _progresive_try_wrap(*args, **kwards):
            def func_wrap():
                return func(*args, **kwards)
            return progresive_try(func_wrap, n_tries, max_s, base, final_raise)
        return _progresive_try_wrap
    return dec_progresive_try


T = TypeVar('T')


class PassError(Exception):
    pass

class InteractiveRetryHandler:
    def __init__(self, n_tries: int = 5, timeout_retry: int = 30*60, ping_func: Callable[[], bool]|None = None):
        self.n_tries = n_tries
        self.timeout_retry = timeout_retry
        self.ping_func = ping_func
        
    def set_ping_func(self, ping_func: Callable[[], bool]|None):
        self.ping_func = ping_func
        
    def __call__(self,func: Callable[[], T], n_tries: int|None = None, timeout_retry: int|None = None, ping_func: Callable[[], bool]|None = None) -> T:
        """
        Attempts to execute a function up to n_tries times, asking the user
        whether to retry or quit upon each failure.

        Args:
            func (Callable[[], T]): The function to execute. It must take no arguments.
            n_tries (int): The maximum number of attempts allowed.

        Returns:
            T: The result of the function if it succeeds.

        Raises:
            Exception: Re-raises the last exception if all retries fail or if the user chooses to quit.
        """
        if n_tries is None:
            n_tries = self.n_tries
        if timeout_retry is None:
            timeout_retry = self.timeout_retry
        if ping_func is None:
            ping_func = self.ping_func
        
        last_exeption = None
        for attempt in range(1, n_tries + 1):
            try:
                return func() 
            
            except Exception as e:
                tqdm.write(f"\nAn error occurred: {e}")
                last_exeption = e
                
                if ping_func is not None and ping_func():
                    tqdm.write("Request corrupted. Queting...")
                    raise PassError("Request corrupted.")

                if attempt == n_tries:
                    tqdm.write("This was the final attempt. The operation has failed.")
                    raise
                
                while True:
                    user_input = None
                    try:
                        user_input = inputimeout(prompt=f"Do you want to (r)etry or (p)ass? (autoretry in {timeout_retry}s)", timeout=timeout_retry)
                        print(f"You said: {user_input}")
                    except TimeoutOccurred:
                        user_input = 'r'
                        break
                    
                    if user_input in ('r', 'retry'):
                        break 
                    elif user_input in ('p', 'pass'):
                        error_str="Passing as requested by user."
                        tqdm.write(error_str)
                        raise PassError(error_str)
                    else:
                        tqdm.write("Invalid input. Please enter 'r' or 'p'.")
        
        raise raise_none(last_exeption)
                            
interactive_retry = InteractiveRetryHandler()

class RetryHandler:
    def __init__(self, n_tries: int = 5, callbacks: list|None = None):
        self.n_tries = n_tries
        self.callbacks = callbacks if callbacks is not None else []
        
    def adds_callbacks(self, callbacks):
        self.callbacks.extend(callbacks)
        
    def clear_callbacks(self):
        self.callbacks = []
        
    def __call__(self, func: Callable[[], T], n_tries: int|None = None):
        if n_tries is None:
            n_tries = self.n_tries
            
        def prog_inc_func():
            try:
                return func
            except Exception as e:
                tqdm.write(f"\nAn error occurred: {e}")
                for callback in self.callbacks:
                    callback.on_llm_error(e)
                raise
        return interactive_retry(raise_none(progresive_try(prog_inc_func, n_tries)), n_tries)

retry = RetryHandler()
    
    



def optimize_image(pix: fitz.Pixmap, max_size=(1024, 1024), quality=70, format="JPEG") -> io.BytesIO:
    """
    Compresses and resizes the image for the LLM to save bandwidth and tokens.
    Returns the optimized image as a base64 string.
    """
    # 1. Load the PyMuPDF Pixmap into a Pillow Image
    img:Image.Image = Image.open(io.BytesIO(pix.tobytes("png")))
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    img.thumbnail(max_size, Image.Resampling.LANCZOS)
    buffer = io.BytesIO()
    img.save(buffer, format=format, optimize=True, quality=quality)
    return buffer

def get_unified_timeout():
    return random.uniform(1, 3) + random.betavariate(50, 50)*6


 
async def set_timezone_auto(tab:Tab, timezone_id: str):
    """
    Override timezone via JavaScript, automatically calculating 
    the correct summer/winter offset for the current date.

    Args:
        tab: The PyDoll browser tab
        timezone_id: IANA timezone name
    """
    target_tz = ZoneInfo(timezone_id)
    now_in_target_tz = datetime.now(target_tz)
    
    offset_minutes = int(raise_none(now_in_target_tz.utcoffset()).total_seconds() / 60)
    
    js_offset = -offset_minutes
    script = f'''
        const _origDTF = Intl.DateTimeFormat;
        Intl.DateTimeFormat = function(...args) {{
            const opts = args[1] || {{}};
            opts.timeZone = '{timezone_id}';
            return new _origDTF(args[0], opts);
        }};
        Object.defineProperty(Intl.DateTimeFormat, 'prototype', {{
            value: _origDTF.prototype
        }});
        Date.prototype.getTimezoneOffset = function() {{ return {js_offset}; }};
    '''
    
    command = PageCommands.add_script_to_evaluate_on_new_document(source=script)
    await tab._connection_handler.execute_command(command)


def get_robust_filename(response: req.Response, fallback_html_text: str = "") -> str:
    """
    Extracts the true filename from the HTTP response exactly like a browser does.
    """
    
    if "Content-Disposition" in response.headers:
        content_disposition = response.headers["Content-Disposition"]
        
        # RFC 5987 formatted names (e.g., filename*=UTF-8''Zadanie.pdf)
        match_utf8 = re.search(r"filename\*=UTF-8''([^;]+)", content_disposition, re.IGNORECASE)
        if match_utf8:
            return unquote(match_utf8.group(1)).strip()
        
        # standard formatted names (e.g., filename="Zadanie.pdf")
        match = re.search(r'filename=["\']?([^;"\']+)["\']?', content_disposition, re.IGNORECASE)
        if match:
            return match.group(1).strip()

    url_path = urlparse(response.url).path
    name_from_url = url_path.split('/')[-1]
    if name_from_url and '.' in name_from_url:
        return unquote(name_from_url).strip()
    
    fallback_html_text = fallback_html_text.strip()
    if fallback_html_text and '.' in fallback_html_text:
        return fallback_html_text
        
    raise ValueError(
        f"Cannot determine a filename for URL: {response.url}\n"
        f"Headers: {response.headers.get('Content-Disposition')}"
    )

def to_jsonable(obj):
    """
    Recursively converts any Python structure into pure JSON-serializable primitives.
    
    - NumPy arrays -> list
    - NumPy scalars -> int, float, bool, or dict(real, imag)
    - Sets / Frozensets -> sorted list
    - Defaultdict / Mappings -> standard dict with string keys
    - Dataclasses / Pydantic / Custom Objects -> dict
    - Date / Time / UUID / Path -> str
    """
    if obj is None or isinstance(obj, (bool, str, int)):
        return obj

    if isinstance(obj, float):
        return obj

    
    if isinstance(obj, np.ndarray):
        return to_jsonable(obj.tolist())
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.floating):
        return float(obj)
    if isinstance(obj, np.bool_):
        return bool(obj)
    if isinstance(obj, np.complexfloating):
        return {"real": float(obj.real), "imag": float(obj.imag)}

    if isinstance(obj, (set, frozenset, AbstractSet)):
        converted_items = [to_jsonable(item) for item in obj]
        try:
            return sorted(converted_items)
        except TypeError:
            return sorted(converted_items, key=lambda x: str(x))

    if isinstance(obj, Mapping):
        return {
            str(k): to_jsonable(v)#1
            for k, v in obj.items()
        }

    if isinstance(obj, (Sequence, deque)) and not isinstance(obj, (str, bytes, bytearray)):
        return [to_jsonable(item) for item in obj]

    if isinstance(obj, (datetime, date, time)):
        return obj.isoformat()
    if isinstance(obj, (UUID, Path)):
        return str(obj)
    if isinstance(obj, Enum):
        return to_jsonable(obj.value)
    if isinstance(obj, (bytes, bytearray)):
        return obj.decode("utf-8", errors="replace")

    if hasattr(obj, "model_dump") and callable(obj.model_dump): # pyright: ignore[reportAttributeAccessIssue]
        return to_jsonable(obj.model_dump()) # pyright: ignore[reportAttributeAccessIssue]
    if hasattr(obj, "dict") and callable(obj.dict): # pyright: ignore[reportAttributeAccessIssue]
        return to_jsonable(obj.dict()) # pyright: ignore[reportAttributeAccessIssue]

    if is_dataclass(obj) and not isinstance(obj, type):
        return to_jsonable(asdict(obj))

    if hasattr(obj, "to_dict") and callable(obj.to_dict): # pyright: ignore[reportAttributeAccessIssue]
        return to_jsonable(obj.to_dict())# pyright: ignore[reportAttributeAccessIssue]
    if hasattr(obj, "__dict__"):
        return to_jsonable(vars(obj))#2

    return str(obj)
