import aiosqlite

DB_NAME = "rewardhub.db"


async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                points INTEGER DEFAULT 0,
                referrals INTEGER DEFAULT 0,
                referred_by INTEGER,
                can_withdraw INTEGER DEFAULT 0
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS referrals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                referrer_id INTEGER NOT NULL,
                referred_id INTEGER UNIQUE NOT NULL
            )
        """)

        await db.commit()


async def add_user(user_id, username=None, referred_by=None):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT user_id FROM users WHERE user_id = ?",
            (user_id,)
        )
        exists = await cursor.fetchone()

        if exists:
            return False

        await db.execute(
            """
            INSERT INTO users
            (user_id, username, referred_by)
            VALUES (?, ?, ?)
            """,
            (user_id, username, referred_by)
        )

        await db.commit()
        return True


async def add_referral(referrer_id, referred_id):
    if referrer_id == referred_id:
        return False

    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT id FROM referrals WHERE referred_id = ?",
            (referred_id,)
        )

        if await cursor.fetchone():
            return False

        await db.execute(
            """
            INSERT INTO referrals
            (referrer_id, referred_id)
            VALUES (?, ?)
            """,
            (referrer_id, referred_id)
        )

        await db.execute(
            """
            UPDATE users
            SET referrals = referrals + 1,
                points = points + 10
            WHERE user_id = ?
            """,
            (referrer_id,)
        )

        await db.execute(
            """
            UPDATE users
            SET can_withdraw =
                CASE
                    WHEN referrals >= 5 THEN 1
                    ELSE 0
                END
            WHERE user_id = ?
            """,
            (referrer_id,)
        )

        await db.commit()
        return True


async def get_user(user_id):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            """
            SELECT user_id, username, points, referrals, can_withdraw
            FROM users
            WHERE user_id = ?
            """,
            (user_id,)
        )

        return await cursor.fetchone()
