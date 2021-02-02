from typing import Dict, List, Any
from parsers.event import EventOutput


class BaseActionClass:
    """
    Base action class, all actions must inherit this class
    """
    def __init__(self, entities_list: List[str], intents_list: List[str], slots_list: List[str]):
        self.entities_list = entities_list
        self.intents_list = intents_list
        self.slots_list = slots_list

    def name(self):
        """
        Return the name of action.
        :return:
        """
        raise NotImplementedError(f"Class BaseActionClass must have name() method")

    def __call__(self, intent: Dict[str, Any], entities: List[Dict[str, Any]], slots: Dict[str, Any]) -> EventOutput:
        """
        Process the action, this is similar to Event, must return EventOutput type.
        :param intent: dict(name, intent_ranking, priority) - current intent of user message
        :param entities: list(dict(entity_name, text, ...) - current entities in user message
        :param slots: dict(slots_name) - current slots of conversation
        :return: EventOutput - event base on the current conversation state
        """
        raise NotImplementedError(f"Class BaseActionClass must have __call__() method")
