from typing import Dict, List, Any
from parsers.event import EventOutput


class BaseActionClass:
    def __init__(self):
        pass

    def name(self):
        raise NotImplementedError(f"Class BaseActionClass must have name() method")

    def __call__(self, intent: Dict[str, Any], entities: List[Dict[str, Any]], slots: Dict[str, Any]) -> EventOutput:
        raise NotImplementedError(f"Class BaseActionClass must have __call__() method")
