from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
import logging
import asyncio
from datetime import datetime
from pyrogram.enums import ChatMemberStatus
from dotenv import load_dotenv
from os import environ
import os
import time
from status import format_progress_bar

from pymongo import MongoClient

# MongoDB connection setup
mongo_uri = os.environ.get('MONGO_URI', '')
if not mongo_uri:
    logging.error("MONGO_URI variable is missing! Exiting now")
    exit(1)

client = MongoClient(mongo_uri)
db = client['terabox_bot']
user_collection = db['users']

# Function to add a user ID to the database
def add_user(user_id):
    if not user_collection.find_one({"user_id": user_id}):
        user_collection.insert_one({"user_id": user_id})

# Function to get all user IDs from the database
def get_all_users():
    return [doc["user_id"] for doc in user_collection.find()]



@Client.on_message(filters.command("broadcast") & filters.user(ADMINS))
async def broadcast_message(client, message):
    if len(message.command) < 2:
        await message.reply("Please provide a message to broadcast.")
        return

    broadcast_message = message.text.split(' ', 1)[1]
    user_ids = get_all_users()

    for user_id in user_ids:
        try:
            await client.send_message(chat_id=user_id, text=broadcast_message)
        except Exception as e:
            logging.error(f"Failed to send message to {user_id}: {e}")