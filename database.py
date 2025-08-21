import aiosqlite
import os

XP_PER_LEVEL = int(os.getenv('XP_PER_LEVEL', 5))

class AsyncUserDatabase:
    def __init__(self, db_path="users.db"):
        self.db_path = db_path

    async def init_database(self):
        """Create tables if they don't exist"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    username TEXT,
                    xp INTEGER DEFAULT 0,
                    level INTEGER DEFAULT 1,
                    last_message_time INTEGER DEFAULT 0
                )                 
            ''')
            await db.commit()

    async def get_user(self, user_id):
        """Get user data or create if doesn't exist"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT * FROM users WHERE user_id = ?", (str(user_id),)
            )
            user = await cursor.fetchone()

            if not user:
                await db.execute(
                    "INSERT INTO users (user_id) values (?)", (str(user_id),)
                )
                await db.commit()
                return await self.get_user(user_id)
            
            return {
                'user_id': user[0],
                'username': user[1],
                'xp': user[2],
                'level': user[3],
                'last_message_time': user[4]
            }
        
    async def update_user_xp(self, user_id, xp_gain):
        """Add XP and handle level ups"""
        user = await self.get_user(user_id)
        new_xp = user['xp'] + xp_gain
        new_level = self.calculate_level(new_xp)

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE users SET xp = ?, level = ? WHERE user_id = ?",
                (new_xp, new_level, str(user_id))
            )
            await db.commit()
        
        return new_level > user['level']
    
    def calculate_level(self, xp):
        """Calculate level based on XP"""
        return int((xp / XP_PER_LEVEL) ** 0.5) + 1
    
    async def update_last_message_time(self, user_id, current_time, username):
        """Update the most recent message time and username"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE users SET last_message_time = ?, username = ? WHERE user_id = ?", 
                (current_time, username, str(user_id))
            )
            await db.commit()