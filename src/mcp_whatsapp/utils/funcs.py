
import json
import operator
import os
import random
from asyncio import sleep
from collections import deque
from collections.abc import Callable, Coroutine, Iterable, Mapping, Sequence
from collections.abc import Set as AbstractSet
from dataclasses import asdict, is_dataclass
from datetime import date, datetime, time
from enum import Enum
from functools import reduce
from inspect import isfunction
from itertools import groupby, zip_longest
from pathlib import Path
from typing import Any, TypeVar
from uuid import UUID

from tqdm import tqdm

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
        return sorted(listObj, key=lambda x:x if not x is None else 0)
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
    if isinstance(val, (float)):
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
    
def search(arr, element):
    for i, arr_item in enumerate(arr):
        if arr_item == element:
            return i
    return -1
    
    
def to_value(element):
    if isinstance(element, Sequence) and len(element) == 1 and not isinstance(element, str):
        return to_value(element[0])
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


def exclude(m, exclude):
    return list(set(m) - set(exclude))

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


def is_in_container():
    return os.path.exists('/.dockerenv')


class ProgressiveTryError(Exception):
    pass


async def progresive_try(func: Callable[[], Coroutine[None, None, T]], n_tries, max_s = 60, base = 4,  error_type = Exception):
    error = None
    for i in range(n_tries):
        try:
            return await func()
        except error_type as e:
            s = abs(min(base**(i+1), max_s) + random.normalvariate(0, base))
            tqdm.write(f"[progresive_try] Error: {e}. Retrying...({s}s)")
            error = e
            await sleep(s)
    
    raise ProgressiveTryError(f"[progresive_try] Failed {n_tries} times.") from error