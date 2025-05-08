import psycopg2
import asyncpg
import asyncio
import random
import string
import time
from contextlib import contextmanager, asynccontextmanager

import config

# --- Database Initialization ---

def setup_database():
    """Creates the necessary table if it doesn't exist and populates it."""
    print("Setting up PostgreSQL database...")
    conn = None
    try:
        conn = psycopg2.connect(
            dbname=config.DB_NAME,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            host=config.DB_HOST,
            port=config.DB_PORT
        )
        conn.autocommit = True # Use autocommit for DDL
        cur = conn.cursor()
        print(f"Checking/Creating table '{config.DB_TABLE_NAME}'...")
        cur.execute(f"""
            CREATE TABLE IF NOT EXISTS {config.DB_TABLE_NAME} (
                id SERIAL PRIMARY KEY,
                content TEXT NOT NULL,
                sent BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMPTZ DEFAULT NOW()
            );
        """)
        cur.execute(f"GRANT ALL PRIVILEGES ON TABLE {config.DB_TABLE_NAME} TO {config.DB_USER};")
        cur.execute(f"GRANT USAGE, SELECT ON SEQUENCE {config.DB_TABLE_NAME}_id_seq TO {config.DB_USER};")
        cur.close()
        conn.close() # Close DDL connection
        print(f"Table '{config.DB_TABLE_NAME}' checked/created.")
        _populate_database_if_empty()
        print(f"Database setup complete. Waiting {config.DB_SETUP_WAIT_SECONDS}s...")
        time.sleep(config.DB_SETUP_WAIT_SECONDS)

    except psycopg2.OperationalError as e:
        print(f"\n*** DATABASE CONNECTION ERROR ***")
        print(f"Could not connect to PostgreSQL database '{config.DB_NAME}' on {config.DB_HOST}:{config.DB_PORT} as user '{config.DB_USER}'.")
        print("Please ensure:")
        print("1. PostgreSQL server is running.")
        print("2. The database and user exist (run the psql commands provided earlier)." )
        print("3. The connection details (DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD) are correct in your .env file or config.py.")
        print(f"Error details: {e}")
        print("*******************************")
        raise # Re-raise the exception to stop the script
    except Exception as e:
        print(f"Error during database setup: {e}")
        if conn:
            conn.close()
        raise

def _generate_random_message(length=50):
    chars = string.ascii_letters + string.digits + ' '
    return ''.join(random.choice(chars) for _ in range(length))

def _populate_database_if_empty():
    """Populates the database with sample messages if it's empty."""
    conn = None
    try:
        conn = psycopg2.connect(config.DATABASE_URL_SYNC)
        cur = conn.cursor()
        cur.execute(f"SELECT COUNT(*) FROM {config.DB_TABLE_NAME};")
        count = cur.fetchone()[0]
        if count == 0:
            print(f"Table '{config.DB_TABLE_NAME}' is empty. Populating with {config.NUM_MESSAGES} sample messages...")
            messages = [(_generate_random_message(),) for _ in range(config.NUM_MESSAGES)]
            insert_query = f"INSERT INTO {config.DB_TABLE_NAME} (content) VALUES (%s)"
            cur.executemany(insert_query, messages)
            conn.commit()
            print(f"Successfully inserted {len(messages)} messages.")
        else:
            print(f"Table '{config.DB_TABLE_NAME}' already contains {count} messages. Skipping population.")
        cur.close()
    except Exception as e:
        print(f"Error populating database: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

# --- Synchronous DB Operations ---

@contextmanager
def get_sync_db_connection():
    conn = None
    try:
        conn = psycopg2.connect(config.DATABASE_URL_SYNC)
        yield conn
    finally:
        if conn:
            conn.close()

def read_message_sync(conn):
    """Reads a single unsent message (oldest first). Returns (id, content) or (None, None)."""
    with conn.cursor() as cur:
        # Fetch one unsent message, mark it as sent (or about to be sent)
        # Using FOR UPDATE SKIP LOCKED is safer for concurrency, but maybe overkill here.
        # Let's just fetch one not marked as sent.
        cur.execute(f"""
            SELECT id, content FROM {config.DB_TABLE_NAME}
            WHERE sent = FALSE
            ORDER BY id
            LIMIT 1
            FOR UPDATE SKIP LOCKED;
        """)
        row = cur.fetchone()
        if row:
            message_id, content = row
            # Optionally mark as sent immediately
            # cur.execute(f"UPDATE {config.DB_TABLE_NAME} SET sent = TRUE WHERE id = %s;", (message_id,))
            # conn.commit() # Commit if not using autocommit connection
            return message_id, content
        else:
            return None, None # No unsent messages found

# --- Asynchronous DB Operations ---

# Global pool variable (can also be managed within the async main function)
async_pool = None

async def create_async_pool():
    global async_pool
    if async_pool is None:
        print("Creating asyncpg connection pool...")
        try:
            async_pool = await asyncpg.create_pool(
                dsn=config.DATABASE_URL_SYNC, # asyncpg uses DSN format directly
                min_size=1, max_size=10 # Example pool size
            )
            print("Asyncpg pool created.")
        except Exception as e:
            print(f"Failed to create asyncpg pool: {e}")
            async_pool = None # Ensure pool is None if creation fails
            raise
    return async_pool

async def close_async_pool():
    global async_pool
    if async_pool:
        print("Closing asyncpg connection pool...")
        await async_pool.close()
        async_pool = None
        print("Asyncpg pool closed.")

@asynccontextmanager
async def get_async_db_connection():
    pool = await create_async_pool()
    if pool is None:
         raise ConnectionError("Asyncpg pool is not available.")
    async with pool.acquire() as connection:
        yield connection

async def read_message_async(conn):
    """Reads a single unsent message asynchronously. Returns (id, content) or (None, None)."""
    async with conn.transaction():
        # Fetch one unsent message
        row = await conn.fetchrow(f"""
            SELECT id, content FROM {config.DB_TABLE_NAME}
            WHERE sent = FALSE
            ORDER BY id
            LIMIT 1
            FOR UPDATE SKIP LOCKED;
        """)
        if row:
            message_id, content = row['id'], row['content']
            # Optionally mark as sent
            # await conn.execute(f"UPDATE {config.DB_TABLE_NAME} SET sent = TRUE WHERE id = $1;", message_id)
            return message_id, content
        else:
            return None, None 