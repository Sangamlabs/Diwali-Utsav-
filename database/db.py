import os
import json
import asyncio
from datetime import datetime
from typing import Optional, Dict, Any, List
import config

try:
    from motor.motor_asyncio import AsyncIOMotorClient
    HAS_MOTOR = True
except ImportError:
    HAS_MOTOR = False

class Database:
    def __init__(self):
        self.use_mongo = False
        self.client = None
        self.db = None
        self.local_file = os.path.join(os.path.dirname(__file__), "..", "data", "local_db.json")
        self.local_lock = asyncio.Lock()
        self.local_data = {
            "users": {},
            "groups": {},
            "settings": {
                "loot_cooldown_hours": config.DEFAULT_LOOT_COOLDOWN_HOURS,
                "loot_coins": config.DEFAULT_LOOT_COINS,
                "daily_coins": config.DAILY_COINS,
            },
            "active_drops": {}
        }

    async def init(self):
        """Initialize connection to Mongo or load local fallback storage."""
        if config.MONGO_URI and HAS_MOTOR:
            try:
                self.client = AsyncIOMotorClient(config.MONGO_URI, serverSelectionTimeoutMS=4000)
                # Verify connection
                await self.client.admin.command('ping')
                self.db = self.client[config.DB_NAME]
                self.use_mongo = True
                print("Connected to MongoDB successfully!")
                return
            except Exception as e:
                print(f"MongoDB connection failed: {e}. Falling back to local storage.")
                self.use_mongo = False

        # Local storage fallback
        os.makedirs(os.path.dirname(self.local_file), exist_ok=True)
        if os.path.exists(self.local_file):
            try:
                with open(self.local_file, "r", encoding="utf-8") as f:
                    self.local_data = json.load(f)
            except Exception as e:
                print(f"Error loading local_db.json: {e}")
        else:
            await self._save_local()
        print("Using local JSON storage for database.")

    async def _save_local(self):
        """Save in-memory data to local JSON file safely."""
        os.makedirs(os.path.dirname(self.local_file), exist_ok=True)
        with open(self.local_file, "w", encoding="utf-8") as f:
            json.dump(self.local_data, f, indent=2, default=str)

    # --- User Operations ---
    async def get_user(self, user_id: int, user_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Fetch user or create if not exists."""
        uid_str = str(user_id)
        default_user = {
            "user_id": user_id,
            "username": (user_data.get("username") if user_data else "") or "",
            "first_name": (user_data.get("first_name") if user_data else "User") or "User",
            "coins": 1000,  # 1000 welcome coins!
            "inventory": {},
            "received_gifts": [],
            "last_daily": None,
            "last_loot": None,
            "last_diya": None,
            "last_wish": None,
            "last_mithai": None,
            "last_diwali": None,
            "wishes_sent": 0,
            "mithai_sent": 0,
            "gifts_sent": 0,
            "gifts_received": 0,
            "created_at": datetime.utcnow().isoformat()
        }

        if self.use_mongo:
            user = await self.db.users.find_one({"user_id": user_id})
            if not user:
                await self.db.users.insert_one(default_user)
                return default_user
            # Update username if changed
            if user_data and (user.get("username") != user_data.get("username") or user.get("first_name") != user_data.get("first_name")):
                await self.db.users.update_one(
                    {"user_id": user_id},
                    {"$set": {"username": user_data.get("username"), "first_name": user_data.get("first_name")}}
                )
            return user
        else:
            async with self.local_lock:
                if uid_str not in self.local_data["users"]:
                    self.local_data["users"][uid_str] = default_user
                    await self._save_local()
                else:
                    if user_data:
                        self.local_data["users"][uid_str]["username"] = user_data.get("username") or ""
                        self.local_data["users"][uid_str]["first_name"] = user_data.get("first_name") or "User"
                return self.local_data["users"][uid_str]

    async def update_user(self, user_id: int, update_dict: Dict[str, Any]):
        """Update user record fields."""
        uid_str = str(user_id)
        if self.use_mongo:
            await self.db.users.update_one({"user_id": user_id}, {"$set": update_dict})
        else:
            async with self.local_lock:
                if uid_str in self.local_data["users"]:
                    self.local_data["users"][uid_str].update(update_dict)
                    await self._save_local()

    async def add_coins(self, user_id: int, amount: int) -> int:
        """Add coins to user and return new balance."""
        user = await self.get_user(user_id)
        new_balance = max(0, user.get("coins", 0) + amount)
        await self.update_user(user_id, {"coins": new_balance})
        return new_balance

    async def deduct_coins(self, user_id: int, amount: int) -> bool:
        """Deduct coins from user if balance is sufficient."""
        user = await self.get_user(user_id)
        current = user.get("coins", 0)
        if current < amount:
            return False
        await self.update_user(user_id, {"coins": current - amount})
        return True

    async def add_gift_to_inventory(self, recipient_id: int, gift_id: str, sender_info: Optional[Dict[str, Any]] = None):
        """Add a gift item to user's inventory and log sender in received_gifts history."""
        user = await self.get_user(recipient_id)
        inventory = user.get("inventory", {})
        inventory[gift_id] = inventory.get(gift_id, 0) + 1
        gifts_recv = user.get("gifts_received", 0) + 1

        update_dict = {
            "inventory": inventory,
            "gifts_received": gifts_recv
        }

        if sender_info:
            history = list(user.get("received_gifts", []))
            history.insert(0, sender_info)
            if len(history) > 50:
                history = history[:50]
            update_dict["received_gifts"] = history

        await self.update_user(recipient_id, update_dict)

    # --- Group Chat Operations ---
    async def get_group(self, chat_id: int, title: str = "") -> Dict[str, Any]:
        """Fetch or register a group chat."""
        cid_str = str(chat_id)
        default_group = {
            "chat_id": chat_id,
            "title": title or "Diwali Group",
            "message_count": 0,
            "min_messages": config.DEFAULT_MIN_GROUP_MESSAGES,
            "drops_enabled": True,
            "last_drop_at": None,
            "joined_at": datetime.utcnow().isoformat()
        }

        if self.use_mongo:
            group = await self.db.groups.find_one({"chat_id": chat_id})
            if not group:
                await self.db.groups.insert_one(default_group)
                return default_group
            if title and group.get("title") != title:
                await self.db.groups.update_one({"chat_id": chat_id}, {"$set": {"title": title}})
            return group
        else:
            async with self.local_lock:
                if cid_str not in self.local_data["groups"]:
                    self.local_data["groups"][cid_str] = default_group
                    await self._save_local()
                else:
                    if title:
                        self.local_data["groups"][cid_str]["title"] = title
                return self.local_data["groups"][cid_str]

    async def update_group(self, chat_id: int, update_dict: Dict[str, Any]):
        """Update group chat settings."""
        cid_str = str(chat_id)
        if self.use_mongo:
            await self.db.groups.update_one({"chat_id": chat_id}, {"$set": update_dict})
        else:
            async with self.local_lock:
                if cid_str in self.local_data["groups"]:
                    self.local_data["groups"][cid_str].update(update_dict)
                    await self._save_local()

    async def increment_group_messages(self, chat_id: int) -> int:
        """Increment message count in group and return current count."""
        group = await self.get_group(chat_id)
        new_count = group.get("message_count", 0) + 1
        await self.update_group(chat_id, {"message_count": new_count})
        return new_count

    async def reset_group_messages(self, chat_id: int):
        """Reset group message counter to 0."""
        await self.update_group(chat_id, {"message_count": 0})

    # --- Settings Operations (Admin Dynamic Cooldowns etc) ---
    async def get_setting(self, key: str, default: Any = None) -> Any:
        """Retrieve dynamic bot settings."""
        if self.use_mongo:
            doc = await self.db.settings.find_one({"key": key})
            if doc:
                return doc.get("value", default)
            return default
        else:
            async with self.local_lock:
                return self.local_data.get("settings", {}).get(key, default)

    async def set_setting(self, key: str, value: Any):
        """Save a dynamic setting."""
        if self.use_mongo:
            await self.db.settings.update_one({"key": key}, {"$set": {"value": value}}, upsert=True)
        else:
            async with self.local_lock:
                if "settings" not in self.local_data:
                    self.local_data["settings"] = {}
                self.local_data["settings"][key] = value
                await self._save_local()

    # --- Active Loot Drops Operations ---
    async def create_drop(self, drop_id: str, drop_data: Dict[str, Any]):
        """Register a new drop in a group."""
        if self.use_mongo:
            await self.db.active_drops.insert_one(drop_data)
        else:
            async with self.local_lock:
                self.local_data["active_drops"][drop_id] = drop_data
                await self._save_local()

    async def get_drop(self, drop_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve an active drop by drop_id."""
        if self.use_mongo:
            return await self.db.active_drops.find_one({"drop_id": drop_id})
        else:
            async with self.local_lock:
                return self.local_data.get("active_drops", {}).get(drop_id)

    async def claim_drop(self, drop_id: str, user_id: int) -> tuple[bool, str]:
        """
        Attempt to claim a drop.
        Returns (success: bool, message: str)
        """
        drop = await self.get_drop(drop_id)
        if not drop or not drop.get("active", False):
            return False, "This drop has already expired or been fully claimed!"

        claimed_by = drop.get("claimed_by", [])
        if user_id in claimed_by:
            return False, "You have already claimed this drop!"

        claimed_by.append(user_id)
        max_claims = drop.get("max_claims", 1)
        active = len(claimed_by) < max_claims

        update_fields = {
            "claimed_by": claimed_by,
            "active": active
        }

        if self.use_mongo:
            await self.db.active_drops.update_one({"drop_id": drop_id}, {"$set": update_fields})
        else:
            async with self.local_lock:
                self.local_data["active_drops"][drop_id].update(update_fields)
                await self._save_local()

        return True, "Claim successful!"

    # --- Leaderboards & Statistics ---
    async def get_top_users(self, sort_by: str = "coins", limit: int = 10) -> List[Dict[str, Any]]:
        """Get top users sorted by coins, wishes_sent, or gifts_sent."""
        if self.use_mongo:
            cursor = self.db.users.find().sort(sort_by, -1).limit(limit)
            return await cursor.to_list(length=limit)
        else:
            async with self.local_lock:
                users = list(self.local_data.get("users", {}).values())
                users.sort(key=lambda x: x.get(sort_by, 0), reverse=True)
                return users[:limit]

    async def get_all_groups(self) -> List[Dict[str, Any]]:
        """List all registered groups for broadcast / stats."""
        if self.use_mongo:
            cursor = self.db.groups.find()
            return await cursor.to_list(length=10000)
        else:
            async with self.local_lock:
                return list(self.local_data.get("groups", {}).values())

    async def get_all_users(self) -> List[Dict[str, Any]]:
        """List all registered users for broadcast / stats."""
        if self.use_mongo:
            cursor = self.db.users.find()
            return await cursor.to_list(length=100000)
        else:
            async with self.local_lock:
                return list(self.local_data.get("users", {}).values())

    async def get_stats(self) -> Dict[str, Any]:
        """Aggregate overall bot statistics."""
        users = await self.get_all_users()
        groups = await self.get_all_groups()
        total_coins = sum(u.get("coins", 0) for u in users)
        total_wishes = sum(u.get("wishes_sent", 0) for u in users)
        total_gifts = sum(u.get("gifts_sent", 0) for u in users)

        return {
            "total_users": len(users),
            "total_groups": len(groups),
            "total_coins": total_coins,
            "total_wishes": total_wishes,
            "total_gifts": total_gifts,
            "storage_mode": "MongoDB" if self.use_mongo else "Local JSON"
        }

# Global database instance
db = Database()

