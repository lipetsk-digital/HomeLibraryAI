# PostgreSQL storage library for maxapi's FSM (finite state machine)

from typing import Any, Dict, Optional, Union
import json
import asyncpg
from maxapi.context import MemoryContext, State
from maxapi import Dispatcher


# Global storage instance that holds database connection
class PostgresStorage:
    """
    Global storage manager for PostgreSQL database connections.
    
    This class manages the database connection pool and provides
    PostgresContext instances for each user.
    
    Usage:
    
    # Initialize once at application startup
    storage = PostgresStorage(
        host='localhost', 
        port=5432, 
        database='maxapi_fsm', 
        user='bot', 
        password='password'
    )
    
    # Initialize connection and create tables
    await storage.init()
    
    # In dispatcher setup, pass storage to context factory
    dp = Dispatcher(context_factory=storage.create_context)
    
    # Close connection on shutdown
    await storage.close()
    """

    def __init__(
        self, 
        user: str, 
        password: str, 
        database: str, 
        host='localhost', 
        port=5432,
        min_pool_size=10,
        max_pool_size=50
    ):
        """
        Args:
            user: PostgreSQL user
            password: PostgreSQL password
            database: Database name
            host: Database host (default: localhost)
            port: Database port (default: 5432)
            min_pool_size: Minimum number of connections in pool (default: 10)
            max_pool_size: Maximum number of connections in pool (default: 50)
        """
        self._host = host
        self._port = port
        self._database = database
        self._user = user
        self._password = password
        self._min_pool_size = min_pool_size
        self._max_pool_size = max_pool_size
        self._pool: Optional[asyncpg.Pool] = None

    async def init(self) -> None:
        """
        Initialize connection pool and create tables if they don't exist.
        
        Creates a pool of database connections that are reused across all users.
        Each PostgresContext instance does NOT hold a dedicated connection,
        but borrows one from the pool only during operations.
        """
        if self._pool is None:
            self._pool = await asyncpg.create_pool(
                user=self._user,
                password=self._password,
                host=self._host,
                port=self._port,
                database=self._database,
                min_size=self._min_pool_size,
                max_size=self._max_pool_size
            )
            
            # Create tables if they don't exist
            async with self._pool.acquire() as conn:
                await conn.execute("""CREATE TABLE IF NOT EXISTS "maxapi_states"(
                                            "chat_id" BIGINT NOT NULL,
                                            "user_id" BIGINT NOT NULL,
                                            "state" TEXT,
                                            PRIMARY KEY ("chat_id", "user_id"))""")
                await conn.execute("""CREATE TABLE IF NOT EXISTS "maxapi_data"(
                                        "chat_id" BIGINT NOT NULL,
                                        "user_id" BIGINT NOT NULL,
                                        "data" JSON,
                                        PRIMARY KEY ("chat_id", "user_id"))""")

    async def close(self) -> None:
        """Close connection pool"""
        if self._pool is not None:
            await self._pool.close()
            self._pool = None

    def create_context(self, chat_id: Optional[int], user_id: Optional[int]) -> 'PostgresContext':
        """Factory method to create PostgresContext instances"""
        return PostgresContext(chat_id=chat_id, user_id=user_id, storage=self)

    def get_connection(self):
        """
        Get a connection from the pool (context manager).
        
        The connection is automatically returned to the pool when the context exits.
        Multiple PostgresContext instances share the same pool.
        
        Returns:
            asyncpg.pool.PoolAcquireContext: Connection context manager
        """
        if self._pool is None:
            raise RuntimeError("Storage not initialized. Call await storage.init() first")
        return self._pool.acquire()


class PostgresContext(MemoryContext):
    """
    Context class that extends MemoryContext with PostgreSQL persistence.
    
    This class inherits from MemoryContext and overrides its methods to store
    data in PostgreSQL instead of memory. Each instance is created per user/chat
    by the PostgresStorage factory.
    
    The context is automatically created by maxapi dispatcher for each event
    and passed to handlers.
    """

    def __init__(self, chat_id: Optional[int], user_id: Optional[int], storage: PostgresStorage):
        super().__init__(chat_id=chat_id, user_id=user_id)
        self._storage = storage

    async def get_data(self) -> Dict[str, Any]:
        """
        Retrieve and deserialize data from PostgreSQL database.
        
        Returns:
            Dictionary with context data or empty dict if no data found
        """
        async with self._storage.get_connection() as conn:
            result = await conn.fetchval(
                """SELECT "data" FROM "maxapi_data" WHERE "chat_id"=$1 AND "user_id"=$2""",
                self.chat_id, self.user_id
            )
            return json.loads(result) if result else {}

    async def set_data(self, data: Dict[str, Any]) -> None:
        """
        Save JSON-serialized data to PostgreSQL database, or delete if data is empty.
        
        Args:
            data: Dictionary with data to save
        """
        async with self._storage.get_connection() as conn:
            if not data:
                await conn.execute(
                    """DELETE FROM "maxapi_data" WHERE "chat_id"=$1 AND "user_id"=$2""",
                    self.chat_id, self.user_id
                )
            else:
                await conn.execute(
                    """INSERT INTO "maxapi_data" VALUES($1, $2, $3)
                       ON CONFLICT ("user_id", "chat_id") DO UPDATE SET "data" = $3""",
                    self.chat_id, self.user_id, json.dumps(data, ensure_ascii=False)
                )

    async def update_data(self, **kwargs: Any) -> None:
        """
        Update context data with new values (merge with existing data).
        
        Args:
            **kwargs: Key-value pairs to update
        """
        # Use lock from parent class to prevent race conditions
        async with self._lock:
            current_data = await self.get_data()
            current_data.update(kwargs)
            await self.set_data(current_data)

    async def set_state(self, state: Optional[Union[State, str]] = None) -> None:
        """
        Save current state to PostgreSQL database (or delete if state is None).
        
        Args:
            state: New state or None to clear state
        """
        _state = state.name if isinstance(state, State) else state
        
        async with self._storage.get_connection() as conn:
            if _state is None:
                await conn.execute(
                    """DELETE FROM "maxapi_states" WHERE chat_id=$1 AND "user_id"=$2""",
                    self.chat_id, self.user_id
                )
            else:
                await conn.execute(
                    """INSERT INTO "maxapi_states" VALUES($1, $2, $3)
                       ON CONFLICT ("user_id", "chat_id") DO UPDATE SET "state" = $3""",
                    self.chat_id, self.user_id, _state
                )

    async def get_state(self) -> Optional[Union[State, str]]:
        """
        Read current state from PostgreSQL database.
        
        Returns:
            Current state or None if state is not set
        """
        async with self._storage.get_connection() as conn:
            result = await conn.fetchval(
                """SELECT "state" FROM "maxapi_states" WHERE "chat_id"=$1 AND "user_id"=$2""",
                self.chat_id, self.user_id
            )
            return result if result else None

    async def clear(self) -> None:
        """
        Clear both state and data from PostgreSQL database.
        """
        async with self._lock:
            await self.set_state(None)
            await self.set_data({})


class PostgresDispatcher(Dispatcher):
    """
    Extended Dispatcher that uses PostgreSQL for context storage.
    
    This class overrides the __get_memory_context method to create
    PostgresContext instances instead of MemoryContext instances.
    
    Usage:
    
    # Initialize storage
    storage = PostgresStorage(
        host='localhost',
        port=5432,
        database='maxapi_fsm',
        user='bot',
        password='password'
    )
    await storage.init()
    
    # Create dispatcher with PostgreSQL storage
    dp = PostgresDispatcher(storage=storage)
    
    # Use as normal dispatcher
    @dp.message_created(F.message.body.text)
    async def handler(event, context):
        await context.update_data(name="John")
    """
    
    def __init__(self, storage: PostgresStorage, router_id: str = None, use_create_task: bool = False):
        super().__init__(router_id=router_id, use_create_task=use_create_task)
        self._storage = storage
    
    def _Dispatcher__get_memory_context(self, chat_id: Optional[int], user_id: Optional[int]) -> PostgresContext:
        """
        Override private method to return PostgresContext instead of MemoryContext.
        
        This method uses name mangling to override the private method from parent class.
        
        Args:
            chat_id: Chat identifier
            user_id: User identifier
            
        Returns:
            PostgresContext: Context for this user
        """
        # Check if context already exists for this user
        for ctx in self.contexts:
            if ctx.chat_id == chat_id and ctx.user_id == user_id:
                return ctx
        
        # Create new PostgresContext
        new_ctx = PostgresContext(chat_id=chat_id, user_id=user_id, storage=self._storage)
        self.contexts.append(new_ctx)
        return new_ctx
