from typing import Dict, Any, List


class Condition:
    """
    Condition type, which defined condition to trigger event
    """
    def _check(self, entities_list: List[str], intents_list: List, slots_list: List[str]):
        """
        Check all attributes in the condition and set up needed attributes
        :param entities_list: list of available entities
        :param intents_list: list of available intents
        :param slots_list: list of available slots
        :return: None
        """
        raise NotImplementedError(f"Condition class must implement _check() method")

    def __call__(self, intent: Dict[str, Any], entities: List[Dict[str, Any]], slots: Dict[str, Any]):
        """
        Process state state and give the true/false condition base on current state of conversation
        :param intent: current intent dict(name, intent_ranking, priority)
        :param entities: list of current entities list(dict(entity_name, text, ...))
        :param slots: dictionary of current slot dict()
        :return: true/false
        """
        raise NotImplementedError(f"Condition class must implement __call__() method")

    def export(self):
        """
        Export to the conversable dictionary
        :return: dict(str, Any)
        """
        raise NotImplementedError(f"Condition class must implement export() method")


class SlotCondition(Condition):
    """
    Condition that base on set slot in conversation
    """
    def __init__(self, slot: Dict[str, Any], entities_list: List[str], intents_list: List[str], slots_list: List[str]):
        """
        Creat slot condition
        :param slot: dict() logic for checking slot condition
        :param entities_list: list of available entities
        :param intents_list: list of available intents
        :param slots_list: list of available slots
        """
        self.slot = slot

        self._check(entities_list, intents_list, slots_list)

    def _check(self, entities_list: List[str], intents_list: List[str], slots_list: List[str]):
        if not isinstance(self.slot, dict):
            raise ValueError(f"slot condition must be a dictionary, not {self.slot}: {type(self.slot)}")

        for slot_name, slot_value in self.slot.items():
            if slot_name not in slots_list:
                raise ValueError(f"Slot {slot_name} is not an available slot")

    def export(self) -> Dict[str, Any]:
        return dict(
            slot=self.slot
        )

    def __call__(self, intent: Dict[str, Any], entities: List[Dict[str, Any]], slots: Dict[str, Any]):
        condition_check = True
        for slot_name, slot_value in self.slot.items():
            if slot_value is True:
                if slots.get(slot_name, None) is None:
                    condition_check = False
                    return condition_check

            elif slot_value is False:
                if slots.get(slot_name, None) is not None:
                    condition_check = False
                    return condition_check

            else:
                current_slot_value = slots.get(slot_name, None)
                if not current_slot_value or slot_value != current_slot_value:
                    condition_check = False
                    return condition_check

        return condition_check


class EntityCondition(Condition):
    """
    Condition that based on entity in the user message
    """
    def __init__(self, entity: Dict[str, Any], entity_list: List[str], intents_list: List[str], slots_list: List[str]):
        """
        Create entity condition
        :param entity: logic for checking entity condition
        :param entities_list: list of available entities
        :param intents_list: list of available intents
        :param slots_list: list of available slots
        """
        self.entity = entity

        self._check(entity_list, intents_list, slots_list)

    def _check(self, entities_list: List[str], intents_list: List, slots_list: List[str]):
        if not isinstance(self.entity, dict):
            raise ValueError(f"Only support dictionary entity, not {self.entity}: {type(self.entity)}")

        for entity_name, entity_value in self.entity.items():
            if entity_name not in entities_list:
                raise ValueError(f"Entity {entity_name} is not an available entity")

            if not (isinstance(entity_value, str) or isinstance(entity_value, bool)):
                raise ValueError(f"Only support string or boolean for entity_value, not {entity_value}: {type(entity_name)}")

    def export(self):
        return dict(
            entity=self.entity
        )

    def __call__(self, intent: Dict[str, Any], entities: List[Dict[str, Any]], slots: Dict[str, Any]):
        check_condition = True
        for entity_name, entity_value in self.entity.items():
            for entity in entities:
                if entity.get("entity_name") == entity_name:
                    if entity_value is False:
                        check_condition = False
                        break

                    elif entity_value != entity.get("text"):
                        check_condition = False
                        break

            if check_condition is False:
                break

        return check_condition


class IntentCondition(Condition):
    """
    Condition that based on intent of user message
    """
    def __init__(self, intent: Dict[str, Any], entities_list: List[str], intents_list: List[str], slots_list: List[str]):
        """
        Create intent condition
        :param intent: logic for checking intent condition
        :param entities_list: list of available entities
        :param intents_list: list of available intents
        :param slots_list: list of available slots
        """
        self.intent = intent

        self._check(entities_list, intents_list, slots_list)

    def _check(self, entities_list: List[str], intents_list: List, slots_list: List[str]):
        if not isinstance(self.intent, dict):
            raise ValueError(f"Only support dictionary type for intent condition, not {self.intent}: {type(self.intent)}")

        for check_type, check_value in self.intent.items():
            if check_type == "intent_name":
                if check_value not in intents_list:
                    raise ValueError(f"Intent {check_value} is not an available intent")

            elif check_type == "priority":
                if not isinstance(check_value, int):
                    raise ValueError(f"priority must be integer, not {check_value}: {type(check_value)}")

    def export(self):
        return dict(
            intent=self.intent
        )

    def __call__(self, intent: Dict[str, Any], entities: List[Dict[str, Any]], slots: Dict[str, Any]):
        check_condition = True

        for check_type, check_value in self.intent.items():
            if check_type == "intent_name":
                if intent != check_value:
                    check_condition = False
                    return check_condition

            elif check_type == "priority":
                if intent["priority"] > check_value:
                    check_condition = False
                    return check_condition

        return check_condition
