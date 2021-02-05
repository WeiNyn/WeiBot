from typing import List, Dict, Any, Union, Optional
from random import randint
import re


class EventOutput:
    """
    output of event type
    """
    def __init__(self, data: Dict[str, Any]):
        self.__dict__.update(data)

    def update(self, data: Dict[str, Any]):
        """
        Do the dictionary update
        :param data: dictionary data
        :return: None
        """
        self.__dict__.update(data)

    def append(self, data: Any):
        """
        The custom update method, which will update the inner dictionary and append the inner list
        :param data: dictionary data or EventOutput type
        :return: None
        """
        if not isinstance(data, dict):
            if isinstance(data, EventOutput):
                data = data.__dict__

            else:
                raise ValueError(f"data must be dict or EventOutput, not {data}: {type(data)}")

        dict_data = self.__dict__

        for key, value in data.items():
            if dict_data.get(key, None) is not None:
                if isinstance(value, list) and isinstance(dict_data.get(key, None), list):
                    dict_data[key] += value

                elif isinstance(value, dict) and isinstance(dict_data.get(key, None), dict):
                    dict_data[key].update(value)

            else:
                dict_data[key] = value

        self.__dict__ = dict_data


class Event:
    """
    Event type, which defines action of chatbot
    """
    def _check(self, entities_list: List[str], intents_list: List, slots_list: List[str]):
        """
        Check all attributes in the event and set up needed attributes
        :param entities_list: list of available entities
        :param intents_list: list of available intents
        :param slots_list: list of available slots
        :return: None
        """
        raise NotImplementedError(f"Event class must implement _check() method")

    def __call__(self, intent: Dict[str, Any], entities: List[Dict[str, Any]], slots: Dict[str, Any]) -> EventOutput:
        """
        Process state state and give the event base on current state of conversation
        :param intent: current intent dict(name, intent_ranking, priority)
        :param entities: list of current entities list(dict(entity_name, text, ...))
        :param slots: dictionary of current slot dict()
        :return: chatbot action as EventOutput
        """
        raise NotImplementedError(f"Event class must implement __call__() method")

    def export(self) -> Dict[str, Any]:
        """
        Export to the conversable dictionary
        :return: dict(str, Any)
        """
        raise NotImplementedError(f"Event class must implement export() method")


class TextEvent(Event):
    """
    Event that return the text message
    """
    def __init__(self, text: List[str], entities_list: List[str], intents_list: List[str], slots_list: List[str]):
        """
        Create text event from
        :param text: list(message) to select random message from this list
        :param entities_list: list of available entities
        :param intents_list: list of available intents
        :param slots_list: list of available slots
        """
        self.slot_regex = "\__[\w\s]+\__"
        self.text = text

        self.slots_to_fill = []
        for t in self.text:
            self.slots_to_fill.append(re.findall(self.slot_regex, t))

        self._check(entities_list, intents_list, slots_list)

    def _check(self, entities_list: List[str], intents_list: List, slots_list: List[str]):
        for t, slot_to_fill in zip(self.text, self.slots_to_fill):
            for slot in slot_to_fill:
                if slot[2:-2] not in slots_list:
                    raise ValueError(f"Slot {slot} is not an available slot")

        if not isinstance(self.text, list):
            raise ValueError(f"text must be a list of string, not {self.text}: {type(self.text)}")

        else:
            for t in self.text:
                if not isinstance(t, str):
                    raise ValueError(f"text must be a list of string, not {self.text}: {type(self.text)}")

    def export(self):
        return dict(
            text=self.text
        )

    def __call__(self, intent: Dict[str, Any], entities: List[Dict[str, Any]], slots: Dict[str, Any]) -> EventOutput:
        rand_idx = randint(0, len(self.text) - 1)
        text = self.text[rand_idx]
        slots_to_fill = self.slots_to_fill[rand_idx]
        for slot in slots_to_fill:
            if slot[1:-1] in slots.keys() and isinstance(slots[slot[1:-1]], str):
                text.replace(slot, slots[slot[1:-1]])

        return EventOutput(dict(
            text=text
        ))


class SetSlotEvent(Event):
    """
    Event that set slots in conversation
    """
    def __init__(self, slots: Dict, entities_list: List[str], intents_list: List[str], slots_list: List[str]):
        """
        Creat set slot event
        :param slots: Dict(slots name: set slot logic)
        :param entities_list: list of available entities
        :param intents_list: list of available intents
        :param slots_list: list of available slots
        """
        self.slots_map = slots

        self._check(entities_list, intents_list, slots_list)

    def _check(self, entities_list: List[str], intents_list: List[str], slots_list: List[str]):
        for slot_name, set_value in self.slots_map.items():
            if isinstance(set_value, str):
                continue

            if slot_name not in slots_list:
                raise ValueError(f"Slot {slot_name} is not an available slot")

            if isinstance(set_value, dict):
                from_intent = set_value.get("from_intent", None)

                if from_intent:
                    if isinstance(from_intent, bool):
                        continue

                    elif isinstance(from_intent, dict):
                        for intent_name in from_intent.keys():
                            if intent_name not in intents_list:
                                raise ValueError(f"Intent {intent_name} is not an available intent")

                    else:
                        raise ValueError(f"Only support boolean or dictionary for from_intent, not {from_intent}: {type(from_intent)}")

                    continue

                from_entity = set_value.get("from_entity", None)

                if from_entity:
                    if isinstance(from_entity, dict):
                        for entity_name, entity_value in from_entity.items():
                            if entity_name not in entities_list:
                                raise ValueError(f"Entity {entity_name} is not an available entity")

                            if not (isinstance(entity_value, str) or isinstance(entity_value, bool)):
                                ValueError(f"Only support boolean or string for entity_value, not {entity_value}: {type(entity_value)}")

                    else:
                        raise ValueError(f"Only support boolean or dictionary for from_entity, not {from_entity}: {type(from_intent)}")

    def export(self):
        return dict(
            set_slot=self.slots_map
        )

    def __call__(self, intent: Dict[str, Any], entities: List[Dict[str, Any]], slots: Dict[str, Any]) -> EventOutput:
        slot_dict = dict()

        for slot_name, set_value in self.slots_map.items():

            if isinstance(set_value, str):
                slot_dict.update({slot_name: set_value})

            if set_value is None:
                slot_dict.update({slot_name: None})

            elif isinstance(set_value, dict):
                from_intent = set_value.get("from_intent", None)

                if from_intent:
                    if isinstance(from_intent, bool):
                        slot_dict.update({slot_name: intent["name"]})

                    elif isinstance(from_intent, dict):
                        for intent_name, slot_value in from_intent.items():
                            if intent["name"] == intent_name:
                                slot_dict.update({slot_name: slot_value})
                                break

                else:
                    from_entity = set_value.get("from_entity", None)

                    for entity_name, entity_value in from_entity.items():
                        for entity in entities:
                            if entity.get("entity_name", None) == entity_name:
                                if entity_value is True:
                                    slot_dict.update({slot_name: entity.get("text")})
                                    break

                                else:
                                    slot_dict.update({slot_name: entity_value})

        return EventOutput(dict(
            set_slot=slot_dict
        ))


class RequestSlotEvent(Event):
    """
    Event that request next slot from user
    """
    def __init__(self, request_slot: str, entities_list: List[str], intents_list: List[str], slots_list: List[str]):
        """
        Create request slot event
        :param request_slot: str - the name of requested slot
        :param entities_list: list of available entities
        :param intents_list: list of available intents
        :param slots_list: list of available slots
        """
        self.request_slot = request_slot

        self._check(entities_list, intents_list, slots_list)

    def _check(self, entities_list: List[str], intents_list: List[str], slots_list: List[str]):
        if self.request_slot not in slots_list:
            raise ValueError(f"Slot {self.request_slot} is not an available slot")

    def export(self):
        return dict(
            request_slot=self.request_slot
        )

    def __call__(self, intent: Dict[str, Any], entities: List[Dict[str, Any]], slots: Dict[str, Any]) -> EventOutput:
        return EventOutput(dict(
            request_slot=self.request_slot
        ))


class TriggerIntentEvent(Event):
    """
    Intent that trigger one intent
    """
    def __init__(self, trigger_intent: Union[str, Dict[str, Any]], entities_list: List[str], intents_list: List[str], slots_list: List[str]):
        """
        Create trigger intent event
        :param trigger_intent: str - name of trigger intent/dict() the logic to select the intent name
        :param entities_list: list of available entities
        :param intents_list: list of available intents
        :param slots_list: list of available slots
        """
        self.trigger_intent = trigger_intent

        self._check(entities_list, intents_list, slots_list)

    def _check(self, entities_list: List[str], intents_list: List, slots_list: List[str]):
        if isinstance(self.trigger_intent, str):
            if self.trigger_intent not in intents_list:
                raise ValueError(f"Intent {self.trigger_intent} is not an available intent")

        elif isinstance(self.trigger_intent, dict):
            from_slot = self.trigger_intent.get("from_slot", None)

            if not from_slot:
                raise ValueError(f"Trigger intent only support fixed intent and from_slot, not {self.trigger_intent}")

            elif from_slot not in slots_list:
                raise ValueError(f"Slot {from_slot} is not an available slot")

    def export(self):
        return dict(
            trigger_intent=self.trigger_intent
        )

    def __call__(self, intent: Dict[str, Any], entities: List[Dict[str, Any]], slots: Dict[str, Any]) -> EventOutput:
        trigger_intent = None
        if isinstance(self.trigger_intent, str):
            trigger_intent = self.trigger_intent

        elif isinstance(self.trigger_intent, dict):
            from_slot = self.trigger_intent.get("from_slot", None)
            trigger_intent = slots.get(from_slot, None)

        return EventOutput(dict(
            trigger_intent=trigger_intent
        ))


class ActionEvent(Event):
    def __init__(self, action: str, entities_list: List[str], intents_list: List[str], slots_list: List[str]):
        self.action = action

    def _check(self, entities_list: List[str], intents_list: List[str], slots_list: List[str]):
        if not isinstance(self.action, str):
            raise ValueError(f"Action must be a string, not {self.action}: {type(self.action)}")

    def export(self):
        return dict(
            action=self.action
        )

    def __call__(self, intent: Dict[str, Any], entities: List[Dict[str, Any]], slots: Dict[str, Any]) -> EventOutput:
        return EventOutput(dict(
            action=self.action
        ))


class ButtonTrigger:
    """
    Trigger class that content condition and event for action_map and request_map
    """
    def __init__(self, trigger: Dict[str, Any], entities_list: List[str], intents_list: List[str],
                 slots_list: List[str]):
        """
        Create triggers
        :param trigger: dict() that contains events
        :param entities_list: list of available entities
        :param intents_list: list of available intents
        :param slots_list: list of available slots
        """
        self.trigger = trigger
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
            if key == "text":
                self.event.append(TextEvent(value, entities_list, intents_list, slots_list))

            elif key == "set_slot":
                self.event.append(SetSlotEvent(value, entities_list, intents_list, slots_list))

            elif key == "trigger_intent":
                self.event.append(TriggerIntentEvent(value, entities_list, intents_list, slots_list))

            else:
                raise ValueError(f"Only support text, trigger_intent and set_slot event, not {key}: {value}")

        if len(self.event) == 0:
            raise ValueError(f"At least one event must be specified, at {self.trigger}")

    def export(self):
        """
        export to the convertible dictionary
        :return: dict() that can be converted to current trigger
        """
        trigger = dict()

        for event in self.event:
            trigger.update(event.export())

        return trigger

    def __call__(self, intent: Dict[str, Any], entities: List[Dict[str, Any]], slots: Dict[str, Any]) -> Optional[EventOutput]:
        """
        Process the current conversation to give the event output
        :param intent: dict(name, intent_ranking, priority) - current intent of user message
        :param entities: list(dict(entity_name, text, ...) - current entities in user message
        :param slots: dict(slots_name) - current slots of conversation
        :return: EventOutput - event base on the current conversation
        """
        events = EventOutput({})

        for event in self.event:
            events.append(event(intent, entities, slots))

        return events


class ButtonEvent(Event):
    """
    Event that return an form for user
    """
    def __init__(self, button: Dict[str, Any], entities_list: List[str], intents_list: List[str], slots_list: List[str]):
        """
        Create button event with given button
        :param button: dict() - button configuration
        :param entities_list: list of available entities
        :param intents_list: list of available intents
        :param slots_list: list of available slots
        """
        self.button = button

        self._check(entities_list, intents_list, slots_list)

    def _check(self, entities_list: List[str], intents_list: List[str], slots_list: List[str]):
        if not isinstance(self.button, dict):
            raise ValueError(f"Button must be a dictionary, not {self.button}: {type(self.button)}")

        text = self.button.get("text", None)
        if not text:
            raise ValueError(f"Button must have 'text' attribute, at {self.button}")

        elif not isinstance(text, str):
            raise ValueError(f"text in button must be a string, not {text}: {type(text)}")

        button = self.button.get("button", None)
        if not button:
            raise ValueError(f"Button must have 'button' attribute, at {self.button}")

        if not isinstance(button, list):
            raise ValueError(f"button must be a list, not {button}: {type(button)}")

        self.events_map: Dict[str, ButtonTrigger] = dict()
        self.synonym_dict: Dict[str, str] = dict()
        for b in button:
            if not isinstance(b, dict):
                raise ValueError(f"button component must be a list, not {b}: {type(b)}")

            title = b.get("title", None)

            if not isinstance(title, str):
                raise ValueError(f"title must be a string, not {title}: {type(title)}")

            for key, value in b.items():
                if key not in ["title", "text", "set_slot", "trigger_intent", "synonym"]:
                    raise ValueError(f"Button only support 'text', 'set_slot', 'trigger_intent', 'synonym' not {key}")

            synonym = b.get("synonym", None)
            if synonym is not None:
                if not isinstance(synonym, list):
                    raise ValueError(f"synonym must be a list of string, not {synonym}")

                for s in synonym:
                    self.synonym_dict[s] = title

            self.events_map[title] = ButtonTrigger({k: v for k, v in b.items() if k not in ["title", "synonym"]}, entities_list, intents_list, slots_list)

    def export(self):
        return dict(button=self.button)

    def __call__(self, intent: Dict[str, Any], entities: List[Dict[str, Any]], slots: Dict[str, Any]) -> EventOutput:
        return EventOutput(dict(
            button=dict(
                text=self.button["text"],
                events_map=self.events_map,
                synonym_dict=self.synonym_dict
            )
        ))
