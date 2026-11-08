@echo off
title Diwali Telegram Bot
echo ======================================================
echo           Starting Diwali Telegram Bot
echo ======================================================

IF NOT EXIST ".env" (
    echo [WARNING] .env file not found!
    echo Creating .env from .env.example...
    copy .env.example .env
    echo Please edit .env with your BOT_TOKEN and ADMIN_IDS before running!
    pause
    exit /b
)

python main.py
pause

