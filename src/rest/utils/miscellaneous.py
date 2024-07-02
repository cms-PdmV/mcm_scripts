"""
Other operations that spread to several
topics and intentions.
"""

import pprint
import random
from copy import deepcopy


def pformat(obj) -> str:
    """
    Pretty print an object in console
    """
    return pprint.pformat(obj, width=50, compact=True)


def shuffle_pick(collection: list[dict], size: int, attribute: str = "") -> list:
    """
    Given a list of objects, shuffles the collection and picks
    the requested attribute only for a subset of `size` elements.

    Args:
        collection: List of objects.
        size: Subset size.
        attribute: Attribute to pick from the objects, it is assumed
            all objects in the collection include it. In case it
            is not provided, the content of the whole object will
            be returned.

    Returns:
        A subset of the original collection, including only the requested
            attribute.

    Raises:
        KeyError: In case the request key is not available in the collection's
            element.
    """
    elements = deepcopy(collection)
    subset_len = min(size, len(elements))
    random.shuffle(elements)
    subset = elements[:subset_len]

    if not attribute:
        return subset

    return [el[attribute] for el in subset]
