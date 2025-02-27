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
        user = update.effective_user
        
        # Создаем пользователя в базе данных
        await db.create_user(user.id, user.username or str(user.id))
        
        # Создаем клавиатуру с кнопками
        keyboard = [
            [InlineKeyboardButton("🎲 Испытать удачу!", callback_data="spin")],
            [InlineKeyboardButton("📊 Статистика", callback_data="stats")],
            [InlineKeyboardButton("🌐 Играть в рулетку", web_app=WebAppInfo(url=WEBAPP_URL))]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Отправляем приветственное сообщение с кнопками
        await update.message.reply_text(
            text=WELCOME_MESSAGE,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    except Exception as e:
        print(f"Error in start handler: {e}")
        await update.message.reply_text("Произошла ошибка при запуске бота. Пожалуйста, попробуйте позже.")

async def spin_roulette(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопки 'Испытать удачу'"""
    try:
        query = update.callback_query
        await query.answer()  # Отвечаем на callback query
        
        user_id = query.from_user.id
        
        # Получаем данные пользователя
        user = await db.get_user(user_id)
        if not user:
            await query.message.reply_text("Пожалуйста, начните с команды /start")
            return
        
        # Проверяем баланс
        if user['stars'] < SPIN_COST:
            await query.message.reply_text(INSUFFICIENT_FUNDS.format(SPIN_COST))
            return
        
        # Запрашиваем подтверждение
        keyboard = [
            [InlineKeyboardButton("✅ Подтвердить", callback_data=f"confirm_spin_{SPIN_COST}")],
            [InlineKeyboardButton("❌ Отменить", callback_data="cancel_spin")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.message.edit_text(
            SPIN_REQUEST_MESSAGE.format(SPIN_COST),
            reply_markup=reply_markup
        )
    except Exception as e:
        print(f"Error in spin_roulette handler: {e}")
        await query.message.reply_text("Произошла ошибка. Пожалуйста, попробуйте позже.")

async def handle_spin_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик подтверждения вращения"""
    try:
        query = update.callback_query
        await query.answer()  # Отвечаем на callback query
        
        if query.data == "cancel_spin":
            keyboard = [
                [InlineKeyboardButton("🎲 Испытать удачу!", callback_data="spin")],
                [InlineKeyboardButton("📊 Статистика", callback_data="stats")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.edit_text("❌ Вращение отменено", reply_markup=reply_markup)
            return
            
        user_id = query.from_user.id
        action, amount = query.data.split('_')[1:]
        amount = int(amount)
        
        # Проверяем баланс
        user = await db.get_user(user_id)
        if not user or user['stars'] < amount:
            await query.message.reply_text(INSUFFICIENT_FUNDS.format(amount))
            return
        
        # Списываем звезды
        await db.update_stars(user_id, -amount)
        await db.add_transaction(user_id, -amount, "spin_cost")
        
        # Показываем анимацию
        await query.message.edit_text(SPINNING_MESSAGE)
        await asyncio.sleep(2)
        
        # Определяем выигрыш
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
                InlineKeyboardButton("💝 Забрать подарок", callback_data=f"keep_{won_gift['value']}"),
                InlineKeyboardButton("💰 Продать", callback_data=f"sell_{won_gift['value']}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.message.edit_text(
            WIN_MESSAGE.format(won_gift['name']),
            reply_markup=reply_markup
        )
        
        # Обновляем статистику
        await db.update_game_stats(user_id, won_gift['value'])
        
    except Exception as e:
        print(f"Error in handle_spin_confirmation handler: {e}")
        await query.message.reply_text("Произошла ошибка. Пожалуйста, попробуйте позже.")

async def handle_gift_decision(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик решения о подарке"""
    try:
        query = update.callback_query
        await query.answer()  # Отвечаем на callback query
        
        user_id = query.from_user.id
        action, value = query.data.split('_')
        value = int(value)
        
        if action == "sell":
            # Начисляем звезды
            await db.update_stars(user_id, value)
            await db.add_transaction(user_id, value, "gift_sold")
            
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
            # Начисляем звезды и отправляем подарок
            await db.update_stars(user_id, value)
            await db.add_transaction(user_id, value, "gift_kept")
            
            # Отправляем подарок (эмодзи сердечка)
            await query.message.reply_text("💝")
            
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
        await query.message.reply_text("Произошла ошибка. Пожалуйста, попробуйте позже.")

async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик просмотра статистики"""
    try:
        query = update.callback_query
        await query.answer()  # Отвечаем на callback query
        
        user_id = query.from_user.id
        
        stats = await db.get_user_stats(user_id)
        if not stats:
            await query.message.reply_text("Статистика недоступна. Начните с /start")
            return
        
        stars, total_games, total_won, biggest_win, total_spent = stats
        
        stats_text = (
            "📊 Ваша статистика:\n\n"
            f"⭐️ Текущий баланс: {stars} звезд\n"
            f"🎮 Всего игр: {total_games}\n"
            f"💰 Всего выиграно: {total_won} звезд\n"
            f"🏆 Лучший выигрыш: {biggest_win} звезд\n"
            f"💸 Всего потрачено: {total_spent} звезд\n"
            f"📈 Общий профит: {total_won - total_spent} звезд"
        )
        
        keyboard = [
            [InlineKeyboardButton("🎲 Испытать удачу!", callback_data="spin")],
            [InlineKeyboardButton("🔄 В главное меню", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.message.edit_text(stats_text, reply_markup=reply_markup)
    except Exception as e:
        print(f"Error in show_stats handler: {e}")
        await query.message.reply_text("Произошла ошибка. Пожалуйста, попробуйте позже.")

async def back_to_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик возврата в главное меню"""
    try:
        query = update.callback_query
        await query.answer()  # Отвечаем на callback query
        
        keyboard = [
            [InlineKeyboardButton("🎲 Испытать удачу!", callback_data="spin")],
            [InlineKeyboardButton("📊 Статистика", callback_data="stats")],
            [InlineKeyboardButton("🌐 Играть в рулетку", web_app=WebAppInfo(url=WEBAPP_URL))]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.message.edit_text(WELCOME_MESSAGE, reply_markup=reply_markup)
    except Exception as e:
        print(f"Error in back_to_main handler: {e}")
        await query.message.reply_text("Произошла ошибка. Пожалуйста, попробуйте позже.")

async def main():
    """Запуск бота"""
    try:
        # Создаем приложение
        application = Application.builder().token(BOT_TOKEN).build()
        
        # Добавляем обработчики
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CallbackQueryHandler(spin_roulette, pattern="^spin$"))
        application.add_handler(CallbackQueryHandler(handle_spin_confirmation, pattern="^confirm_spin_\d+$"))
        application.add_handler(CallbackQueryHandler(handle_spin_confirmation, pattern="^cancel_spin$"))
        application.add_handler(CallbackQueryHandler(show_stats, pattern="^stats$"))
        application.add_handler(CallbackQueryHandler(back_to_main, pattern="^back_to_main$"))
        application.add_handler(CallbackQueryHandler(handle_gift_decision, pattern="^(sell|keep)_\d+$"))
        
        # Запускаем бота
        print("Bot started...")
        await application.initialize()
        await application.start()
        await application.run_polling(allowed_updates=Update.ALL_TYPES)
    except Exception as e:
        print(f"Error in main: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 