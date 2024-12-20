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
from video import download_video, upload_video
from web import keep_alive
from pymongo import MongoClient
import requests
import aria2p

load_dotenv('config.env', override=True)

logging.basicConfig(level=logging.INFO)

api_id = os.environ.get('TELEGRAM_API', '')
if len(api_id) == 0:
    logging.error("TELEGRAM_API variable is missing! Exiting now")
    exit(1)

api_hash = os.environ.get('TELEGRAM_HASH', '')
if len(api_hash) == 0:
    logging.error("TELEGRAM_HASH variable is missing! Exiting now")
    exit(1)
    
bot_token = os.environ.get('BOT_TOKEN', '')
if len(bot_token) == 0:
    logging.error("BOT_TOKEN variable is missing! Exiting now")
    exit(1)
dump_id = os.environ.get('DUMP_CHAT_ID', '')
if len(dump_id) == 0:
    logging.error("DUMP_CHAT_ID variable is missing! Exiting now")
    exit(1)
else:
    dump_id = int(dump_id)

fsub_id = os.environ.get('FSUB_ID', '')
if len(fsub_id) == 0:
    logging.error("FSUB_ID variable is missing! Exiting now")
    exit(1)
else:
    fsub_id = int(fsub_id)

# MongoDB connection setup
mongo_uri = os.environ.get('MONGO_URI', 'mongodb+srv://Mrdaxx123:Mrdaxx123@cluster0.q1da65h.mongodb.net/?retryWrites=true&w=majority')
if not mongo_uri:
    logging.error("MONGO_URI variable is missing! Exiting now")
    exit(1)

app = Client("my_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

@app.on_message(filters.command("start"))
async def start_command(client, message):
    id = message.from_user.id
    if not await present_user(id):
        try:
            await add_user(id)
        except:
            pass

    sticker_message = await message.reply_sticker("CAACAgIAAxkBAAEYonplzwrczhVu3I6HqPBzro3L2JU6YAACvAUAAj-VzAoTSKpoG9FPRjQE")
    await asyncio.sleep(2)
    await sticker_message.delete()
    user_mention = message.from_user.mention
    reply_message = f"ᴡᴇʟᴄᴏᴍᴇ, {user_mention}.\n\n🌟 ɪ ᴀᴍ ᴀ ᴛᴇʀᴀʙᴏx ᴅᴏᴡɴʟᴏᴀᴅᴇʀ ʙᴏᴛ. sᴇɴᴅ ᴍᴇ ᴀɴʏ ᴛᴇʀᴀʙᴏx ʟɪɴᴋ ɪ ᴡɪʟʟ ᴅᴏᴡɴʟᴏᴀᴅ ᴡɪᴛʜɪɴ ғᴇᴡ sᴇᴄᴏɴᴅs ᴀɴᴅ sᴇɴᴅ ɪᴛ ᴛᴏ ʏᴏᴜ ✨."
    join_button = InlineKeyboardButton("ᴊᴏɪɴ ❤️🚀", url="https://t.me/Javpostr")
    developer_button = InlineKeyboardButton("ᴅᴇᴠᴇʟᴏᴘᴇʀ ⚡️", url="https://t.me/rohit_1888")
    reply_markup = InlineKeyboardMarkup([[join_button, developer_button]])
    video_file_id = "/app/Jet-Mirror.mp4"
    if os.path.exists(video_file_id):
        await client.send_video(
            chat_id=message.chat.id,
            video=video_file_id,
            caption=reply_message,
            reply_markup=reply_markup
        )
    else:
        await message.reply_text(reply_message, reply_markup=reply_markup)

async def is_user_member(client, user_id):
    try:
        member = await client.get_chat_member(fsub_id, user_id)
        logging.info(f"User {user_id} membership status: {member.status}")
        if member.status in [ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
            return True
        else:
            return False
    except Exception as e:
        logging.error(f"Error checking membership status for user {user_id}: {e}")
        return False

@app.on_message(filters.text)
async def handle_message(client, message: Message):
    if message.from_user is None:
        logging.error("Message does not contain user information.")
        return

    user_id = message.from_user.id
    user_mention = message.from_user.mention

    # Check if the message is the /broadcast command
    if message.text.startswith("/broadcast") and user_id in admin_user_ids:
        try:
            await handle_broadcast(client, message)
        except Exception as e:
            logging.error(f"Error in broadcast command: {e}")
            await message.reply_text("Failed to broadcast the message.")
        return

    # Check if the message is the /users command
    if message.text.startswith("/users") and user_id in admin_user_ids:
        try:
            users = await full_userbase()
            await message.reply_text(f"Currently, {len(users)} users are using this bot.")
        except Exception as e:
            logging.error(f"Error in /users command: {e}")
            await message.reply_text("An error occurred while fetching the user data.")
        return

    # Check if the user is a member of the required channel
    is_member = await is_user_member(client, user_id)
    if not is_member:
        join_button = InlineKeyboardButton("ᴊᴏɪɴ ❤️🚀", url="https://t.me/Javpostr")
        reply_markup = InlineKeyboardMarkup([[join_button]])
        await message.reply_text("ʏᴏᴜ ᴍᴜsᴛ ᴊᴏɪɴ ᴍʏ ᴄʜᴀɴɴᴇʟ ᴛᴏ ᴜsᴇ ᴍᴇ.", reply_markup=reply_markup)
        return

    # Validate the Terabox link (this will now be checked only if the message is not a command)
    valid_domains = [
        'terabox.com', 'nephobox.com', '4funbox.com', 'mirrobox.com', 
        'momerybox.com', 'teraboxapp.com', '1024tera.com', 
        'terabox.app', 'gibibox.com', 'goaibox.com', 'terasharelink.com', 'teraboxlink.com', 'terafileshare.com'
    ]
    terabox_link = message.text.strip()

    # Check if the message is a valid Terabox link (ignore if it's a command)
    if not any(domain in terabox_link for domain in valid_domains) and not message.text.startswith("/"):
        await message.reply_text("ᴘʟᴇᴀsᴇ sᴇɴᴅ ᴀ ᴠᴀʟɪᴅ ᴛᴇʀᴀʙᴏx ʟɪɴᴋ.")
        return

    # If the link is valid, proceed to process the link
    if not message.text.startswith("/"):  # Ensure we're not processing a command
        reply_msg = await message.reply_text("sᴇɴᴅɪɴɢ ʏᴏᴜ ᴛʜᴇ ᴍᴇᴅɪᴀ...🤤")
        try:
            file_path, thumbnail_path, video_title = await download_video(terabox_link, reply_msg, user_mention, user_id)
            await upload_video(client, file_path, thumbnail_path, video_title, reply_msg, dump_id, user_mention, user_id, message)
        except Exception as e:
            logging.error(f"Error handling message: {e}")
            await reply_msg.edit_text("Api has given a Broken Download Link. Dont Contact the Owner for this Issue.")



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
admin_ids = os.environ.get('ADMINS', '')
if len(admin_ids) == 0:
    logging.error("ADMINS variable is missing! Exiting now")
    exit(1)

admin_user_ids = [int(admin_id.strip()) for admin_id in admin_ids.split(',') if admin_id.strip().isdigit()]

@app.on_message(filters.command('broadcast'))
async def handle_broadcast(client: Client, message: Message):
    if message.from_user.id in admin_user_ids:
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

@app.on_message(filters.command('users'))
async def get_users(client: Client, message: Message):
    if message.from_user.id in admin_user_ids:
        # Corrected the text string with quotes
        msg = await client.send_message(chat_id=message.chat.id, text="Ruk jaa")  
        try:
            users = await full_userbase()
            await msg.edit(f"{len(users)} users are using this bot")
        except Exception as e:
            logging.error(f"Error in /users command: {e}")
            await msg.edit("An error occurred while fetching user data.")


if __name__ == "__main__":
    keep_alive()
    app.run()


