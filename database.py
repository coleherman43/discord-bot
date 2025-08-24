import aiosqlite
import os
from dotenv import load_dotenv
import time

load_dotenv()
XP_PER_LEVEL = int(os.getenv('XP_PER_LEVEL', 5))

class AsyncUserDatabase:
    def __init__(self, db_path="users.db"):
        self.db_path = db_path

    async def init_database(self):
        """Initialize database from schema file"""
        # Read schema file
        schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
        
        try:
            with open(schema_path, 'r') as f:
                schema = f.read()
        except FileNotFoundError:
            # Fallback to inline schema if file doesn't exist
            await self._create_tables_inline()
            return
        
        # Execute schema
        async with aiosqlite.connect(self.db_path) as db:
            await db.executescript(schema)
            await db.commit()
            print("Database initialized from schema.sql")
        
        # Populate default data
        await self._populate_default_data()

    async def _create_tables_inline(self):
        """Fallback method if schema.sql doesn't exist"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    username TEXT,
                    xp INTEGER DEFAULT 0,
                    level INTEGER DEFAULT 1,
                    last_message_time INTEGER DEFAULT 0,
                    coins REAL DEFAULT 0.0
                )                 
            ''')
            await db.commit()

    async def _populate_default_data(self):
        """Add default shop items and other initial data"""
        async with aiosqlite.connect(self.db_path) as db:
            # Check if shop items exist
            cursor = await db.execute("SELECT COUNT(*) FROM shop_items")
            count = await cursor.fetchone()
            
            if count[0] == 0:
                default_items = [
                    ("XP Booster", "Double XP for 1 hour", 100, "utility", "xp_multiplier", "2.0", 1, 1),
                    ("Coin Magnet", "50% more coins for 30 minutes", 75, "utility", "coin_multiplier", "1.5", 1, 1),
                    ("VIP Badge", "Show off your VIP status", 5, "cosmetic", "badge", "vip", 0, 5),
                ]
                
                await db.executemany('''
                    INSERT INTO shop_items (name, description, price, category, effect_type, effect_value, is_consumable, min_level)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', default_items)
                await db.commit()
                print("Populated shop with default items")

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
                'last_message_time': user[4],
                'coins': user[5]
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
    
    async def update_user_coins(self, user_id, coin_gain):
        """"Add coins and handle level up"""
        user = await self.get_user(user_id)
        new_coins = user['coins'] + coin_gain

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE users SET coins = ? WHERE user_id = ?",
                (new_coins, str(user_id))
            )
            await db.commit()
    
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

    async def _get_all_users(self):
        """Get all users (for debugging)"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("SELECT * FROM users ORDER BY xp DESC")
            users = await cursor.fetchall()
            return [
                {
                    'user_id': user[0],
                    'username': user[1],
                    'xp': user[2],
                    'level': user[3],
                    'last_message_time': user[4],
                    'coins': user[5]
                }
                for user in users
            ]
    async def get_shop_items(self, category=None):
        """Get all shop items or by category"""
        async with aiosqlite.connect(self.db_path) as db:
            if category:
                cursor = await db.execute(
                    "SELECT * FROM shop_items WHERE category = ? ORDER BY price ASC",
                    (category,)
                )
            else:
                cursor = await db.execute("SELECT * FROM shop_items ORDER BY category, price ASC")
            
            items = await cursor.fetchall()
            return [
                {
                    'id': item[0],
                    'name': item[1],
                    'description': item[2],
                    'price': item[3],
                    'category': item[4],
                    'effect_type': item[5],
                    'effect_value': item[6],
                    'is_consumable': item[7],
                    'min_level': item[8]
                }
                for item in items
            ]

    async def purchase_item(self, user_id, item_id):
        """Purchase an item from the shop"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("SELECT * FROM shop_items WHERE item_id = ?", (item_id,))
            item = await cursor.fetchone()

            if not item:
                return {"success": False, "message": "Item not found"}
            
            user = await self.get_user(user_id)
            if user['coins'] < item[3]:
                return {"success": False, "message": "Not enough coins"}
            if user['level'] < item[8]:
                return {"success": False, "message": f"Requires level {item[8]}"}
            
            new_coins = user['coins'] - item[3]
            await db.execute(
                "UPDATE users SET coins = ? WHERE user_id = ?",
                (new_coins, str(user_id))
            )
            await db.execute('''
                INSERT OR REPLACE INTO user_inventory (user_id, item_id, quantity, purchased_at)
                VALUES (?, ?, COALESCE((SELECT quantity FROM user_inventory WHERE user_id = ? AND item_id = ?), 0) + 1, ?)                         
            ''', (str(user_id), item_id, str(user_id), item_id, int(time.time())))
            await db.commit()
            return {
                "success": True,
                "message": f"Purchased {item[1]} for {item[3]} coins",
                "item_name": item[1],
                "coins_remaining": new_coins
            }

    async def get_user_inventory(self, user_id):
        """Get user's inventory"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('''
                SELECT si.name, si.description, ui.quantity, si.effect_type, si.effect_value
                FROM user_inventory ui
                JOIN shop_items si ON ui.item_id = si.item_id
                WHERE ui.user_id = ?
                ORDER BY si.category, si.name
            ''', (str(user_id),))
            return await cursor.fetchall()