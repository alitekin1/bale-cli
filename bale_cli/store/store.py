import json
import sqlite3
from pathlib import Path
from typing import Optional

import aiosqlite


class Store:
    """SQLite store with FTS5 for message indexing."""

    def __init__(self, store_dir: Path):
        self.store_dir = store_dir
        self.store_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.store_dir / "bale.db"

    async def init(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("PRAGMA journal_mode=WAL")
            await db.execute("PRAGMA foreign_keys=ON")

            await db.execute("""
                CREATE TABLE IF NOT EXISTS chats (
                    id INTEGER PRIMARY KEY,
                    peer_id INTEGER NOT NULL UNIQUE,
                    peer_type TEXT NOT NULL,
                    title TEXT,
                    username TEXT,
                    about TEXT,
                    photo_id TEXT,
                    last_message_date INTEGER DEFAULT 0,
                    unread_count INTEGER DEFAULT 0,
                    is_pinned INTEGER DEFAULT 0,
                    is_muted INTEGER DEFAULT 0,
                    is_archived INTEGER DEFAULT 0,
                    local_name TEXT
                )
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message_id INTEGER NOT NULL,
                    chat_id INTEGER NOT NULL,
                    peer_id INTEGER NOT NULL,
                    peer_type TEXT NOT NULL,
                    sender_id INTEGER,
                    sender_name TEXT,
                    text TEXT,
                    message_type TEXT DEFAULT 'text',
                    media_file_id TEXT,
                    media_access_hash TEXT,
                    media_mime_type TEXT,
                    media_file_size INTEGER,
                    media_duration INTEGER,
                    media_url TEXT,
                    reply_to_message_id INTEGER,
                    reply_to_peer_id INTEGER,
                    date INTEGER NOT NULL,
                    seq INTEGER,
                    is_from_me INTEGER DEFAULT 0,
                    is_edited INTEGER DEFAULT 0,
                    is_pinned INTEGER DEFAULT 0,
                    reactions TEXT DEFAULT '[]',
                    raw_json TEXT,
                    UNIQUE(message_id, chat_id)
                )
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS contacts (
                    id INTEGER PRIMARY KEY,
                    peer_id INTEGER NOT NULL UNIQUE,
                    first_name TEXT,
                    last_name TEXT,
                    phone TEXT,
                    username TEXT,
                    about TEXT,
                    is_bot INTEGER DEFAULT 0,
                    is_blocked INTEGER DEFAULT 0,
                    local_name TEXT
                )
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS groups (
                    id INTEGER PRIMARY KEY,
                    peer_id INTEGER NOT NULL UNIQUE,
                    title TEXT,
                    about TEXT,
                    member_count INTEGER DEFAULT 0,
                    is_channel INTEGER DEFAULT 0,
                    username TEXT,
                    invite_url TEXT,
                    creator_id INTEGER,
                    admin INTEGER DEFAULT 0
                )
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS sync_state (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """)

            try:
                await db.execute("""
                    CREATE VIRTUAL TABLE IF NOT EXISTS messages_fts
                    USING fts5(text, content=messages, content_rowid=id)
                """)
            except Exception:
                pass

            try:
                await db.execute("""
                    CREATE TRIGGER IF NOT EXISTS messages_ai AFTER INSERT ON messages
                    BEGIN
                        INSERT INTO messages_fts(rowid, text)
                        VALUES (new.id, new.text);
                    END
                """)
            except Exception:
                pass

            try:
                await db.execute("""
                    CREATE TRIGGER IF NOT EXISTS messages_ad AFTER DELETE ON messages
                    BEGIN
                        INSERT INTO messages_fts(messages_fts, rowid, text)
                        VALUES ('delete', old.id, old.text);
                    END
                """)
            except Exception:
                pass

            await db.commit()

    async def upsert_chat(self, peer_id: int, peer_type: str, title: str = None,
                          username: str = None, **kwargs):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO chats (peer_id, peer_type, title, username, last_message_date)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(peer_id) DO UPDATE SET
                    peer_type=excluded.peer_type,
                    title=COALESCE(excluded.title, chats.title),
                    username=COALESCE(excluded.username, chats.username),
                    last_message_date=MAX(chats.last_message_date, excluded.last_message_date)
            """, (peer_id, peer_type, title, username, kwargs.get("last_message_date", 0)))
            await db.commit()

    async def insert_message(self, message_id: int, chat_id: int, peer_id: int,
                             peer_type: str, text: str = None, sender_id: int = None,
                             sender_name: str = None, message_type: str = "text",
                             date: int = 0, is_from_me: bool = False,
                             reply_to_message_id: int = None,
                             media_file_id: str = None, media_access_hash: str = None,
                             media_mime_type: str = None, media_file_size: int = None,
                             media_duration: int = None, raw_json: str = None,
                             seq: int = None):
        async with aiosqlite.connect(self.db_path) as db:
            try:
                await db.execute("""
                    INSERT OR IGNORE INTO messages
                        (message_id, chat_id, peer_id, peer_type, sender_id, sender_name,
                         text, message_type, date, is_from_me, reply_to_message_id,
                         media_file_id, media_access_hash, media_mime_type,
                         media_file_size, media_duration, raw_json, seq)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (message_id, chat_id, peer_id, peer_type, sender_id, sender_name,
                      text, message_type, date, int(is_from_me), reply_to_message_id,
                      media_file_id, media_access_hash, media_mime_type,
                      media_file_size, media_duration, raw_json, seq))
                await db.commit()
            except Exception:
                pass

    async def search_messages(self, query: str, chat_id: int = None,
                              sender_id: int = None, message_type: str = None,
                              date_from: int = None, date_to: int = None,
                              limit: int = 50, offset: int = 0):
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            conditions = []
            params = []

            if chat_id:
                conditions.append("m.chat_id = ?")
                params.append(chat_id)
            if sender_id:
                conditions.append("m.sender_id = ?")
                params.append(sender_id)
            if message_type:
                conditions.append("m.message_type = ?")
                params.append(message_type)
            if date_from:
                conditions.append("m.date >= ?")
                params.append(date_from)
            if date_to:
                conditions.append("m.date <= ?")
                params.append(date_to)

            where = " AND ".join(conditions) if conditions else "1=1"

            sql = f"""
                SELECT m.*, c.title as chat_title
                FROM messages m
                LEFT JOIN chats c ON m.chat_id = c.peer_id
                WHERE {where}
                AND m.text IS NOT NULL AND m.text != ''
                ORDER BY m.date DESC
                LIMIT ? OFFSET ?
            """
            params.extend([limit, offset])

            async with db.execute(sql, params) as cursor:
                rows = await cursor.fetchall()
                return [dict(r) for r in rows]

    async def search_messages_fts(self, query: str, chat_id: int = None,
                                  limit: int = 50, offset: int = 0):
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            conditions = ["m.text IS NOT NULL", "m.text != ''"]
            params = []

            if chat_id:
                conditions.append("m.chat_id = ?")
                params.append(chat_id)

            where = " AND ".join(conditions)

            sql = f"""
                SELECT m.*, c.title as chat_title, rank
                FROM messages_fts f
                JOIN messages m ON m.id = f.rowid
                LEFT JOIN chats c ON m.chat_id = c.peer_id
                WHERE messages_fts MATCH ?
                AND {where}
                ORDER BY rank
                LIMIT ? OFFSET ?
            """
            params = [query] + params + [limit, offset]

            try:
                async with db.execute(sql, params) as cursor:
                    rows = await cursor.fetchall()
                    return [dict(r) for r in rows]
            except Exception:
                return await self.search_messages(query, chat_id=chat_id, limit=limit, offset=offset)

    async def get_chats(self, limit: int = 100, offset: int = 0,
                        peer_type: str = None):
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            where = "1=1"
            params = []
            if peer_type:
                where = "peer_type = ?"
                params.append(peer_type)

            sql = f"""
                SELECT * FROM chats
                WHERE {where}
                ORDER BY last_message_date DESC
                LIMIT ? OFFSET ?
            """
            params.extend([limit, offset])

            async with db.execute(sql, params) as cursor:
                rows = await cursor.fetchall()
                return [dict(r) for r in rows]

    async def get_contacts(self, limit: int = 100, offset: int = 0):
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM contacts ORDER BY first_name LIMIT ? OFFSET ?",
                (limit, offset)
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(r) for r in rows]

    async def get_groups(self, limit: int = 100, offset: int = 0,
                         is_channel: bool = None):
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            where = "1=1"
            params = []
            if is_channel is not None:
                where = "is_channel = ?"
                params.append(int(is_channel))

            sql = f"""
                SELECT * FROM groups
                WHERE {where}
                ORDER BY title
                LIMIT ? OFFSET ?
            """
            params.extend([limit, offset])

            async with db.execute(sql, params) as cursor:
                rows = await cursor.fetchall()
                return [dict(r) for r in rows]

    async def get_sync_state(self, key: str) -> Optional[str]:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT value FROM sync_state WHERE key = ?", (key,)
            ) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else None

    async def set_sync_state(self, key: str, value: str):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO sync_state (key, value)
                VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET value=excluded.value
            """, (key, value))
            await db.commit()

    async def message_count(self) -> int:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT COUNT(*) FROM messages") as cursor:
                row = await cursor.fetchone()
                return row[0]

    async def db_size(self) -> int:
        wal = self.db_path.with_name(self.db_path.name + "-wal")
        shm = self.db_path.with_name(self.db_path.name + "-shm")
        size = self.db_path.stat().st_size if self.db_path.exists() else 0
        size += wal.stat().st_size if wal.exists() else 0
        size += shm.stat().st_size if shm.exists() else 0
        return size
