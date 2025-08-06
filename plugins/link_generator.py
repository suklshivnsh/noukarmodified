#(©)Codexbotz

from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
import asyncio
import re
from bot import Bot
from config import ADMINS
from helper_func import encode, get_message_id

@Bot.on_message(filters.private & filters.user(ADMINS) & filters.command('batch'))
async def batch(client: Client, message: Message):
    """Generate a batch link for multiple files"""
    # First message
    try:
        first_prompt = await message.reply_text("Forward the First Message from DB Channel (with Quotes)..\n\nor Send the DB Channel Post Link")
        
        first_message = await message.chat.ask(
            "Forward the First Message from DB Channel (with Quotes)..\n\nor Send the DB Channel Post Link",
            filters=(filters.forwarded | (filters.text & ~filters.forwarded)),
            timeout=60
        )
        
        f_msg_id = await get_message_id(client, first_message)
        if not f_msg_id:
            return await first_message.reply("❌ Error\n\nThis forwarded post is not from my DB Channel or this Link is not valid", quote=True)
        
        # Second message
        second_message = await message.chat.ask(
            "Forward the Last Message from DB Channel (with Quotes)..\nor Send the DB Channel Post link",
            filters=(filters.forwarded | (filters.text & ~filters.forwarded)),
            timeout=60
        )
        
        s_msg_id = await get_message_id(client, second_message)
        if not s_msg_id:
            return await second_message.reply("❌ Error\n\nThis forwarded post is not from my DB Channel or this Link is not valid", quote=True)
        
        # Generate batch link
        string = f"get-{f_msg_id * abs(client.db_channel.id)}-{s_msg_id * abs(client.db_channel.id)}"
        base64_string = await encode(string)
        link = f"https://t.me/{client.username}?start={base64_string}"
        reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("🔁 Share URL", url=f'https://telegram.me/share/url?url={link}')]])
        
        await second_message.reply_text(
            f"<b>Here is your link</b>\n\n{link}",
            quote=True,
            reply_markup=reply_markup
        )
        
    except asyncio.TimeoutError:
        await message.reply_text("⏱️ Timeout! Process cancelled.")
    except Exception as e:
        print(f"Error in batch command: {e}")
        await message.reply_text(f"❌ Error: {str(e)}\n\nPlease try again.")


@Bot.on_message(filters.private & filters.user(ADMINS) & filters.command('genlink'))
async def link_generator(client: Client, message: Message):
    """Generate a link for a single file"""
    try:
        channel_message = await message.chat.ask(
            "Forward Message from the DB Channel (with Quotes)..\nor Send the DB Channel Post link",
            filters=(filters.forwarded | (filters.text & ~filters.forwarded)),
            timeout=60
        )
        
        msg_id = await get_message_id(client, channel_message)
        if not msg_id:
            return await channel_message.reply("❌ Error\n\nThis Forwarded Post is not from my DB Channel or this Link is not taken from DB Channel", quote=True)
            
        base64_string = await encode(f"get-{msg_id * abs(client.db_channel.id)}")
        link = f"https://t.me/{client.username}?start={base64_string}"
        reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("🔁 Share URL", url=f'https://telegram.me/share/url?url={link}')]])
        
        await channel_message.reply_text(
            f"<b>Here is your link</b>\n\n{link}",
            quote=True,
            reply_markup=reply_markup
        )
        
    except asyncio.TimeoutError:
        await message.reply_text("⏱️ Timeout! Process cancelled.")
    except Exception as e:
        print(f"Error in genlink command: {e}")
        await message.reply_text(f"❌ Error: {str(e)}\n\nPlease try again.")
