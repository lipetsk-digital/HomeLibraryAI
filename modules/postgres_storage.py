from typing import Any, Dict, Optional
import jsonpickle
import asyncpg
from aiogram.fsm.state import State
from aiogram.fsm.storage.base import BaseStorage, StateType, StorageKey

class PostgresStorage(BaseStorage):
    """
    Asynchronous storage based on PostgreSQL database for aiogram python library.

    Usage:

    pgstorage = PGStorage(host='localhost', port=5432, database='aiogram_fsm', user='bot', password='password')
    dp = Dispatcher(bot, storage=pgstorage)
    """

    # Constructor of PostgresStorage object. Remember database connection parameters
    def __init__(self, user: str, password: str, database: str, host='localhost', port=5432):
        self._host = host
        self._port = port
        self.database: str = database
        self.user = user
        self._password = password
        self._db = None # internal field for asyncpg.Connection

    # Connect to the database and create tables if they do not exist. 
    # Return existing connection if it is open
    async def get_db(self) -> asyncpg.Connection:
        if isinstance(self._db, asyncpg.Connection):
            return self._db
        self._db = await asyncpg.connect(
            user=self.user,
            password=self._password,
            host=self._host,
            port=self._port,
            database=self.database
        )
        await self._db.execute("""CREATE TABLE IF NOT EXISTS "aiogram_states"(
                                        "chat_id" BIGINT NOT NULL,
                                        "user_id" BIGINT NOT NULL,
                                        "state" TEXT,
                                        PRIMARY KEY ("chat_id", "user_id"))""")
        await self._db.execute("""CREATE TABLE IF NOT EXISTS "aiogram_data"(
                                    "chat_id" BIGINT NOT NULL,
                                    "user_id" BIGINT NOT NULL,
                                    "data" JSON,
                                    PRIMARY KEY ("chat_id", "user_id"))""")
        jsonpickle.set_preferred_backend('json')
        jsonpickle.set_encoder_options('json', ensure_ascii=False)
        return self._db

    # Destructor of PostgresStorage object. Close database connection if it is open
    async def close(self):
        if isinstance(self._db, asyncpg.Connection):
            await self._db.close()

    #async def wait_closed(self):
    #    return True

    # Save current state into database (or delete if state is undefined)
    async def set_state(self, key: StorageKey, state: StateType = None) -> None:
        _state = state.state if isinstance(state, State) else state
        db = await self.get_db()
        if _state is None:
            await db.execute("""DELETE FROM "aiogram_states" WHERE chat_id=$1 AND "user_id"=$2""", key.chat_id, key.user_id)
        else:
            await db.execute("""INSERT INTO "aiogram_states" VALUES($1, $2, $3)"""
                             """ON CONFLICT ("user_id", "chat_id") DO UPDATE SET "state" = $3""",
                             key.chat_id, key.user_id, _state)

    # Read current state from database (or None if state is undefined)
    async def get_state(self, key: StorageKey) -> Optional[str]:
        db = await self.get_db()
        result = await db.fetchval("""SELECT "state" FROM "aiogram_states" WHERE "chat_id"=$1 AND "user_id"=$2""", key.chat_id, key.user_id)
        return result if result else None

    # Save JSON-serialized data into database, or delete if data is empty
    async def set_data(self, key: StorageKey, data: Dict[str, Any]) -> None:
        db = await self.get_db()
        if not data:
            await db.execute("""DELETE FROM "aiogram_data" WHERE "chat_id"=$1 AND "user_id"=$2""", key.chat_id, key.user_id)
        else:
            await db.execute("""INSERT INTO "aiogram_data" VALUES($1, $2, $3)"""
                             """ON CONFLICT ("user_id", "chat_id") DO UPDATE SET "data" = $3""",
                             key.chat_id, key.user_id, jsonpickle.encode(data))

    # Retrieve and deserialize (from JSON) data from database, or return empty dict if no data found
    async def get_data(self, key: StorageKey) -> Dict[str, Any]:
        db = await self.get_db()
        result = await db.fetchval("""SELECT "data" FROM "aiogram_data" WHERE "chat_id"=$1 AND "user_id"=$2""", key.chat_id, key.user_id)
        return jsonpickle.decode(result) if result else {}