from abc import ABC, abstractmethod
import math
from typing import Any, Dict, Union
from .undefined import UNDEFINED
from ..client import WebElement


class ClassicSerializable(ABC):
    """Interface for the objects that can be serialized to the WebDriver classic protocol."""

    @abstractmethod
    def to_classic_protocol_value(self) -> Dict:
        """Return the object representing reference in WebDriver classic format."""
        pass


class BidiNode(ClassicSerializable):
    bidi_value: Dict[str, Any]
    shared_id: str

    def __init__(self, bidi_value: Dict[str, Any]):
        assert bidi_value["type"] == "node"
        self.bidi_value = bidi_value
        self.shared_id = bidi_value["sharedId"]

    def to_classic_protocol_value(self) -> Dict:
        return {WebElement.identifier: self.shared_id}


class BidiWindow:
    def __init__(self, bidi_value: Dict[str, Any]):
        assert bidi_value["type"] == "window"
        self.bidi_value = bidi_value

    def browsing_context(self) -> str:
        return self.bidi_value["value"]["context"]

def bidi_deserialize(bidi_value: Union[str, int, Dict]):
    """
    Deserialize the BiDi primitive values, lists and objects to the Python value, keeping non-common data types
    in BiDi format.
    Note: there can be some uncertainty in the deserialized value. Eg `{window: {context: "abc"}}` can represent a
    window proxy, or the JS object `{window: {context: "abc"}}`.
    """
    # script.PrimitiveProtocolValue https://w3c.github.io/webdriver-bidi/#type-script-PrimitiveProtocolValue
    if isinstance(bidi_value, str):
        return bidi_value
    if isinstance(bidi_value, int):
        return bidi_value
    if not isinstance(bidi_value, dict):
        raise ValueError("Unexpected bidi value: %s" % bidi_value)
    if bidi_value["type"] == "undefined":
        return UNDEFINED
    if bidi_value["type"] == "null":
        return None
    if bidi_value["type"] == "string":
        return bidi_value["value"]
    if bidi_value["type"] == "number":
        if bidi_value["value"] == "NaN":
            return math.nan
        if bidi_value["value"] == "-0":
            return -0.0
        if bidi_value["value"] == "Infinity":
            return math.inf
        if bidi_value["value"] == "-Infinity":
            return -math.inf
        if isinstance(bidi_value["value"], int) or isinstance(bidi_value["value"], float):
            return bidi_value["value"]
        raise ValueError("Unexpected bidi value: %s" % bidi_value)
    if bidi_value["type"] == "boolean":
        return bool(bidi_value["value"])
    if bidi_value["type"] == "bigint":
        # Python handles big integers natively.
        return int(bidi_value["value"])
    # script.RemoteValue https://w3c.github.io/webdriver-bidi/#type-script-RemoteValue
    if bidi_value["type"] == "array":
        result = []
        for item in bidi_value["value"]:
            result.append(bidi_deserialize(item))
        return result
    if bidi_value["type"] == "object":
        result = {}
        for item in bidi_value["value"]:
            result[bidi_deserialize(item[0])] = bidi_deserialize(item[1])
        return result
    if bidi_value["type"] == "node":
        return BidiNode(bidi_value)
    if bidi_value["type"] == "window":
        return BidiWindow(bidi_value)
    # TODO: do not raise after verified no regressions in the tests.
    raise ValueError("Unexpected bidi value: %s" % bidi_value)
    # # All other types are not deserialized and returned as-is.
    # # TODO: deserialize `date`, `regexp`, `map` and `set` types if needed.
    # return bidi_value
