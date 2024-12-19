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

# Fetch admin IDs from environment variables
admin_ids = os.environ.get('ADMINS', '')
if len(admin_ids) == 0:
    logging.error("ADMINS variable is missing! Exiting now")
    exit(1)

# Convert admin IDs to a list of integers
admin_user_ids = [int(admin_id.strip()) for admin_id in admin_ids.split(',') if admin_id.strip().isdigit()]


@Client.on_message(filters.private & filters.command('broadcast') & filters.user(admin_user_ids))
async def send_text(client: Bot, message: Message):
    if message.reply_to_message:
        query = get_all_users()  # Fetch all user IDs from the database
        broadcast_msg = message.reply_to_message
        total = 0
        successful = 0
        blocked = 0
        deleted = 0
        unsuccessful = 0

        pls_wait = await message.reply("<i>Broadcasting Message.. This will take some time</i>")
        for chat_id in query:
            try:
                await broadcast_msg.copy(chat_id)
                successful += 1
            except FloodWait as e:
                await asyncio.sleep(e.value)
                await broadcast_msg.copy(chat_id)
                successful += 1
            except UserIsBlocked:
                await del_user(chat_id)  # Remove blocked user from the database
                blocked += 1
            except InputUserDeactivated:
                await del_user(chat_id)  # Remove deactivated user from the database
                deleted += 1
            except Exception as e:
                logging.error(f"Failed to broadcast to {chat_id}: {e}")
                unsuccessful += 1
            total += 1

        status = f"""<b><u>Broadcast Completed</u></b>

<b>Total Users:</b> <code>{total}</code>
<b>Successful:</b> <code>{successful}</code>
<b>Blocked Users:</b> <code>{blocked}</code>
<b>Deleted Accounts:</b> <code>{deleted}</code>
<b>Unsuccessful:</b> <code>{unsuccessful}</code>"""

        return await pls_wait.edit(status)

    else:
        msg = await message.reply("<i>Please reply to a message to broadcast it.</i>")
        await asyncio.sleep(8)
        await msg.delete()