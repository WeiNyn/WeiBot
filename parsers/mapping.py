from typing import Dict, Any, Optional, List
from parsers.condition import Condition, SlotCondition, EntityCondition, IntentCondition
from parsers.event import Event, TextEvent, SetSlotEvent, RequestSlotEvent, TriggerIntentEvent, EventOutput, ButtonEvent

ConditionMap = {
    "slot": SlotCondition,
    "entity": EntityCondition,
    "intent": IntentCondition
}

EventMap = {
    "text": TextEvent,
    "button": ButtonEvent,
    "set_slot": SetSlotEvent,
    "request_slot": RequestSlotEvent,
    "trigger_intent": TriggerIntentEvent,
}


class Trigger:
    """
    Trigger class that content condition and event for action_map and request_map
    """
    def __init__(self, trigger: Dict[str, Any], entities_list: List[str], intents_list: List[str],
                 slots_list: List[str]):
        """
        Create triggers
        :param trigger: dict() that content conditions and events
        :param entities_list: list of available entities
        :param intents_list: list of available intents
        :param slots_list: list of available slots
        """
        self.trigger = trigger
        self.condition: List[Condition] = []
        self.event: List[Event] = []
        self._check(entities_list, intents_list, slots_list)

    def _check(self, entities_list: List[str], intents_list: List[str], slots_list: List[str]):
        """
        Validate given triggers and create all needed attributes.
        :param entities_list: list of available entities
        :param intents_list: list of available intents
        :param slots_list: list of available slots
        :return: None
        """
        if not isinstance(self.trigger, dict):
            raise ValueError(f"trigger must be an dictionary, not {self.trigger}: {type(self.trigger)}")

        for key, value in self.trigger.items():
            condition = ConditionMap.get(key, None)
            if condition:
                self.condition.append(condition(value, entities_list, intents_list, slots_list))
                continue

            event = EventMap.get(key, None)
            if event:
                self.event.append(event(value, entities_list, intents_list, slots_list))
                continue

            raise ValueError(f"only support defined conditions and events, at {self.trigger}")

        if len(self.event) == 0:
            raise ValueError(f"At least one event must be specified, at {self.trigger}")

    def export(self):
        """
        export to the convertible dictionary
        :return: dict() that can be converted to current trigger
        """
        trigger = dict()
        for condition in self.condition:
            trigger.update(condition.export())

        for event in self.event:
            trigger.update(event.export())

        return trigger

    def __call__(self, intent: Dict[str, Any], entities: List[Dict[str, Any]], slots: Dict[str, Any]) -> Optional[EventOutput]:
        """
        Process the current conversation to check condition and give the event output
        :param intent: dict(name, intent_ranking, priority) - current intent of user message
        :param entities: list(dict(entity_name, text, ...) - current entities in user message
        :param slots: dict(slots_name) - current slots of conversation
        :return: EventOutput - event base on the current conversation
        """
        for condition in self.condition:
            if condition(intent, entities, slots) is False:
                return None

        events = EventOutput({})

        for event in self.event:
            events.append(event(intent, entities, slots))

        return events


class ActionMap:
    """
    Action that will be raise base on the current intent
    """
    def __init__(self, action_map: Dict[str, Any], entities_list: List[str], intents_list: List, slots_list: List[str]):
        """
        Create action map base on give dictionary
        :param action_map: dict(intent, set, set_slot, triggers) - config dictionary for action_map
        :param entities_list: list of available entities
        :param intents_list: list of available intents
        :param slots_list: list of available slots
        """
        self.action_map: Dict[str, Any] = action_map
        self.priority: int = 1
        self.slot_to_set: Optional[SetSlotEvent] = None
        self.set_slot: Optional[SetSlotEvent] = None
        self.triggers: List[Trigger] = []

        self._check(entities_list, intents_list, slots_list)

    def _check(self, entities_list: List[str], intents_list: List, slots_list: List[str]):
        """
        Validate the given config and setup needed attributes
        :param entities_list: list of available entities
        :param intents_list: list of available intents
        :param slots_list: list of available slots
        :return: None
        """
        intent = self.action_map.get("intent", None)
        priority = self.action_map.get("priority", 1)
        triggers = self.action_map.get("triggers", None)
        slot_to_set = self.action_map.get("set", None)
        set_slot = self.action_map.get("set_slot", None)

        if not intent:
            raise ValueError(f"intent should be defined in action_map, at {self.action_map}")

        else:
            if intent not in intents_list:
                raise ValueError(f"Intent {intent} is not an available intent")
            else:
                self.intent = intent

        if not triggers:
            raise ValueError(f"triggers should be defined in action_map (in intent {self.intent})")

        else:
            if not isinstance(triggers, list):
                raise ValueError(f"triggers must be a list of combinations of conditions and events, not {triggers}: {type(triggers)}")

            self.triggers: List[Trigger] = []
            for trigger in triggers:
                self.triggers.append(Trigger(trigger, entities_list, intents_list, slots_list))

        self.priority = priority

        if slot_to_set:
            self.slot_to_set = SetSlotEvent(slot_to_set, entities_list, intents_list, slots_list)

        if set_slot:
            self.set_slot = SetSlotEvent(set_slot, entities_list, intents_list, slots_list)

    def export(self):
        """
        Export the action_map to convertible dictionary
        :return: dict() that can create the same action_map
        """
        action_map = dict()
        action_map["intent"] = self.intent
        action_map["priority"] = self.priority

        if self.slot_to_set is not None:
            action_map["set"] = self.slot_to_set.export()["set_slot"]

        if self.set_slot is not None:
            action_map["set_slot"] = self.set_slot.export()["set_slot"]

        action_map["triggers"] = [trigger.export() for trigger in self.triggers]

        return action_map

    def __call__(self, intent: Dict[str, Any], entities: List[Dict[str, Any]], slots: Dict[str, Any]):
        """
        Process action_map base on current conversation state
        :param intent: dict(name, intent_ranking, priority) - current intent of user message
        :param entities: list(dict(entity_name, text, ...) - current entities in user message
        :param slots: dict(slots_name) - current slots of conversation
        :return: EventOutput - event base on the conversation state and action_map's config
        """
        intent["priority"] = self.priority

        events = EventOutput({})

        if self.slot_to_set:
            slot_to_set = self.slot_to_set(intent, entities, slots)
            slots.update(slot_to_set.set_slot)
            events.append(slot_to_set)

        if self.set_slot:
            set_slot = self.set_slot(intent, entities, slots)
            slots.update(set_slot.set_slot)
            events.append(set_slot)

        for trigger in self.triggers:
            event = trigger(intent, entities, slots)
            if event:
                events.append(event)
                return events

        return events


class RequestMap:
    """
    Request map that trigger when slot is requested
    """
    def __init__(self, request_map: Dict[str, Any], entities_list: List[str], intents_list: List[str],
                 slots_list: List[str]):
        """
        Create request map base on config
        :param request_map: dict(set, set_slot, text, redirect) - dictionary for creating request map
        :param entities_list: list of available entities
        :param intents_list: list of available intents
        :param slots_list: list of available slots
        """
        self.request_map: Dict[str, Any] = request_map
        self.slot: str = ""
        self.set_slot: Optional[SetSlotEvent] = None
        self.text: Optional[TextEvent] = None
        self.triggers: List[Trigger] = []

        self._check(entities_list, intents_list, slots_list)

    def _check(self, entities_list: List[str], intents_list: List[str], slots_list: List[str]):
        """
        Validate all the given config and create needed attributes
        :param entities_list: list of available entities
        :param intents_list: list of available intents
        :param slots_list: list of available slots
        :return: None
        """
        slot = self.request_map.get("slot", None)
        set_slot = self.request_map.get("set_slot", None)
        text = self.request_map.get("text", None)
        button = self.request_map.get("button", None)
        redirect = self.request_map.get("redirect", None)

        if not slot:
            raise ValueError(f"slot should be defined in request_map, at self.request_map")

        elif not isinstance(slot, str):
            raise ValueError(f"slot must be a string, not {slot}: {type(slot)}")

        elif slot not in slots_list:
            raise ValueError(f"Slot {slot} is not an available slot")

        else:
            self.slot = slot

        if set_slot is not None:
            self.set_slot = SetSlotEvent(set_slot, entities_list, intents_list, slots_list)

        self.startup_condition = SlotCondition({
            self.slot: False,
            "request_slot": False
        }, entities_list, intents_list, slots_list)

        self.startup_set_slot = SetSlotEvent(dict(request_slot=self.slot), intents_list, entities_list, slots_list)

        if text is not None:
            self.text = TextEvent(text, entities_list, intents_list, slots_list)

        elif button is not None:
            self.button = ButtonEvent(button, intents_list, intents_list, slots_list)

        if redirect is None:
            raise ValueError(f"redirect should be defined in request_map (at {self.slot})")

        else:
            self.triggers: List[Trigger] = []
            for trigger in redirect:
                self.triggers.append(Trigger(trigger, entities_list, intents_list, slots_list))

    def export(self):
        """
        export to the convertible dictionary
        :return: dict() - the dictionary that can be converted to current request map
        """
        request_map = dict()
        request_map["slot"] = self.slot

        if self.set_slot:
            request_map["set_slot"] = self.set_slot.export()["set_slot"]

        if self.text:
            request_map["text"] = self.text.export()["text"]
        else:
            request_map["button"] = self.button.export()["button"]

        request_map["redirect"] = [trigger.export() for trigger in self.triggers]

        return request_map

    def __call__(self, intent: Dict[str, Any], entities: List[Dict[str, Any]], slots: Dict[str, Any]):
        """
        Process the request slot base on current conversation state
        :param intent: dict(name, intent_ranking, priority) - current intent of user message
        :param entities: list(dict(entity_name, text, ...) - current entities in user message
        :param slots: dict(slots_name) - current slots of conversation
        :return: EventOutput - event base on the current conversation
        """
        events = EventOutput({})

        if self.set_slot:
            set_slot = self.set_slot(intent, entities, slots)
            slots.update(set_slot.set_slot)
            events.append(set_slot)

        if self.startup_condition(intent, entities, slots) is True:
            if self.text:
                text_event = self.text(intent, entities, slots)
                events.append(text_event)
            else:
                button_event = self.button(intent, entities, slots)
                events.append(button_event)

            set_slot_event = self.startup_set_slot(intent, entities, slots)
            events.append(set_slot_event)

            return events

        for trigger in self.triggers:
            event = trigger(intent, entities, slots)
            if event:
                events.append(event)
                return events

        return events


