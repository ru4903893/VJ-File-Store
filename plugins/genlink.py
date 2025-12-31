# Patched by ChatGPT – Pyrogram v2 compatible

import re
import os
import json
import base64
from pyrogram import Client, filters
from pyrogram.errors import ChannelInvalid, UsernameInvalid, UsernameNotModified

from config import ADMINS, LOG_CHANNEL, PUBLIC_FILE_STORE, WEBSITE_URL, WEBSITE_URL_MODE
from plugins.users_api import get_user, get_short_link


async def allowed(_, __, message):
    if PUBLIC_FILE_STORE:
        return True
    if message.from_user and message.from_user.id in ADMINS:
        return True
    return False


@Client.on_message((filters.document | filters.video | filters.audio) & filters.private)
async def incoming_gen_link(bot, message):
    if not await allowed(bot, None, message):
        return

    username = (await bot.get_me()).username
    post = await message.copy(LOG_CHANNEL)

    string = f"file_{post.id}"
    outstr = base64.urlsafe_b64encode(string.encode()).decode().strip("=")

    user = await get_user(message.from_user.id)

    if WEBSITE_URL_MODE:
        share_link = f"{WEBSITE_URL}?Tech_VJ={outstr}"
    else:
        share_link = f"https://t.me/{username}?start={outstr}"

    if user.get("base_site") and user.get("shortener_api"):
        share_link = await get_short_link(user, share_link)

    await message.reply(
        f"<b>⭕ HERE IS YOUR LINK\n\n🔗 {share_link}</b>"
    )


@Client.on_message(filters.command("link") & filters.private)
async def gen_link_s(bot, message):
    if not await allowed(bot, None, message):
        return

    replied = message.reply_to_message
    if not replied:
        return await message.reply("Reply to a file to generate link.")

    username = (await bot.get_me()).username
    post = await replied.copy(LOG_CHANNEL)

    string = f"file_{post.id}"
    outstr = base64.urlsafe_b64encode(string.encode()).decode().strip("=")

    user = await get_user(message.from_user.id)

    if WEBSITE_URL_MODE:
        share_link = f"{WEBSITE_URL}?Tech_VJ={outstr}"
    else:
        share_link = f"https://t.me/{username}?start={outstr}"

    if user.get("base_site") and user.get("shortener_api"):
        share_link = await get_short_link(user, share_link)

    await message.reply(
        f"<b>⭕ HERE IS YOUR LINK\n\n🔗 {share_link}</b>"
    )


@Client.on_message(filters.command("batch") & filters.private)
async def gen_link_batch(bot, message):
    if not await allowed(bot, None, message):
        return

    if not message.text or len(message.text.split()) != 3:
        return await message.reply(
            "Use:\n/batch first_link last_link"
        )

    _, first, last = message.text.split()
    regex = re.compile(r"(https://)?t\.me/(c/)?([\w\d_]+)/(\d+)")

    m1 = regex.match(first)
    m2 = regex.match(last)
    if not m1 or not m2:
        return await message.reply("Invalid links.")

    chat_id = m1.group(3)
    start_id = int(m1.group(4))
    end_id = int(m2.group(4))

    if chat_id.isdigit():
        chat_id = int("-100" + chat_id)

    try:
        await bot.get_chat(chat_id)
    except ChannelInvalid:
        return await message.reply("Make me admin in that channel.")
    except (UsernameInvalid, UsernameNotModified):
        return await message.reply("Invalid channel.")

    status = await message.reply("Generating batch link...")

    files = []
    async for msg in bot.iter_messages(
        chat_id=chat_id,
        min_id=start_id - 1,
        max_id=end_id
    ):
        if msg.document or msg.video or msg.audio:
            files.append({"c": chat_id, "m": msg.id})

    if not files:
        return await status.edit("No files found.")

    fname = f"batch_{message.from_user.id}.json"
    with open(fname, "w") as f:
        json.dump(files, f)

    doc = await bot.send_document(
        LOG_CHANNEL,
        fname,
        caption="Batch file"
    )
    os.remove(fname)

    username = (await bot.get_me()).username
    batch_code = base64.urlsafe_b64encode(
        f"BATCH-{doc.id}".encode()
    ).decode().strip("=")

    if WEBSITE_URL_MODE:
        link = f"{WEBSITE_URL}?Tech_VJ={batch_code}"
    else:
        link = f"https://t.me/{username}?start={batch_code}"

    await status.edit(
        f"<b>⭕ BATCH LINK READY\n\n📦 Files: {len(files)}\n🔗 {link}</b>"
    )
