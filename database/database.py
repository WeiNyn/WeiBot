import json
import sqlite3
import warnings
from datetime import datetime
from typing import Dict, List, Any, Tuple


class ChatStateDB:
    """
    chat_state database for storing user chat information.
    """

    def __init__(self, db: str):
        """
        Create database object, which creates database and table  if not exists.
        :param db: path to database file.
        """
        try:
            conn = sqlite3.connect(db)
        except Exception as ex:
            raise RuntimeError(f"Cannot connect to database {db} by error {ex}")

        self.conn = conn
        self.create_table()

    def create_table(self):
        """
        Create table storing conversation state of users
        :return: None
        """
        sql_statement = """CREATE TABLE IF NOT EXISTS chat_state (
                id integer PRIMARY KEY AUTOINCREMENT,
                user_id text NOT NULL,
                user_name text NOT NULL,
                version text NOT NULL,
                intent text,
                slots text,
                entities text,
                timestamp float,
                events text,
                button text,
                loop_stack int(10),
                response text,
                synonym_dict text)
                """

        try:
            c = self.conn.cursor()
            c.execute(sql_statement)
            self.conn.commit()

        except Exception as ex:
            raise RuntimeError(f"Cannot create table 'chat_state' by error {ex}")

        sql_statement = """CREATE TABLE IF NOT EXISTS user_status (
                    id integer primary KEY AUTOINCREMENT,
                    user_id text NOT NULL,
                    user_name text NOT NULL,
                    u2u boolean,
                    timestamp float,
                    floor text
                    )"""

        try:
            c = self.conn.cursor()
            c.execute(sql_statement)
            self.conn.commit()

        except Exception as ex:
            raise RuntimeError(f"Cannot create table 'user_status' by error {ex}")

    @staticmethod
    def replace_dict():
        return {
            "'": "__single_quote__"
        }

    @staticmethod
    def revert_replace_dict():
        return {v: k for k, v in ChatStateDB.replace_dict().items()}

    @staticmethod
    def convert_dict(dict_as_string: str, dictionary: Dict[str, Any]) -> str:
        for key, value in dictionary.items():
            dict_as_string = dict_as_string.replace(key, value)

        return dict_as_string

    def dump_data(self, intent: Dict[str, Any], entities: List[Dict[str, Any]], slots: Dict[str, Any],
                  events: Dict[str, Any], button: Dict[str, Any], response: Dict[str, Any],
                  synonym_dict: Dict[str, Any]) -> Tuple:
        return (
            self.convert_dict(json.dumps(intent), dictionary=self.replace_dict()),
            self.convert_dict(json.dumps(entities), dictionary=self.replace_dict()),
            self.convert_dict(json.dumps(slots), dictionary=self.replace_dict()),
            self.convert_dict(json.dumps(events), dictionary=self.replace_dict()),
            None if not button else self.convert_dict(json.dumps(button), dictionary=self.replace_dict()),
            None if not response else self.convert_dict(json.dumps(response), dictionary=self.replace_dict()),
            None if not synonym_dict else self.convert_dict(json.dumps(synonym_dict), dictionary=self.replace_dict())
        )

    def load_data(self, intent: str, entities: str, slots: str, events: str, button: str, response: str,
                  synonym_dict: str) -> Tuple:
        return (
            json.loads(self.convert_dict(intent, dictionary=self.revert_replace_dict())),
            json.loads(self.convert_dict(entities, dictionary=self.revert_replace_dict())),
            json.loads(self.convert_dict(slots, dictionary=self.revert_replace_dict())),
            json.loads(self.convert_dict(events, dictionary=self.revert_replace_dict())),
            None if not button else json.loads(self.convert_dict(button, dictionary=self.revert_replace_dict())),
            None if not response else json.loads(self.convert_dict(response, dictionary=self.revert_replace_dict())),
            None if not synonym_dict else json.loads(
                self.convert_dict(synonym_dict, dictionary=self.revert_replace_dict())),
        )

    def insert_table(self, user_id: str, user_name: str, version: str, intent: Dict[str, Any], slots: Dict[str, Any],
                     entities: List[Dict[str, Any]], events: Dict[str, Any], button: Dict[str, Any],
                     loop_stack: int = 0, response: Dict[str, Any] = None, synonym_dict: Dict[str, Any] = None):
        """
        Insert conversation state into database
        :param user_id: str - unique user identifier
        :param user_name: str - name of user
        :param version: str - version of system
        :param intent: dict(name, intent_ranking, priority) - user intent
        :param slots: dict(slots_name) - dictionary of current conversation slots
        :param entities: list(dict(entity_name, text, ...)) - list of entities in user message
        :param events: dict(event: logic) - latest events in the current conversation
        :param button: dict() - dictionary for recreate button events_map
        :param loop_stack: int - chat state's loop stack
        :param response: dict(text, button) - response of chatbot
        :param synonym_dict: dict() - synonym dict for button
        :return: None
        """
        if not isinstance(user_id, str):
            raise ValueError(f"user_id must be a string not {user_id}: {type(user_id)}")

        if not isinstance(user_name, str):
            raise ValueError(f"user_name must be a string not {user_name}: {type(user_name)}")

        if not isinstance(version, str):
            raise ValueError(f"version must be a string not {version}: {type(version)}")

        try:
            intent, entities, slots, events, button, response, synonym_dict = self.dump_data(intent, entities, slots,
                                                                                             events, button,
                                                                                             response, synonym_dict)

        except Exception as ex:
            raise RuntimeWarning(f"Cannot convert intent/slots/entities/events/button to text format by error {ex}")

        sql_statement = f"""INSERT INTO chat_state (user_id, user_name, version, intent, slots, entities, timestamp, events, button, loop_stack, response, synonym_dict) 
                            VALUES ('{user_id}', '{user_name}', '{version}', '{intent}', '{slots}', '{entities}', {datetime.today().timestamp()}, '{events}', {("'" + button + "'") if button else "NULL"}, {loop_stack}, {"'" + response + "'" if response else "NULL"}, {"'" + synonym_dict + "'" if synonym_dict else "NULL"})"""

        try:
            c = self.conn.cursor()
            c.execute(sql_statement)
            self.conn.commit()

        except Exception as ex:
            raise RuntimeWarning(f"Cannot insert data into table with error {ex}")

        user_status = self.get_user_status(user_id=user_id)

        if not user_status:
            self.change_user_status(user_id=user_id, user_name=user_name, u2u=False, floor="not set")

    def fetch_chat_state(self, user_id: str) -> Dict[str, Any]:
        """
        Get the conversation state of user
        :param user_id: str - unique identifier of the user
        :return: dict(id, user_id, version, intent, slots, entities, timestamp, events, button, loop_stack, response, synonym_dict)
        """
        sql_statement = f"""SELECT * FROM chat_state 
                            WHERE user_id = '{user_id}'
                            ORDER BY id DESC LIMIT 1"""

        try:
            c = self.conn.cursor()
            result = c.execute(sql_statement).fetchone()

        except Exception as ex:
            result = None
            warnings.warn(f"Cannot fetch chat state of user {user_id} by error {ex}")

        chat_state = None
        try:
            intent, entities, slots, events, button, response, synonym_dict = self.load_data(result[4], result[6],
                                                                                             result[5],
                                                                                             result[8], result[9],
                                                                                             result[11], result[12])
            chat_state = dict(
                id=result[0],
                user_id=result[1],
                user_name=result[2],
                version=result[3],
                intent=intent,
                slots=slots,
                entities=entities,
                timestamp=result[7],
                events=events,
                button=button,
                loop_stack=result[10],
                response=response,
                synonym_dict=synonym_dict
            )

        except Exception as ex:
            warnings.warn(f"Cannot convert intent/entities/slots from text format by error {ex}")

        return chat_state

    def fetch_user_messages(self, user_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get the user states in database.
        :param user_id: unique identifier of the user
        :param limit: number of query row
        :return: list(dict(id, user_id, version, intent, slots, entities, timestamp, events, button, loop_stack, response))
        """
        sql_statement = f"""SELECT * FROM chat_state 
                                    WHERE user_id = '{user_id}'
                                    ORDER BY id DESC LIMIT {limit}"""

        try:
            c = self.conn.cursor()
            result = c.execute(sql_statement).fetchall()

        except Exception as ex:
            result = None
            warnings.warn(f"Cannot fetch chat state of user {user_id} by error {ex}")

        user_messages = []
        for row in result:
            try:
                intent, entities, slots, events, button, response, synonym_dict = self.load_data(row[4], row[6], row[5],
                                                                                                 row[8], row[9],
                                                                                                 row[11], row[12])
                user_messages.append(dict(
                    id=row[0],
                    user_id=row[1],
                    user_name=row[2],
                    version=row[3],
                    intent=intent,
                    slots=slots,
                    entities=entities,
                    timestamp=row[7],
                    events=events,
                    button=button,
                    loop_stack=row[10],
                    response=response,
                    synonym_dict=synonym_dict
                ))

            except Exception as ex:
                warnings.warn(f"Cannot convert intent/entities/slots from text format by error {ex}")

        return user_messages

    def fetch_all_messages(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get the messages from all user
        :param limit: number of query row
        :return: list(dict(id, user_id, version, intent, slots, entities, timestamp, events, button, loop_stack, response))
        """
        sql_statement = f"""SELECT * FROM chat_state ORDER BY id DESC LIMIT {limit}"""

        try:
            c = self.conn.cursor()
            result = c.execute(sql_statement).fetchall()

        except Exception as ex:
            result = 0
            warnings.warn(f"Cannot fetch chat state by error {ex}")

        messages = []
        for row in result:
            try:
                intent, entities, slots, events, button, response, synonym_dict = self.load_data(row[4], row[6], row[5],
                                                                                                 row[8], row[9],
                                                                                                 row[11], row[12])
                messages.append(dict(
                    id=row[0],
                    user_id=row[1],
                    user_name=row[2],
                    version=row[3],
                    intent=intent,
                    slots=slots,
                    entities=entities,
                    timestamp=row[7],
                    events=events,
                    button=button,
                    loop_stack=row[10],
                    response=response,
                    synonym_dict=synonym_dict
                ))

            except Exception as ex:
                warnings.warn(f"Cannot convert intent/entities/slots from text format by error {ex}")

        return messages

    def fetch_users(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get the latest state of number of users

        :param limit: number of user to fetch
        :return: list(dict(id, user_id, version, intent, slots, entities, timestamp, events, button, loop_stack, response))
        """
        sql_statement = f"""SELECT MAX(id) AS [id], user_id, version, intent, slots, entities, timestamp, events, button
                            FROM chat_state
                            GROUP BY user_id
                            LIMIT {limit}"""

        try:
            c = self.conn.cursor()
            result = c.execute(sql_statement).fetchall()

        except Exception as ex:
            warnings.warn(f"Cannot fetch users state by error {ex}")
            result = []

        messages = []
        for row in result:
            try:
                intent, entities, slots, events, button, response, synonym_dict = self.load_data(row[4], row[6], row[5],
                                                                                                 row[8], row[9],
                                                                                                 row[11], row[12])
                messages.append(dict(
                    id=row[0],
                    user_id=row[1],
                    user_name=row[2],
                    version=row[3],
                    intent=intent,
                    slots=slots,
                    entities=entities,
                    timestamp=row[7],
                    events=events,
                    button=button,
                    loop_stack=row[10],
                    response=response,
                    synonym_dict=synonym_dict
                ))

            except Exception as ex:
                warnings.warn(f"Cannot convert intent/entities/slots/events/button from text format by error {ex}")

        return messages

    def get_user_status(self, user_id) -> Dict[str, Any]:
        sql_statement = f"""SELECT * FROM user_status 
                                    WHERE user_id = '{user_id}'
                                    ORDER BY id DESC LIMIT 1"""

        try:
            c = self.conn.cursor()
            result = c.execute(sql_statement).fetchone()

        except Exception as ex:
            result = None
            warnings.warn(f"Cannot fetch status of user {user_id} by error {ex}")

        status = None
        try:
            status = dict(
                id=result[0],
                user_id=result[1],
                user_name=result[2],
                u2u=result[3],
                timestamp=result[4],
                floor=result[5]
            )

        except Exception as ex:
            warnings.warn(f"Cannot convert user status {ex}")

        return status

    def change_user_status(self, user_id: str, user_name: str, u2u: bool, floor: str):
        current_status = self.get_user_status(user_id=user_id)

        if not current_status:
            sql_statement = f"""INSERT INTO user_status (user_id, user_name, u2u, timestamp, floor) VALUES ('{user_id}', '{user_name}', {"TRUE" if u2u else "FALSE"}, {datetime.today().timestamp()}, '{floor}')"""

        else:
            sql_statement = f"""UPDATE user_status SET user_name = '{user_name}', u2u = {"TRUE" if u2u else "FALSE"}, timestamp = {datetime.today().timestamp()}, floor = '{floor}' WHERE user_id = '{user_id}'"""

        try:
            c = self.conn.cursor()
            c.execute(sql_statement)
            self.conn.commit()

        except Exception as ex:
            raise RuntimeWarning(f"Cannot insert data into table with error {ex}")

    def fetch_arm_status(self) -> List[Dict[str, Any]]:
        """
        Get the user states in database.
        :param user_id: unique identifier of the user
        :param limit: number of query row
        :return: list(dict(id, user_id, version, intent, slots, entities, timestamp, events, button, loop_stack, response))
        """
        sql_statement = f"""SELECT * FROM user_status"""

        try:
            c = self.conn.cursor()
            result = c.execute(sql_statement).fetchall()

        except Exception as ex:
            result = None
            warnings.warn(f"Cannot fetch arm status of user {user_id} by error {ex}")

        arm_statuses = []
        for row in result:
            try:
                arm_statuses.append(dict(
                    id=row[0],
                    user_id=row[1],
                    user_name=row[2],
                    u2u=row[3],
                    timestamp=row[4],
                    floor=row[5]
            ))

            except Exception as ex:
                warnings.warn(f"Cannot convert arm status format by error {ex}")

        return arm_statuses
