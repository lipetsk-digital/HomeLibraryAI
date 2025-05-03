# ========================================================
# Module for creating tables in PostgreSQL
# ========================================================
# This module is responsible for creating the necessary tables in the PostgreSQL database.
# It checks if the tables already exist and creates them if they do not. The tables include:
# - logs: for logging user activity
# - state: for storing the state of the bot
# - books: for storing book information
# ========================================================

import asyncpg # For asynchronous PostgreSQL connection

# ========================================================
# Create tables in PostgreSQL if they doesn't exist
# ========================================================
async def create_tables(POSTGRES_CONFIG):
    conn = await asyncpg.connect(**POSTGRES_CONFIG)
    await conn.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            user_id BIGINT,
            nickname TEXT,
            username TEXT,
            datetime TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    await conn.execute('''
        CREATE TABLE IF NOT EXISTS books (
            user_id BIGINT,
            book_id BIGINT,
            cathegory TEXT,
            photo_filename TEXT,
            cover_filename TEXT,
            brief_filename TEXT,
            title TEXT,
            authors TEXT,
            pages TEXT,
            puiblisher TEXT,
            year TEXT,
            isbn TEXT,
            annotation TEXT,
            brief TEXT,
            datetime TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, book_id)
        )
    ''')
    await conn.close()