import aiosqlite
import time

DB_NAME = "database.db"


async def get_db():
    return await aiosqlite.connect(DB_NAME)


async def init_db():
    db = await get_db()

    await db.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER UNIQUE,
        username TEXT,
        referrals INTEGER DEFAULT 0,
        balance INTEGER DEFAULT 0,
        last_daily INTEGER DEFAULT 0,
        channel_reward INTEGER DEFAULT 0
    )
    """)

    await db.commit()
    await db.close()


async def add_user(user_id, username=None, ref_id=None):
    db = await get_db()

    cur = await db.execute(
        "SELECT user_id FROM users WHERE user_id=?",
        (user_id,)
    )

    if await cur.fetchone():
        await db.close()
        return False

    await db.execute(
        """
        INSERT INTO users(user_id, username)
        VALUES(?,?)
        """,
        (user_id, username)
    )

    if ref_id and ref_id != user_id:
        await db.execute(
            """
            UPDATE users
            SET referrals=referrals+1,
            balance=balance+10
            WHERE user_id=?
            """,
            (ref_id,)
        )

    await db.commit()
    await db.close()

    return True


async def add_points(user_id, amount):
    db = await get_db()

    await db.execute(
        """
        UPDATE users
        SET balance=balance+?
        WHERE user_id=?
        """,
        (amount,user_id)
    )

    await db.commit()
    await db.close()


async def give_channel_reward(user_id):
    db = await get_db()

    cur = await db.execute(
        "SELECT channel_reward FROM users WHERE user_id=?",
        (user_id,)
    )

    row = await cur.fetchone()

    if row and row[0] == 0:
        await db.execute(
            """
            UPDATE users
            SET balance=balance+5,
            channel_reward=1
            WHERE user_id=?
            """,
            (user_id,)
        )

        await db.commit()
        await db.close()
        return True

    await db.close()
    return False


async def claim_daily(user_id):
    db = await get_db()

    cur = await db.execute(
        "SELECT last_daily FROM users WHERE user_id=?",
        (user_id,)
    )

    row = await cur.fetchone()

    now=int(time.time())

    if row and now-row[0] >= 86400:

        await db.execute(
            """
            UPDATE users
            SET balance=balance+10,
            last_daily=?
            WHERE user_id=?
            """,
            (now,user_id)
        )

        await db.commit()
        await db.close()
        return True

    await db.close()
    return False


async def get_user(user_id):
    db = await get_db()

    cur = await db.execute(
        """
        SELECT user_id,username,referrals,balance
        FROM users
        WHERE user_id=?
        """,
        (user_id,)
    )

    user = await cur.fetchone()

    await db.close()

    return user￼Enter
