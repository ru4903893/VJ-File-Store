# Patched Start Handler for VJ File Store
# Supports single file + batch links

import base64
import json
import os
from pyrogram import Client, filters
from config import LOG_CHANNEL


@Client.on_message(filters.command("start") & filters.private)
async def start_handler(bot, message):
    if len(message.command) == 1:
        return await message.reply(
            "👋 Welcome!\n\nSend me a file or use a generated link."
        )

    try:
        code = message.command[1] + "=="
        data = base64.urlsafe_b64decode(code).decode()
    except Exception:
        return await message.reply("Invalid or expired link.")

    # 🔹 Single file
    if data.startswith("file_"):
        msg_id = int(data.replace("file_", ""))
        msg = await bot.get_messages(LOG_CHANNEL, msg_id)
        await msg.copy(message.chat.id)

    # 🔹 Batch files
    elif data.startswith("BATCH-"):
        msg_id = int(data.replace("BATCH-", ""))
        batch_msg = await bot.get_messages(LOG_CHANNEL, msg_id)
        path = await batch_msg.download()

        with open(path) as f:
            files = json.load(f)

        for f in files:
            try:
                msg = await bot.get_messages(f["c"], f["m"])
                await msg.copy(message.chat.id)
            except:
                continue

        os.remove(path)
    else:
        await message.reply("Unknown link format.")
