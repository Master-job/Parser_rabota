import os
import asyncpg
import hashlib
import secrets
from datetime import datetime


DATABASE_URL = os.getenv("DATABASE_URL")


class DatabaseManager:

    def __init__(self):
        self.pool = None


    async def init_pool(self):
        self.pool = await asyncpg.create_pool(
            DATABASE_URL,
            min_size=1,
            max_size=5
        )

        async with self.pool.acquire() as conn:

            await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                full_name TEXT,
                phone TEXT,
                role TEXT,
                password_hash TEXT,
                token TEXT
            )
            """)


            await conn.execute("""
            CREATE TABLE IF NOT EXISTS parsed_leads (
                id SERIAL PRIMARY KEY,
                source_id TEXT UNIQUE,
                category TEXT,
                title TEXT,
                description TEXT,
                metro TEXT,
                district TEXT,
                link TEXT,
                tags TEXT,
                created_at TIMESTAMP DEFAULT NOW()
            )
            """)


            await conn.execute("""
            CREATE TABLE IF NOT EXISTS requests (
                id SERIAL PRIMARY KEY,
                user_id INTEGER,
                title TEXT,
                description TEXT,
                category TEXT,
                subcategory TEXT,
                budget_min INTEGER,
                budget_max INTEGER,
                metro TEXT,
                district TEXT,
                created_at TIMESTAMP DEFAULT NOW()
            )
            """)

        print("✅ PostgreSQL database initialized")


    async def close_pool(self):

        if self.pool:
            await self.pool.close()



    def hash_password(self, password):

        return hashlib.sha256(
            password.encode()
        ).hexdigest()



    async def create_user(self, data):

        async with self.pool.acquire() as conn:

            result = await conn.fetchrow(
                """
                INSERT INTO users
                (username, full_name, phone, role, password_hash)

                VALUES ($1,$2,$3,$4,$5)

                RETURNING id
                """,

                data.username,
                data.full_name,
                data.phone,
                data.role,
                self.hash_password(data.password)

            )

            return result["id"]



    async def authenticate_user(self, username, password):

        async with self.pool.acquire() as conn:

            user = await conn.fetchrow(
                """
                SELECT *
                FROM users
                WHERE username=$1
                """,
                username
            )


            if not user:
                return None


            if user["password_hash"] != self.hash_password(password):
                return None


            return dict(user)



    async def generate_token(self, user_id):

        token = secrets.token_hex(32)


        async with self.pool.acquire() as conn:

            await conn.execute(
                """
                UPDATE users
                SET token=$1
                WHERE id=$2
                """,
                token,
                user_id
            )


        return token



    async def verify_token(self, token):

        async with self.pool.acquire() as conn:

            user = await conn.fetchrow(
                """
                SELECT *
                FROM users
                WHERE token=$1
                """,
                token
            )

            return dict(user) if user else None




    async def save_parsed_lead(self, lead):

        async with self.pool.acquire() as conn:

            result = await conn.execute(
                """
                INSERT INTO parsed_leads
                (
                source_id,
                category,
                title,
                description,
                metro,
                district,
                link,
                tags
                )

                VALUES
                ($1,$2,$3,$4,$5,$6,$7,$8)

                ON CONFLICT(source_id)
                DO NOTHING

                """,

                lead.get("source_id"),
                lead.get("category"),
                lead.get("title"),
                lead.get("description"),
                lead.get("metro"),
                lead.get("district"),
                lead.get("link"),
                lead.get("tags")

            )


            return result != "INSERT 0 0"



    async def create_request(self, user_id, data):

        async with self.pool.acquire() as conn:

            result = await conn.fetchrow(
                """
                INSERT INTO requests
                (
                user_id,
                title,
                description,
                category,
                subcategory,
                budget_min,
                budget_max,
                metro,
                district
                )

                VALUES
                ($1,$2,$3,$4,$5,$6,$7,$8,$9)

                RETURNING id
                """,

                user_id,
                data.title,
                data.description,
                data.category,
                data.subcategory,
                data.budget_min,
                data.budget_max,
                data.metro,
                data.district
            )

            return result["id"]



    async def get_request(self, request_id):

        async with self.pool.acquire() as conn:

            row = await conn.fetchrow(
                """
                SELECT *
                FROM requests
                WHERE id=$1
                """,
                request_id
            )

            return dict(row) if row else None
