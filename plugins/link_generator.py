#(©)Codexbotz

from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from bot import Bot
from config import ADMINS
from helper_func import encode, get_message_id

@Bot.on_message(filters.private & filters.user(ADMINS) & filters.command('batch'))
async def batch(client: Client, message: Message):
    # First message handling
    try:
        first_message = await client.ask(
            text = "Forward the First Message from DB Channel (with Quotes)..\n\nor Send the DB Channel Post Link", 
            chat_id = message.from_user.id, 
            filters=(filters.forwarded | (filters.text & ~filters.forwarded)), 
            timeout=60
        )
    except Exception as e:
        print(f"Error in batch command first message: {e}")
        await message.reply("An error occurred or the process timed out. Please try again.")
        return
        
    f_msg_id = await get_message_id(client, first_message)
    if not f_msg_id:
        await first_message.reply("❌ Error\n\nThis forwarded post is not from my DB Channel or this Link is not valid", quote=True)
        return
    
    # Second message handling - only proceed if first message is valid
    try:
        second_message = await client.ask(
            text = "Forward the Last Message from DB Channel (with Quotes)..\nor Send the DB Channel Post link", 
            chat_id = message.from_user.id, 
            filters=(filters.forwarded | (filters.text & ~filters.forwarded)), 
            timeout=60
        )
    except Exception as e:
        print(f"Error in batch command second message: {e}")
        await first_message.reply("An error occurred or the process timed out. Please try again.")
        return
        
    s_msg_id = await get_message_id(client, second_message)
    if not s_msg_id:
        await second_message.reply("❌ Error\n\nThis forwarded post is not from my DB Channel or this Link is not valid", quote=True)
        return
    
    # Create batch link only after both messages are validated
    string = f"get-{f_msg_id * abs(client.db_channel.id)}-{s_msg_id * abs(client.db_channel.id)}"
    base64_string = await encode(string)
    link = f"https://t.me/{client.username}?start={base64_string}"
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("🔁 Share URL", url=f'https://telegram.me/share/url?url={link}')]])
    await second_message.reply_text(f"<b>Here is your link</b>\n\n{link}", quote=True, reply_markup=reply_markup)


@Bot.on_message(filters.private & filters.user(ADMINS) & filters.command('genlink'))
async def link_generator(client: Client, message: Message):
    while True:
        try:
            channel_message = await client.ask(
                text = "Forward Message from the DB Channel (with Quotes)..\nor Send the DB Channel Post link", 
                chat_id = message.from_user.id, 
                filters=(filters.forwarded | (filters.text & ~filters.forwarded)), 
                timeout=60
            )
        except:
            return
            
        msg_id = await get_message_id(client, channel_message)
        if msg_id:
            break
        else:
            await channel_message.reply("❌ Error\n\nThis Forwarded Post is not from my DB Channel or this Link is not taken from DB Channel", quote = True)
            continue

    base64_string = await encode(f"get-{msg_id * abs(client.db_channel.id)}")
    link = f"https://t.me/{client.username}?start={base64_string}"
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("🔁 Share URL", url=f'https://telegram.me/share/url?url={link}')]])
    await channel_message.reply_text(f"<b>Here is your link</b>\n\n{link}", quote=True, reply_markup=reply_markup)
