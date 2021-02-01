from actions.actions import BaseActionClass
from typing import Dict, List, str, Any


class DefaultAction(BaseActionClass):
    def name(self):
        return "default"
    
    @staticmethod
    def intent_list():
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
        text = "Sorry, I don't understand, what do you mean?"

        intent_ranking = [(key, value) for key, value in intent.get('intent_ranking').items()]
        intent_ranking.sort(lambda x: x[0])

