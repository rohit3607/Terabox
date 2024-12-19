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

load_dotenv('config.env', override=True)

logging.basicConfig(level=logging.INFO)


# MongoDB connection setup
mongo_uri = os.environ.get('MONGO_URI', 'mongodb+srv://Mrdaxx123:Mrdaxx123@cluster0.q1da65h.mongodb.net/?retryWrites=true&w=majority')
if not mongo_uri:
    logging.error("MONGO_URI variable is missing! Exiting now")
    exit(1)


dbclient = pymongo.MongoClient(mongo_uri)
database = dbclient[terabox_bot]
user_data = database['users']



async def present_user(user_id : int):
    found = user_data.find_one({'_id': user_id})
    return bool(found)

async def add_user(user_id: int):
    user_data.insert_one({'_id': user_id})
    return

async def full_userbase():
    user_docs = user_data.find()
    user_ids = []
    for doc in user_docs:
        user_ids.append(doc['_id'])

    return user_ids

async def del_user(user_id: int):
    user_data.delete_one({'_id': user_id})
    return

# Fetch admin IDs from environment variables
admin_ids = os.environ.get('ADMINS', '')
if len(admin_ids) == 0:
    logging.error("ADMINS variable is missing! Exiting now")
    exit(1)

# Convert admin IDs to a list of integers
admin_user_ids = [int(admin_id.strip()) for admin_id in admin_ids.split('7328629001,6955387260') if admin_id.strip().isdigit()]


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