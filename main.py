import logging
from aiogram import Bot, Dispatcher, types, executor
from config import BOT_TOKEN, WEBAPP_URL, WELCOME_MESSAGE

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    """Обработчик команды /start"""
    try:
        # Создаем кнопку для перехода в веб-приложение
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(
            types.InlineKeyboardButton(
                text="🎮 Играть",
                web_app=types.WebAppInfo(url=WEBAPP_URL)
            )
        )
        
        # Отправляем приветственное сообщение с кнопкой
        await message.answer(
            text=WELCOME_MESSAGE,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        logger.info(f"User {message.from_user.id} started the bot")
    except Exception as e:
        logger.error(f"Error in start command: {e}")
        await message.answer("Произошла ошибка. Пожалуйста, попробуйте позже.")

if __name__ == '__main__':
    logger.info("Starting bot...")
    executor.start_polling(dp, skip_updates=True) 