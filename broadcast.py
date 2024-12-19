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



@Client.on_message(filters.command("broadcast"))
async def broadcast_message(client, message):
    if message.from_user.id not in ADMINS:
        await message.reply("You are not authorized to use this command.")
        return
    
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

@Bot.on_message(filters.private & filters.command('broadcast') & filters.user(ADMINS))
async def send_text(client: Bot, message: Message):
    if message.reply_to_message:
        query = await full_userbase()
        broadcast_msg = message.reply_to_message
        total = 0
        successful = 0
        blocked = 0
        deleted = 0
        unsuccessful = 0

        pls_wait = await message.reply("<i>Broadcasting Message.. This will Take Some Time</i>")
        for chat_id in query:
            try:
                await broadcast_msg.copy(chat_id)
                successful += 1
            except FloodWait as e:
                await asyncio.sleep(e.x)
                await broadcast_msg.copy(chat_id)
                successful += 1
            except UserIsBlocked:
                await del_user(chat_id)
                blocked += 1
            except InputUserDeactivated:
                await del_user(chat_id)
                deleted += 1
            except:
                unsuccessful += 1
                pass
            total += 1

        status = f"""<b><u>Broadcast Completed</u>

Total Users: <code>{total}</code>
Successful: <code>{successful}</code>
Blocked Users: <code>{blocked}</code>
Deleted Accounts: <code>{deleted}</code>
Unsuccessful: <code>{unsuccessful}</code></b>"""

        return await pls_wait.edit(status)

    else:
        msg = await message.reply(REPLY_ERROR)
        await asyncio.sleep(8)
        await msg.delete()