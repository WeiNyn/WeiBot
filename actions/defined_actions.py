from actions.actions import BaseActionClass
from typing import Dict, List, Any

from parsers.event import ButtonEvent


class DefaultAction(BaseActionClass):
    """
    Action that handle 'default' intent
    """
    def __init__(self, entities_list: List[str], intents_list: List[str], slots_list: List[str]):
        super().__init__(entities_list, intents_list, slots_list)

    def name(self):
        return "default"
    
    @staticmethod
    def intent_list():
        """
        This function store the list of intent and their suggestion sentences.
        :return: dict(intent_name) - mapping for intent names and suggestion sentences.
        """
        return dict(
            WorkTimesBreaches="Work time breaches",
            WorkingTimeBreachDiscipline="Work time discipline",
            HolidaysOff="Holidays",
            AnnualLeaveApplicationProcess="Annual leave process",
            WorkingHours="Working time",
            WorkingDay="Working day",
            BreakTime="Break time",
            Pregnant="Pregnant policies",
            AttendanceRecord="Attendance checking",
            LaborContract="Labor contract",
            Recruitment="Recruitment",
            SickLeave="Sick leave",
            UnpaidLeave="Unpaid leave",
            PaidLeaveForFamilyEvent="Family events",
            UnusedAnnualLeave="Unused annual leave",
            RegulatedAnnualLeave="Regulated Annual Leave"
        )
    
    def __call__(self, intent: Dict[str, Any], entities: List[Dict[str, Any]], slots: Dict[str, Any]):
        """
        Based on the ranking of intents, suggest the most likely intent to user
        :param intent: dict(name, intent_ranking, priority) - current intent of user message
        :param entities: list(dict(entity_name, text, ...)) - current entities of user message
        :param slots: dict(slot_name) - current slots of user message
        :return: EventOutput - the output of ButtonEvent of current conversation.
        """
        text = "Sorry, I don't understand, what do you mean?"

        intent_ranking = [(self.intent_list()[key], key, value) for key, value in intent.get('intent_ranking').items() if key in self.intent_list().keys()]
        intent_ranking.sort(key=lambda x: -x[2])

        button = dict(
            text=text,
            button=[dict(
                title=x[0],
                trigger_intent=x[1]
            ) for x in intent_ranking[:5]]
        )

        button_event = ButtonEvent(button, self.entities_list, self.intents_list, self.slots_list)

        return button_event(intent, entities, slots)

