from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from database import db
from config import GIFTS, SPIN_COST
import random
import json
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# CORS middleware с расширенными настройками
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Content-Security-Policy"] = "default-src 'self' https://unpkg.com https://cdn.jsdelivr.net 'unsafe-inline' 'unsafe-eval'"
    return response

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    logger.info("Rendering index.html")
    try:
        # Создаем тестового пользователя с ID 1 для демонстрации
        test_user_id = 1
        user = await db.get_user(test_user_id)
        if not user:
            await db.create_user(test_user_id, "test_user")
            user = await db.get_user(test_user_id)

        stats = await db.get_user_stats(test_user_id) or (100, 0, 0, 0, 0)
        leaderboard = await db.get_leaderboard()
        
        response = templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "user": user,
                "stats": {
                    "stars": stats[0],
                    "total_games": stats[1],
                    "total_won": stats[2],
                    "biggest_win": stats[3],
                    "total_spent": stats[4]
                },
                "spin_cost": SPIN_COST,
                "gifts": GIFTS,
                "leaderboard": leaderboard[:10]  # Top 10 players
            }
        )
        logger.info("Successfully rendered index.html")
        return response
    except Exception as e:
        logger.error(f"Error rendering index.html: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/user/{user_id}")
async def get_user_info(user_id: int):
    logger.info(f"Getting user info for ID: {user_id}")
    try:
        user = await db.get_user(user_id)
        if not user:
            await db.create_user(user_id, str(user_id))
            user = await db.get_user(user_id)
            
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
            
        logger.info(f"User data: {user}")
        return user
    except Exception as e:
        logger.error(f"Error getting user info: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/stats/{user_id}")
async def get_user_stats(user_id: int):
    logger.info(f"Getting stats for user ID: {user_id}")
    try:
        stats = await db.get_user_stats(user_id)
        if not stats:
            return {
                "stars": 0,
                "total_games": 0,
                "total_won": 0,
                "biggest_win": 0,
                "total_spent": 0
            }
            
        logger.info(f"User stats: {stats}")
        return {
            "stars": stats[0],
            "total_games": stats[1],
            "total_won": stats[2],
            "biggest_win": stats[3],
            "total_spent": stats[4]
        }
    except Exception as e:
        logger.error(f"Error getting user stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/leaderboard")
async def get_leaderboard():
    try:
        return await db.get_leaderboard()
    except Exception as e:
        logger.error(f"Error getting leaderboard: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/spin")
async def spin_roulette(request: Request):
    try:
        data = await request.json()
        user_id = data.get("user_id")
        
        if not user_id:
            raise HTTPException(status_code=400, detail="User ID is required")
            
        logger.info(f"Spinning roulette for user ID: {user_id}")
        
        # Check if user has enough stars
        user = await db.get_user(user_id)
        if not user or user['stars'] < SPIN_COST:
            raise HTTPException(status_code=400, detail="Insufficient stars")
        
        # Deduct spin cost
        if not await db.update_stars(user_id, -SPIN_COST):
            raise HTTPException(status_code=400, detail="Failed to deduct stars")
        
        # Add transaction for spin cost
        await db.add_transaction(user_id, -SPIN_COST, "spin_cost")
        
        # Always return 15 stars (first gift)
        won_gift = GIFTS[0]
        
        # Update game stats
        await db.update_game_stats(user_id, won_gift['value'])
        
        logger.info(f"User won: {won_gift}")
        return {
            "gift": won_gift,
            "new_balance": user['stars'] - SPIN_COST
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during spin: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/claim")
async def claim_gift(request: Request):
    try:
        data = await request.json()
        user_id = data.get("user_id")
        amount = data.get("amount")
        action = data.get("action")
        
        if not all([user_id, amount, action]):
            raise HTTPException(status_code=400, detail="Missing required fields")
            
        if action not in ["sell", "keep"]:
            raise HTTPException(status_code=400, detail="Invalid action")
        
        logger.info(f"Claiming gift for user ID: {user_id}, amount: {amount}, action: {action}")
        
        # Add stars to user's balance
        if not await db.update_stars(user_id, amount):
            raise HTTPException(status_code=400, detail="Failed to update stars")
        
        # Record transaction
        await db.add_transaction(user_id, amount, f"gift_{action}", amount)
        
        return {"status": "success", "message": f"Gift {action} for {amount} stars"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error claiming gift: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error") 