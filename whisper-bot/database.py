"""
Шёпот Bot — База данных (SQLite)
"""
import aiosqlite
from datetime import datetime, timedelta, timezone
from config import DB_PATH


class Database:
    def __init__(self):
        self.db_path = DB_PATH
        self.db: aiosqlite.Connection | None = None

    async def connect(self):
        self.db = await aiosqlite.connect(self.db_path)
        self.db.row_factory = aiosqlite.Row
        await self.db.execute("PRAGMA journal_mode=WAL")
        await self.db.execute("PRAGMA foreign_keys=ON")
        await self._create_tables()

    async def close(self):
        if self.db:
            await self.db.close()

    # ──────────────────────── Схема ────────────────────────

    async def _create_tables(self):
        await self.db.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                user_id         INTEGER PRIMARY KEY,
                username        TEXT,
                first_name      TEXT,
                unique_code     TEXT UNIQUE NOT NULL,
                referrer_id     INTEGER,
                is_premium      INTEGER DEFAULT 0,
                premium_until   TEXT,
                free_unmasks    INTEGER DEFAULT 0,
                messages_received INTEGER DEFAULT 0,
                messages_sent   INTEGER DEFAULT 0,
                is_banned       INTEGER DEFAULT 0,
                greeting        TEXT,
                created_at      TEXT DEFAULT (datetime('now')),
                last_active     TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS messages (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                sender_id       INTEGER NOT NULL,
                receiver_id     INTEGER NOT NULL,
                text            TEXT NOT NULL,
                msg_type        TEXT DEFAULT 'text',
                is_read         INTEGER DEFAULT 0,
                is_unmasked     INTEGER DEFAULT 0,
                reply_to_id     INTEGER,
                created_at      TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (sender_id)   REFERENCES users(user_id),
                FOREIGN KEY (receiver_id) REFERENCES users(user_id)
            );

            CREATE TABLE IF NOT EXISTS referrals (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                referrer_id     INTEGER NOT NULL,
                referred_id     INTEGER NOT NULL,
                created_at      TEXT DEFAULT (datetime('now')),
                UNIQUE(referrer_id, referred_id),
                FOREIGN KEY (referrer_id) REFERENCES users(user_id),
                FOREIGN KEY (referred_id) REFERENCES users(user_id)
            );

            CREATE TABLE IF NOT EXISTS payments (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id         INTEGER NOT NULL,
                amount          INTEGER NOT NULL,
                payment_type    TEXT NOT NULL,
                telegram_payment_id TEXT,
                created_at      TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            );

            CREATE INDEX IF NOT EXISTS idx_msg_receiver  ON messages(receiver_id);
            CREATE INDEX IF NOT EXISTS idx_msg_sender    ON messages(sender_id);
            CREATE INDEX IF NOT EXISTS idx_users_code    ON users(unique_code);
            CREATE INDEX IF NOT EXISTS idx_ref_referrer  ON referrals(referrer_id);
        """)
        await self.db.commit()

    # ──────────────────────── Пользователи ────────────────────────

    async def get_user(self, user_id: int) -> aiosqlite.Row | None:
        async with self.db.execute(
            "SELECT * FROM users WHERE user_id = ?", (user_id,)
        ) as cur:
            return await cur.fetchone()

    async def get_user_by_code(self, code: str) -> aiosqlite.Row | None:
        async with self.db.execute(
            "SELECT * FROM users WHERE unique_code = ?", (code,)
        ) as cur:
            return await cur.fetchone()

    async def create_user(
        self,
        user_id: int,
        username: str | None,
        first_name: str | None,
        unique_code: str,
        referrer_id: int | None = None,
    ):
        await self.db.execute(
            """INSERT OR IGNORE INTO users
               (user_id, username, first_name, unique_code, referrer_id)
               VALUES (?, ?, ?, ?, ?)""",
            (user_id, username, first_name, unique_code, referrer_id),
        )
        await self.db.commit()

    async def update_user_info(self, user_id: int, username: str | None, first_name: str | None):
        await self.db.execute(
            "UPDATE users SET username=?, first_name=?, last_active=datetime('now') WHERE user_id=?",
            (username, first_name, user_id),
        )
        await self.db.commit()

    async def touch_user(self, user_id: int):
        await self.db.execute(
            "UPDATE users SET last_active=datetime('now') WHERE user_id=?", (user_id,)
        )
        await self.db.commit()

    async def set_greeting(self, user_id: int, greeting: str | None):
        await self.db.execute(
            "UPDATE users SET greeting=? WHERE user_id=?", (greeting, user_id)
        )
        await self.db.commit()

    async def ban_user(self, user_id: int, ban: bool = True):
        await self.db.execute(
            "UPDATE users SET is_banned=? WHERE user_id=?", (1 if ban else 0, user_id)
        )
        await self.db.commit()

    # ── Premium ──

    async def set_premium(self, user_id: int, days: int):
        user = await self.get_user(user_id)
        # Если уже есть активный premium — продлеваем
        now = datetime.now(timezone.utc)
        if user and user["is_premium"] and user["premium_until"]:
            current_until = datetime.fromisoformat(user["premium_until"])
            if current_until > now:
                new_until = current_until + timedelta(days=days)
            else:
                new_until = now + timedelta(days=days)
        else:
            new_until = now + timedelta(days=days)
        await self.db.execute(
            "UPDATE users SET is_premium=1, premium_until=? WHERE user_id=?",
            (new_until.isoformat(), user_id),
        )
        await self.db.commit()

    async def is_premium(self, user_id: int) -> bool:
        user = await self.get_user(user_id)
        if not user or not user["is_premium"]:
            return False
        if user["premium_until"]:
            until = datetime.fromisoformat(user["premium_until"])
            now = datetime.now(timezone.utc)
            # Handle naive datetime from DB
            if until.tzinfo is None:
                until = until.replace(tzinfo=timezone.utc)
            if until < now:
                await self.db.execute(
                    "UPDATE users SET is_premium=0, premium_until=NULL WHERE user_id=?",
                    (user_id,),
                )
                await self.db.commit()
                return False
        return True

    async def add_free_unmasks(self, user_id: int, count: int = 1):
        await self.db.execute(
            "UPDATE users SET free_unmasks=free_unmasks+? WHERE user_id=?",
            (count, user_id),
        )
        await self.db.commit()

    async def use_free_unmask(self, user_id: int) -> bool:
        user = await self.get_user(user_id)
        if user and user["free_unmasks"] > 0:
            await self.db.execute(
                "UPDATE users SET free_unmasks=free_unmasks-1 WHERE user_id=?",
                (user_id,),
            )
            await self.db.commit()
            return True
        return False

    # ──────────────────────── Сообщения ────────────────────────

    async def create_message(
        self,
        sender_id: int,
        receiver_id: int,
        text: str,
        msg_type: str = "text",
        reply_to_id: int | None = None,
    ) -> int:
        cur = await self.db.execute(
            """INSERT INTO messages (sender_id, receiver_id, text, msg_type, reply_to_id)
               VALUES (?, ?, ?, ?, ?)""",
            (sender_id, receiver_id, text, msg_type, reply_to_id),
        )
        await self.db.execute(
            "UPDATE users SET messages_received=messages_received+1 WHERE user_id=?",
            (receiver_id,),
        )
        await self.db.execute(
            "UPDATE users SET messages_sent=messages_sent+1 WHERE user_id=?",
            (sender_id,),
        )
        await self.db.commit()
        return cur.lastrowid

    async def get_message(self, message_id: int) -> aiosqlite.Row | None:
        async with self.db.execute(
            "SELECT * FROM messages WHERE id=?", (message_id,)
        ) as cur:
            return await cur.fetchone()

    async def mark_read(self, message_id: int):
        await self.db.execute("UPDATE messages SET is_read=1 WHERE id=?", (message_id,))
        await self.db.commit()

    async def unmask_message(self, message_id: int):
        await self.db.execute(
            "UPDATE messages SET is_unmasked=1 WHERE id=?", (message_id,)
        )
        await self.db.commit()

    async def count_sent_today(self, user_id: int) -> int:
        async with self.db.execute(
            """SELECT COUNT(*) as cnt FROM messages
               WHERE sender_id=? AND date(created_at)=date('now')""",
            (user_id,),
        ) as cur:
            row = await cur.fetchone()
            return row["cnt"] if row else 0

    async def last_message_time(
        self, sender_id: int, receiver_id: int
    ) -> datetime | None:
        async with self.db.execute(
            """SELECT created_at FROM messages
               WHERE sender_id=? AND receiver_id=?
               ORDER BY created_at DESC LIMIT 1""",
            (sender_id, receiver_id),
        ) as cur:
            row = await cur.fetchone()
            if row:
                return datetime.fromisoformat(row["created_at"])
            return None

    # ──────────────────────── Рефералы ────────────────────────

    async def create_referral(self, referrer_id: int, referred_id: int):
        try:
            await self.db.execute(
                "INSERT INTO referrals (referrer_id, referred_id) VALUES (?, ?)",
                (referrer_id, referred_id),
            )
            await self.db.commit()
        except Exception:
            pass  # duplicate

    async def referral_count(self, referrer_id: int) -> int:
        async with self.db.execute(
            "SELECT COUNT(*) as cnt FROM referrals WHERE referrer_id=?",
            (referrer_id,),
        ) as cur:
            row = await cur.fetchone()
            return row["cnt"] if row else 0

    # ──────────────────────── Платежи ────────────────────────

    async def create_payment(
        self, user_id: int, amount: int, payment_type: str, tg_payment_id: str | None = None
    ):
        await self.db.execute(
            """INSERT INTO payments (user_id, amount, payment_type, telegram_payment_id)
               VALUES (?, ?, ?, ?)""",
            (user_id, amount, payment_type, tg_payment_id),
        )
        await self.db.commit()

    # ──────────────────────── Статистика ────────────────────────

    async def stats(self) -> dict:
        data = {}
        for label, query in [
            ("total_users", "SELECT COUNT(*) FROM users"),
            ("total_messages", "SELECT COUNT(*) FROM messages"),
            ("today_users", "SELECT COUNT(*) FROM users WHERE date(created_at)=date('now')"),
            ("today_messages", "SELECT COUNT(*) FROM messages WHERE date(created_at)=date('now')"),
            ("active_24h", "SELECT COUNT(*) FROM users WHERE last_active>=datetime('now','-1 day')"),
            ("premium_users", "SELECT COUNT(*) FROM users WHERE is_premium=1"),
            ("total_revenue", "SELECT COALESCE(SUM(amount),0) FROM payments"),
        ]:
            async with self.db.execute(query) as cur:
                row = await cur.fetchone()
                data[label] = row[0] if row else 0
        return data

    async def all_user_ids(self) -> list[int]:
        async with self.db.execute(
            "SELECT user_id FROM users WHERE is_banned=0"
        ) as cur:
            rows = await cur.fetchall()
            return [r["user_id"] for r in rows]
