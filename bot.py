import asyncio
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters
from config import BOT_TOKEN, SPIN_COST, GIFTS, WEBAPP_URL, WELCOME_MESSAGE, SPIN_REQUEST_MESSAGE, INSUFFICIENT_FUNDS, SPINNING_MESSAGE, WIN_MESSAGE, SOLD_MESSAGE, KEPT_MESSAGE
from database import db

# Хранение состояний пользователей
user_states = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    try:
        keyboard = [
            [InlineKeyboardButton("🎲 Испытать удачу!", callback_data="spin")],
            [InlineKeyboardButton("📊 Статистика", callback_data="stats")],
            [InlineKeyboardButton("🌐 Рулетка", web_app=WebAppInfo(url=WEBAPP_URL))]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        user = update.effective_user
        db.create_user(user.id, user.username or str(user.id))
        
        await update.message.reply_text(WELCOME_MESSAGE, reply_markup=reply_markup)
    except Exception as e:
        print(f"Error in start handler: {e}")

async def spin_roulette(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопки 'Испытать удачу'"""
    try:
        query = update.callback_query
        user_id = query.from_user.id
        
        # Get user data
        user_data = db.get_user(user_id)
        if not user_data:
            await query.answer("Пожалуйста, начните с команды /start")
            return
        
        # Запрашиваем у пользователя передачу звезд
        keyboard = [
            [InlineKeyboardButton("💫 Передать звезды", callback_data=f"transfer_{SPIN_COST}")],
            [InlineKeyboardButton("❌ Отменить", callback_data="cancel_spin")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.message.edit_text(
            SPIN_REQUEST_MESSAGE.format(SPIN_COST),
            reply_markup=reply_markup
        )
    except Exception as e:
        print(f"Error in spin_roulette handler: {e}")

async def handle_transfer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик передачи звезд"""
    try:
        query = update.callback_query
        user_id = query.from_user.id
        action, amount = query.data.split('_')
        amount = int(amount)
        
        if action == "transfer":
            # Проверяем баланс
            user_data = db.get_user(user_id)
            if not user_data or user_data['stars'] < amount:
                await query.answer(INSUFFICIENT_FUNDS.format(amount), show_alert=True)
                return
            
            # Списываем звезды
            db.update_stars(user_id, -amount)
            db.add_transaction(user_id, -amount, "spin_cost")
            
            # Запускаем анимацию
            await query.message.edit_text(SPINNING_MESSAGE)
            await asyncio.sleep(2)
            
            # Рассчитываем выигрыш
            total_weight = sum(gift["weight"] for gift in GIFTS)
            random_value = random.randint(1, total_weight)
            current_weight = 0
            
            for gift in GIFTS:
                current_weight += gift["weight"]
                if random_value <= current_weight:
                    won_gift = gift
                    break
            
            # Показываем результат
            keyboard = [
                [
                    InlineKeyboardButton("💰 Продать", callback_data=f"sell_{won_gift['value']}"),
                    InlineKeyboardButton("✨ Оставить", callback_data=f"keep_{won_gift['value']}")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.message.edit_text(
                WIN_MESSAGE.format(won_gift['name']),
                reply_markup=reply_markup
            )
            
            # Обновляем статистику
            db.update_game_stats(user_id, won_gift['value'])
        
        elif action == "cancel":
            keyboard = [
                [InlineKeyboardButton("🎲 Испытать удачу!", callback_data="spin")],
                [InlineKeyboardButton("📊 Статистика", callback_data="stats")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.edit_text("❌ Вращение отменено", reply_markup=reply_markup)
    except Exception as e:
        print(f"Error in handle_transfer handler: {e}")

async def handle_gift_decision(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик решения о подарке"""
    try:
        query = update.callback_query
        user_id = query.from_user.id
        action, value = query.data.split('_')
        value = int(value)
        
        if action == "sell":
            # Начисляем звезды
            db.update_stars(user_id, value)
            db.add_transaction(user_id, value, "gift_sold")
            
            # Обновляем сообщение
            keyboard = [
                [InlineKeyboardButton("🎲 Испытать удачу снова!", callback_data="spin")],
                [InlineKeyboardButton("📊 Статистика", callback_data="stats")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.edit_text(
                SOLD_MESSAGE.format(value),
                reply_markup=reply_markup
            )
        
        elif action == "keep":
            # Начисляем звезды
            db.update_stars(user_id, value)
            db.add_transaction(user_id, value, "gift_kept")
            
            # Обновляем сообщение
            keyboard = [
                [InlineKeyboardButton("🎲 Испытать удачу снова!", callback_data="spin")],
                [InlineKeyboardButton("📊 Статистика", callback_data="stats")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.edit_text(
                KEPT_MESSAGE.format(value),
                reply_markup=reply_markup
            )
    except Exception as e:
        print(f"Error in handle_gift_decision handler: {e}")

async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик просмотра статистики"""
    try:
        query = update.callback_query
        user_id = query.from_user.id
        
        stats = db.get_user_stats(user_id)
        if not stats:
            await query.answer("Статистика недоступна. Начните с /start")
            return
        
        stars, total_games, total_won = stats
        
        stats_text = (
            "📊 Ваша статистика:\n\n"
            f"⭐️ Текущий баланс: {stars} звезд\n"
            f"🎮 Всего игр: {total_games}\n"
            f"💰 Всего выиграно: {total_won} звезд\n"
        )
        
        keyboard = [
            [InlineKeyboardButton("🎲 Испытать удачу!", callback_data="spin")],
            [InlineKeyboardButton("🔄 В главное меню", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.message.edit_text(stats_text, reply_markup=reply_markup)
    except Exception as e:
        print(f"Error in show_stats handler: {e}")

async def back_to_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик возврата в главное меню"""
    try:
        query = update.callback_query
        keyboard = [
            [InlineKeyboardButton("🎲 Испытать удачу!", callback_data="spin")],
            [InlineKeyboardButton("📊 Статистика", callback_data="stats")],
            [InlineKeyboardButton("🌐 Рулетка", web_app=WebAppInfo(url=WEBAPP_URL))]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.message.edit_text(WELCOME_MESSAGE, reply_markup=reply_markup)
    except Exception as e:
        print(f"Error in back_to_main handler: {e}")

async def main():
    """Запуск бота"""
    try:
        # Создаем приложение
        application = Application.builder().token(BOT_TOKEN).build()
        
        # Добавляем обработчики
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CallbackQueryHandler(spin_roulette, pattern="^spin$"))
        application.add_handler(CallbackQueryHandler(show_stats, pattern="^stats$"))
        application.add_handler(CallbackQueryHandler(back_to_main, pattern="^back_to_main$"))
        application.add_handler(CallbackQueryHandler(handle_transfer, pattern="^transfer_\d+$"))
        application.add_handler(CallbackQueryHandler(handle_transfer, pattern="^cancel_spin$"))
        application.add_handler(CallbackQueryHandler(handle_gift_decision, pattern="^(sell|keep)_\d+$"))
        
        # Запускаем бота
        await application.initialize()
        await application.start()
        await application.run_polling(allowed_updates=Update.ALL_TYPES)
    except Exception as e:
        print(f"Error in main: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 