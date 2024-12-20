from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
import logging
import asyncio
from pyrogram.enums import ChatMemberStatus
from pymongo import MongoClient
from dotenv import load_dotenv
import os
import requests
import aria2p

load_dotenv('config.env', override=True)
logging.basicConfig(level=logging.INFO)

app = Client


# MongoDB connection setup
mongo_uri = os.environ.get('MONGO_URI', 'mongodb+srv://Mrdaxx123:Mrdaxx123@cluster0.q1da65h.mongodb.net/?retryWrites=true&w=majority')
if not mongo_uri:
    logging.error("MONGO_URI variable is missing! Exiting now")
    exit(1)

dbclient = MongoClient(mongo_uri)
database = dbclient['terabox_bot']
user_data = database['users']

# Fetching data (example query)
users = user_data.find({})  # Example: Retrieve all users

# Now, interacting with aria2:
aria2 = aria2p.API(
    aria2p.Client(
        host="http://localhost",
        port=6800,
        secret=""  # Set the correct secret if required
    )
)

# Example: Add a download and update MongoDB with download info
try:
    download = aria2.add(["http://example.com/file.zip"])  # Use 'add' instead of 'add_uri'
    download_id = download.gid

    # Update MongoDB with the download status
    user_data.update_one(
        {"username": "user123"},
        {"$set": {"downloads": [{"download_id": download_id, "status": "started"}]}}
    )
except Exception as e:
    logging.error(f"Failed to add download: {e}")

async def present_user(user_id: int):
    found = user_data.find_one({'_id': user_id})
    return bool(found)

async def add_user(user_id: int):
    user_data.insert_one({'_id': user_id})

async def full_userbase():
    user_docs = user_data.find()
    return [doc['_id'] for doc in user_docs]

async def del_user(user_id: int):
    user_data.delete_one({'_id': user_id})

# Fetch admin IDs from environment variables
admin_ids = os.environ.get('ADMINS', '7328629001,6955387260')
if len(admin_ids) == 0:
    logging.error("ADMINS variable is missing! Exiting now")
    exit(1)
admin_user_ids = [int(admin_id.strip()) for admin_id in admin_ids.split('7328629001,6955387260') if admin_id.strip().isdigit()]

@app.on_message(filters.private & filters.text('/broadcast') & filters.user(admin_user_ids))
async def send_text(client: Client, message: Message):
    if message.reply_to_message:
        query = await full_userbase()
        broadcast_msg = message.reply_to_message
        total, successful, blocked, deleted, unsuccessful = 0, 0, 0, 0, 0

        pls_wait = await message.reply("<i>Broadcasting Message... This will take some time</i>")
        for chat_id in query:
            try:
                await broadcast_msg.copy(chat_id)
                successful += 1
            except FloodWait as e:
                await asyncio.sleep(e.value)
                await broadcast_msg.copy(chat_id)
                successful += 1
            except UserIsBlocked:
                await del_user(chat_id)
                blocked += 1
            except InputUserDeactivated:
                await del_user(chat_id)
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
        await pls_wait.edit(status)
    else:
        msg = await message.reply("<i>Please reply to a message to broadcast it.</i>")
        await asyncio.sleep(8)
        await msg.delete()

@app.on_message(filters.text('/users') & filters.private & filters.user(admin_user_ids))
async def get_users(client: Client, message: Message):
    # Corrected the text string with quotes
    msg = await client.send_message(chat_id=message.chat.id, text="Ruk jaa")  
    try:
        users = await full_userbase()
        await msg.edit(f"{len(users)} users are using this bot")
    except Exception as e:
        logging.error(f"Error in /users command: {e}")
        await msg.edit("An error occurred while fetching user data.")