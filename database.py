"""
Database module for persistent storage of user stats and bot data.
Uses PostgreSQL with asyncpg for async operations.
Falls back to SQLite if no PostgreSQL is configured (for local development).
"""
import os
import asyncio
import json
from typing import Optional, Dict, Any

# Try to import asyncpg for PostgreSQL
try:
    import asyncpg
    HAS_ASYNCPG = True
except ImportError:
    HAS_ASYNCPG = False
    print("Warning: asyncpg not installed. PostgreSQL support disabled.")

# Try to import aiosqlite for SQLite fallback
try:
    import aiosqlite
    HAS_AIOSQLITE = True
except ImportError:
    HAS_AIOSQLITE = False
    print("Warning: aiosqlite not installed. SQLite fallback disabled.")


class Database:
    """Async database wrapper supporting PostgreSQL (production) and SQLite (development)."""
    
    def __init__(self):
        self.pool = None
        self.sqlite_conn = None
        self.is_postgres = False
        self.is_sqlite = False
    
    async def connect(self):
        """Connect to database. Tries PostgreSQL first, falls back to SQLite."""
        database_url = os.environ.get('DATABASE_URL')
        
        if database_url and HAS_ASYNCPG:
            # Use PostgreSQL
            try:
                # DigitalOcean uses postgres:// but asyncpg needs postgresql://
                if database_url.startswith('postgres://'):
                    database_url = database_url.replace('postgres://', 'postgresql://', 1)
                
                self.pool = await asyncpg.create_pool(
                    database_url,
                    min_size=1,
                    max_size=10,
                    command_timeout=60
                )
                self.is_postgres = True
                print("✅ Connected to PostgreSQL database")
                await self._create_tables_postgres()
                return
            except Exception as e:
                print(f"❌ Failed to connect to PostgreSQL: {e}")
                print("Falling back to SQLite...")
        
        # Fall back to SQLite for local development
        if HAS_AIOSQLITE:
            db_path = os.path.join(os.path.dirname(__file__), 'bot_data.db')
            self.sqlite_conn = await aiosqlite.connect(db_path)
            self.is_sqlite = True
            print(f"✅ Connected to SQLite database at {db_path}")
            await self._create_tables_sqlite()
        else:
            raise RuntimeError(
                "No database available! Install either 'asyncpg' (for PostgreSQL) "
                "or 'aiosqlite' (for SQLite development)."
            )
    
    async def _create_tables_postgres(self):
        """Create tables in PostgreSQL."""
        async with self.pool.acquire() as conn:
            # User stats table
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS user_stats (
                    user_id BIGINT PRIMARY KEY,
                    userphone_messages INTEGER DEFAULT 0,
                    userphone_started INTEGER DEFAULT 0,
                    wins_tictactoe INTEGER DEFAULT 0,
                    wins_connectfour INTEGER DEFAULT 0,
                    wins_rps INTEGER DEFAULT 0,
                    wins_hangman INTEGER DEFAULT 0
                )
            ''')
            
            # Warnings table
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS warnings (
                    id SERIAL PRIMARY KEY,
                    guild_id BIGINT NOT NULL,
                    user_id BIGINT NOT NULL,
                    moderator_id BIGINT NOT NULL,
                    reason TEXT,
                    timestamp TIMESTAMP DEFAULT NOW()
                )
            ''')
            await conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_warnings_guild_user 
                ON warnings(guild_id, user_id)
            ''')
            
            # Config tables for various bot features
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS bot_config (
                    key TEXT PRIMARY KEY,
                    value JSONB NOT NULL
                )
            ''')
            
            print("✅ PostgreSQL tables created/verified")
    
    async def _create_tables_sqlite(self):
        """Create tables in SQLite."""
        # User stats table
        await self.sqlite_conn.execute('''
            CREATE TABLE IF NOT EXISTS user_stats (
                user_id INTEGER PRIMARY KEY,
                userphone_messages INTEGER DEFAULT 0,
                userphone_started INTEGER DEFAULT 0,
                wins_tictactoe INTEGER DEFAULT 0,
                wins_connectfour INTEGER DEFAULT 0,
                wins_rps INTEGER DEFAULT 0,
                wins_hangman INTEGER DEFAULT 0
            )
        ''')
        
        # Warnings table
        await self.sqlite_conn.execute('''
            CREATE TABLE IF NOT EXISTS warnings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                moderator_id INTEGER NOT NULL,
                reason TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        await self.sqlite_conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_warnings_guild_user 
            ON warnings(guild_id, user_id)
        ''')
        
        # Config table
        await self.sqlite_conn.execute('''
            CREATE TABLE IF NOT EXISTS bot_config (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        ''')
        
        await self.sqlite_conn.commit()
        print("✅ SQLite tables created/verified")
    
    async def close(self):
        """Close database connection."""
        if self.is_postgres and self.pool:
            await self.pool.close()
        elif self.is_sqlite and self.sqlite_conn:
            await self.sqlite_conn.close()
    
    # User Stats Methods
    
    async def get_user_stats(self, user_id: int) -> Dict[str, int]:
        """Get all stats for a user."""
        if self.is_postgres:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow(
                    'SELECT * FROM user_stats WHERE user_id = $1',
                    user_id
                )
                if row:
                    return dict(row)
                return {
                    'userphone_messages': 0,
                    'userphone_started': 0,
                    'wins_tictactoe': 0,
                    'wins_connectfour': 0,
                    'wins_rps': 0,
                    'wins_hangman': 0
                }
        else:
            async with self.sqlite_conn.execute(
                'SELECT * FROM user_stats WHERE user_id = ?',
                (user_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return {
                        'userphone_messages': row[1],
                        'userphone_started': row[2],
                        'wins_tictactoe': row[3],
                        'wins_connectfour': row[4],
                        'wins_rps': row[5],
                        'wins_hangman': row[6]
                    }
                return {
                    'userphone_messages': 0,
                    'userphone_started': 0,
                    'wins_tictactoe': 0,
                    'wins_connectfour': 0,
                    'wins_rps': 0,
                    'wins_hangman': 0
                }
    
    async def increment_stat(self, user_id: int, stat_name: str, amount: int = 1):
        """Increment a specific stat for a user."""
        valid_stats = [
            'userphone_messages', 'userphone_started',
            'wins_tictactoe', 'wins_connectfour', 'wins_rps', 'wins_hangman'
        ]
        if stat_name not in valid_stats:
            raise ValueError(f"Invalid stat name: {stat_name}")
        
        if self.is_postgres:
            async with self.pool.acquire() as conn:
                await conn.execute(f'''
                    INSERT INTO user_stats (user_id, {stat_name})
                    VALUES ($1, $2)
                    ON CONFLICT (user_id)
                    DO UPDATE SET {stat_name} = user_stats.{stat_name} + $2
                ''', user_id, amount)
        else:
            await self.sqlite_conn.execute(f'''
                INSERT INTO user_stats (user_id, {stat_name})
                VALUES (?, ?)
                ON CONFLICT(user_id)
                DO UPDATE SET {stat_name} = {stat_name} + ?
            ''', (user_id, amount, amount))
            await self.sqlite_conn.commit()
    
    async def get_all_user_stats(self) -> Dict[int, Dict[str, int]]:
        """Get stats for all users (for migration purposes)."""
        result = {}
        if self.is_postgres:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch('SELECT * FROM user_stats')
                for row in rows:
                    result[row['user_id']] = dict(row)
        else:
            async with self.sqlite_conn.execute('SELECT * FROM user_stats') as cursor:
                async for row in cursor:
                    result[row[0]] = {
                        'userphone_messages': row[1],
                        'userphone_started': row[2],
                        'wins_tictactoe': row[3],
                        'wins_connectfour': row[4],
                        'wins_rps': row[5],
                        'wins_hangman': row[6]
                    }
        return result
    
    # Warning Methods
    
    async def add_warning(self, guild_id: int, user_id: int, moderator_id: int, reason: str) -> int:
        """Add a warning and return the warning ID."""
        if self.is_postgres:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow('''
                    INSERT INTO warnings (guild_id, user_id, moderator_id, reason)
                    VALUES ($1, $2, $3, $4)
                    RETURNING id
                ''', guild_id, user_id, moderator_id, reason)
                return row['id']
        else:
            cursor = await self.sqlite_conn.execute('''
                INSERT INTO warnings (guild_id, user_id, moderator_id, reason)
                VALUES (?, ?, ?, ?)
            ''', (guild_id, user_id, moderator_id, reason))
            await self.sqlite_conn.commit()
            return cursor.lastrowid
    
    async def get_warnings(self, guild_id: int, user_id: int) -> list:
        """Get all warnings for a user in a guild."""
        if self.is_postgres:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch('''
                    SELECT id, moderator_id, reason, timestamp
                    FROM warnings
                    WHERE guild_id = $1 AND user_id = $2
                    ORDER BY timestamp DESC
                ''', guild_id, user_id)
                return [dict(row) for row in rows]
        else:
            async with self.sqlite_conn.execute('''
                SELECT id, moderator_id, reason, timestamp
                FROM warnings
                WHERE guild_id = ? AND user_id = ?
                ORDER BY timestamp DESC
            ''', (guild_id, user_id)) as cursor:
                rows = await cursor.fetchall()
                return [
                    {'id': row[0], 'moderator_id': row[1], 'reason': row[2], 'timestamp': row[3]}
                    for row in rows
                ]
    
    async def remove_warning(self, warning_id: int, guild_id: int) -> bool:
        """Remove a specific warning. Returns True if found and removed."""
        if self.is_postgres:
            async with self.pool.acquire() as conn:
                result = await conn.execute('''
                    DELETE FROM warnings
                    WHERE id = $1 AND guild_id = $2
                ''', warning_id, guild_id)
                return result != 'DELETE 0'
        else:
            await self.sqlite_conn.execute('''
                DELETE FROM warnings
                WHERE id = ? AND guild_id = ?
            ''', (warning_id, guild_id))
            await self.sqlite_conn.commit()
            return self.sqlite_conn.total_changes > 0
    
    async def clear_warnings(self, guild_id: int, user_id: int) -> int:
        """Clear all warnings for a user. Returns count of warnings removed."""
        if self.is_postgres:
            async with self.pool.acquire() as conn:
                result = await conn.execute('''
                    DELETE FROM warnings
                    WHERE guild_id = $1 AND user_id = $2
                ''', guild_id, user_id)
                # Extract number from "DELETE 5" string
                return int(result.split()[-1])
        else:
            await self.sqlite_conn.execute('''
                DELETE FROM warnings
                WHERE guild_id = ? AND user_id = ?
            ''', (guild_id, user_id))
            await self.sqlite_conn.commit()
            return self.sqlite_conn.total_changes
    
    # Config Methods (for giveaway, timechannel, welcomer configs)
    
    async def get_config(self, key: str) -> Optional[dict]:
        """Get a config value by key."""
        if self.is_postgres:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow(
                    'SELECT value FROM bot_config WHERE key = $1',
                    key
                )
                if not row:
                    return None
                
                # Handle both dict (new format) and string (old format with double JSON encoding)
                value = row['value']
                if isinstance(value, str):
                    # Old format: was stored as json.dumps(dict), need to parse it
                    return json.loads(value)
                else:
                    # New format: JSONB already returns a dict
                    return value
        else:
            async with self.sqlite_conn.execute(
                'SELECT value FROM bot_config WHERE key = ?',
                (key,)
            ) as cursor:
                row = await cursor.fetchone()
                return json.loads(row[0]) if row else None
    
    async def set_config(self, key: str, value: dict):
        """Set a config value."""
        if self.is_postgres:
            async with self.pool.acquire() as conn:
                await conn.execute('''
                    INSERT INTO bot_config (key, value)
                    VALUES ($1, $2)
                    ON CONFLICT (key)
                    DO UPDATE SET value = $2
                ''', key, value)  # PostgreSQL JSONB handles dicts directly, no json.dumps needed
        else:
            await self.sqlite_conn.execute('''
                INSERT INTO bot_config (key, value)
                VALUES (?, ?)
                ON CONFLICT(key)
                DO UPDATE SET value = ?
            ''', (key, json.dumps(value), json.dumps(value)))
            await self.sqlite_conn.commit()
    
    async def delete_config(self, key: str):
        """Delete a config key."""
        if self.is_postgres:
            async with self.pool.acquire() as conn:
                await conn.execute('DELETE FROM bot_config WHERE key = $1', key)
        else:
            await self.sqlite_conn.execute('DELETE FROM bot_config WHERE key = ?', (key,))
            await self.sqlite_conn.commit()


# Global database instance
db = Database()
