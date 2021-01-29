import sqlite3
from typing import Dict, List, Any
import json
from datetime import datetime


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
                version text NOT NULL,
                intent text,
                slots text,
                entities text,
                timestamp float,
                events text)
                """

        try:
            c = self.conn.cursor()
            c.execute(sql_statement)
            self.conn.commit()

        except Exception as ex:
            raise RuntimeError(f"Cannot create table 'chat_state' by error {ex}")

    def insert_table(self, user_id: str, version: str, intent: Dict[str, Any], slots: Dict[str, Any], entities: List[Dict[str, Any]], events: Dict[str, Any]):
        """
        Insert conversation state into database
        :param user_id: str - unique user identifier
        :param version: str - version of system
        :param intent: dict(name, intent_ranking, priority) - user intent
        :param slots: dict(slots_name) - dictionary of current conversation slots
        :param entities: list(dict(entity_name, text, ...)) - list of entities in user message
        :param events: dict(event: logic) - latest events in the current conversation
        :return: None
        """
        if not isinstance(user_id, str):
            raise ValueError(f"user_id must be a string not {user_id}: {type(user_id)}")

        if not isinstance(version, str):
            raise ValueError(f"version must be a string not {version}: {type(version)}")

        try:
            intent = json.dumps(intent)
            slots = json.dumps(slots)
            entities = json.dumps(entities)
            events = json.dumps(events)

        except Exception as ex:
            raise ValueError(f"Cannot convert intent/slots/entities to text format by error {ex}")

        sql_statement = f"""INSERT INTO chat_state (user_id, version, intent, slots, entities, timestamp, events) 
                            VALUES ('{user_id}', '{version}', '{intent}', '{slots}', '{entities}', {datetime.today().timestamp()}, '{events}')"""

        try:
            c = self.conn.cursor()
            c.execute(sql_statement)
            self.conn.commit()

        except Exception as ex:
            raise RuntimeError(f"Cannot insert data into table with error {ex}")

    def fetch_chat_state(self, user_id: str) -> Dict[str, Any]:
        """
        Get the conversation state of user
        :param user_id: str - unique identifier of the user
        :return: dict(id, user_id, version, intent, slots, entities, timestamp, events)
        """
        sql_statement = f"""SELECT * FROM chat_state 
                            WHERE user_id = '{user_id}'
                            ORDER BY id DESC LIMIT 1"""

        try:
            c = self.conn.cursor()
            result = c.execute(sql_statement).fetchone()

        except Exception as ex:
            raise RuntimeError(f"Cannot fetch chat state of user {user_id} by error {ex}")

        chat_state = None
        try:
            chat_state = dict(
                id=result[0],
                user_id=result[1],
                version=result[2],
                intent=json.loads(result[3]),
                slots=json.loads(result[4]),
                entities=json.loads(result[5]),
                timestamp=result[6],
                events=json.loads(result[7])
            )

        except Exception as ex:
            raise RuntimeError(f"Cannot convert intent/entities/slots from text format by error {ex}")

        return chat_state

    def fetch_user_messages(self, user_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get the user states in database.
        :param user_id: unique identifier of the user
        :param limit: number of query row
        :return: list(dict(id, user_id, version, intent, slots, entities, timestamp, events))
        """
        sql_statement = f"""SELECT * FROM chat_state 
                                    WHERE user_id = '{user_id}'
                                    ORDER BY id DESC LIMIT {limit}"""

        try:
            c = self.conn.cursor()
            result = c.execute(sql_statement).fetchall()

        except Exception as ex:
            raise RuntimeError(f"Cannot fetch chat state of user {user_id} by error {ex}")

        user_messages = []
        for row in result:
            try:
                user_messages.append(dict(
                    id=row[0],
                    user_id=row[1],
                    version=row[2],
                    intent=json.loads(row[3]),
                    slots=json.loads(row[4]),
                    entities=json.loads(row[5]),
                    timestamp=row[6],
                    events=json.loads(row[7])
                ))

            except Exception as ex:
                raise RuntimeError(f"Cannot convert intent/entities/slots from text format by error {ex}")

        return user_messages

    def fetch_all_messages(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get the messages from all user
        :param limit: number of query row
        :return: list(dict(id, user_id, version, intent, slots, entities, timestamp, events))
        """
        sql_statement = f"""SELECT * FROM chat_state ORDER BY id DESC LIMIT {limit}"""

        try:
            c = self.conn.cursor()
            result = c.execute(sql_statement).fetchall()

        except Exception as ex:
            raise RuntimeError(f"Cannot fetch chat state by error {ex}")

        messages = []
        for row in result:
            try:
                messages.append(dict(
                    id=row[0],
                    user_id=row[1],
                    version=row[2],
                    intent=json.loads(row[3]),
                    slots=json.loads(row[4]),
                    entities=json.loads(row[5]),
                    timestamp=row[6],
                    events=json.loads(row[7])
                ))

            except Exception as ex:
                raise RuntimeError(f"Cannot convert intent/entities/slots from text format by error {ex}")

        return messages
