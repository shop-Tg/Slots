from postgrest import PostgrestClient
from config import SUPABASE_URL, SUPABASE_KEY, DATABASE_TABLES
from datetime import datetime
import asyncio

class Database:
    def __init__(self):
        # Initialize PostgrestClient with Supabase URL and key
        self.client = PostgrestClient(
            base_url=f"{SUPABASE_URL}",
            headers={
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}"
            }
        )
        self._ensure_tables()

    def _ensure_tables(self):
        # В Supabase таблицы создаются через веб-интерфейс или миграции
        # Этот метод оставляем пустым
        pass

    async def get_user(self, user_id):
        response = await self.client.from_("users").select(
            "user_id,username,stars,total_games,total_won,biggest_win,total_spent,last_spin,created_at"
        ).eq("user_id", user_id).execute()
        return response.data[0] if response.data else None

    async def create_user(self, user_id, username):
        if not await self.get_user(user_id):
            await self.client.from_("users").insert({
                'user_id': user_id,
                'username': username,
                'stars': 100,  # Начальный бонус
                'total_games': 0,
                'total_won': 0,
                'biggest_win': 0,
                'total_spent': 0,
                'last_spin': None
            }).execute()

    async def update_stars(self, user_id, amount):
        user = await self.get_user(user_id)
        if user:
            new_stars = user['stars'] + amount
            if new_stars >= 0:
                await self.client.from_("users").update({
                    'stars': new_stars,
                    'total_spent': user['total_spent'] + (-amount if amount < 0 else 0)
                }).eq("user_id", user_id).execute()
                return True
        return False

    async def add_transaction(self, user_id, amount, type_, gift_value=None):
        await self.client.from_("transactions").insert({
            'user_id': user_id,
            'amount': amount,
            'type': type_,
            'gift_value': gift_value,
            'timestamp': datetime.utcnow().isoformat()
        }).execute()

    async def get_user_stats(self, user_id):
        user = await self.get_user(user_id)
        if user:
            return (
                user.get('stars', 0),
                user.get('total_games', 0),
                user.get('total_won', 0),
                user.get('biggest_win', 0),
                user.get('total_spent', 0)
            )
        return None

    async def update_game_stats(self, user_id, won_amount):
        user = await self.get_user(user_id)
        if user:
            await self.client.from_("users").update({
                'total_games': user.get('total_games', 0) + 1,
                'total_won': user.get('total_won', 0) + won_amount,
                'biggest_win': max(user.get('biggest_win', 0), won_amount),
                'last_spin': datetime.utcnow().isoformat()
            }).eq("user_id", user_id).execute()

    async def get_leaderboard(self):
        response = await self.client.from_("leaderboard").select(
            "user_id,username,stars,total_games,total_won,biggest_win,total_spent,net_profit"
        ).execute()
        return response.data if response.data else []

db = Database() 