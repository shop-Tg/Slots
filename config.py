import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Bot Configuration
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Web App Configuration
WEBAPP_URL = "https://shop-tg.github.io/Slots/"

# Welcome Message
WELCOME_MESSAGE = """
<b>🎰 Добро пожаловать в Crypto Slots!</b>

🌟 <b>Нажмите кнопку ниже, чтобы начать игру!</b>

<i>🎮 Вас ждут крутые призы и увлекательная игра!</i>
"""

# Game Settings
SPIN_COST = 25  # Cost in stars to spin the roulette
GIFTS = [
    {"name": "💝 15 Stars", "value": 15, "weight": 70},  # 70% chance
    {"name": "💝 25 Stars", "value": 25, "weight": 15},  # 15% chance
    {"name": "💝 35 Stars", "value": 35, "weight": 8},   # 8% chance
    {"name": "💝 50 Stars", "value": 50, "weight": 4},   # 4% chance
    {"name": "💝 100 Stars", "value": 100, "weight": 2}, # 2% chance
    {"name": "💝 250 Stars", "value": 250, "weight": 1}  # 1% chance
]

# Messages
SPIN_REQUEST_MESSAGE = "💫 <b>Подтвердите списание {} ⭐️ для вращения рулетки</b>"
INSUFFICIENT_FUNDS = "❌ <b>У вас недостаточно звезд!</b>\nНеобходимо: {} ⭐️"
SPINNING_MESSAGE = "🎰 <b>Крутим рулетку...</b>"
WIN_MESSAGE = "🎉 <b>Поздравляем!</b>\n\n🎁 Вам выпало: {}\n\n<i>Что хотите сделать с подарком?</i>"
SOLD_MESSAGE = "💰 <b>Вы продали подарок</b> и получили <b>{} ⭐️</b>"
KEPT_MESSAGE = "✨ <b>Вы оставили себе подарок</b>\n🎁 Получено: <b>{} ⭐️</b>"

# Database settings
DATABASE_FILE = "bot_database.db" 