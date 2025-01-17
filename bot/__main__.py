import os
import subprocess
import time
import importlib
import subprocess

from sys import executable

from telegram import ParseMode, BotCommand
from telegram.ext import CommandHandler, MessageHandler, Filters, run_async
from telegram.error import TimedOut, BadRequest

from bot.gDrive import GoogleDriveHelper
from bot.fs_utils import get_readable_file_size, is_gdtot_link, gdtot
from bot.config import BOT_TOKEN, OWNER_ID, GDRIVE_FOLDER_ID, GIT_PASS, AUTHORISED_USERS
from bot.decorators import is_authorised, is_owner
from bot.clone_status import CloneStatus
from bot.msg_utils import deleteMessage, sendMessage
from bot.modules import ALL_MODULES
from bot import LOGGER, dispatcher, updater, bot

for module in ALL_MODULES:
    imported_module = importlib.import_module("bot.modules." + module)
    importlib.reload(imported_module)

REPO_LINK = "https://github.com/jagrit007/Telegram-CloneBot"
# Soon to be used for direct updates from within the bot.

CLONE_REGEX = r"https://drive\.google\.com/(drive)?/?u?/?\d?/?(mobile)?/?(file)?(folders)?/?d?/(?P<id>[-\w]+)[?+]?/?(w+)?"

@run_async
def start(update, context):
    LOGGER.info('UID: {} - UN: {} - MSG: {}'.format(update.message.chat.id, update.message.chat.username, update.message.text))
    sendMessage("Hello! Please send me a Google Drive Shareable Link to Clone to your Drive!" \
        "\nSend /help for checking all available commands.",
    context.bot, update, 'Markdown')
    # ;-;

@run_async
def helper(update, context):
    LOGGER.info('UID: {} - UN: {} - MSG: {}'.format(update.message.chat.id, update.message.chat.username, update.message.text))
    sendMessage("Here are the available commands of the bot\n\n" \
        "*Usage:* `/clone <link> [DESTINATION_ID]`\n*Example:* \n1. `/clone https://drive.google.com/drive/u/1/folders/0AO-ISIXXXXXXXXXXXX`\n2. `/clone 0AO-ISIXXXXXXXXXXXX`" \
            "\n*DESTIONATION_ID* is optional. It can be either link or ID to where you wish to store a particular clone." \
            "\n\nYou can also *ignore folders* from clone process by doing the following:\n" \
                "`/clone <FOLDER_ID> [DESTINATION] [id1,id2,id3]`\n In this example: id1, id2 and id3 would get ignored from cloning\nDo not use <> or [] in actual message." \
                    "*Make sure to not put any space between commas (,).*\n" \
                        f"Source of this bot: [GitHub]({REPO_LINK})", context.bot, update, 'Markdown')

# TODO Cancel Clones with /cancel command.
@run_async
@is_authorised
def cloneNode(update, context):
    LOGGER.info('UID: {} - UN: {} - MSG: {}'.format(update.message.chat.id, update.message.chat.username, update.message.text))
    
    args = update.message.text.split(" ", maxsplit=1)
    reply_to = update.message.reply_to_message
    if len(args) > 1:
        link = args[1]
    elif reply_to is not None:
        link = reply_to.text
    else:
        link = None
    
    if is_gdtot_link(link):
        link = gdtot(link)
        if link is None:
            return sendMessage("<code>Something Wrong In Your GDTot Link !</code>", context.bot, update)
    
    if link is not None:
        DESTINATION_ID = GDRIVE_FOLDER_ID
        print(DESTINATION_ID) # Usage: /clone <FolderToClone> <Destination> <IDtoIgnoreFromClone>,<IDtoIgnoreFromClone>
        
        try:
            ignoreList = args[-1].split(',')
        except IndexError:
            ignoreList = []
        
        msg = sendMessage(f"<b>Cloning:</b> <code>{link}</code>", context.bot, update)
        status_class = CloneStatus()
        gd = GoogleDriveHelper(GFolder_ID=DESTINATION_ID)
        sendCloneStatus(update, context, status_class, msg, link)
        result = gd.clone(link, status_class, ignoreList=ignoreList)
        deleteMessage(context.bot, msg)
        status_class.set_status(True)
        if update.message.from_user.username:
            uname = f'@{update.message.from_user.username}'
        else:
            uname = f'<a href="tg://user?id={update.message.from_user.id}">{update.message.from_user.first_name}</a>'
        if uname is not None:
            cc = f'\n\n<b>Clone by: {uname} ID:</b> <code>{update.message.from_user.id}</code>'
        sendMessage(result + cc, context.bot, update)
    else:
        sendMessage("<b>Please Provide a Google Drive Shared Link to Clone.</b>", bot, update)


@run_async
def sendCloneStatus(update, context, status, msg, link):
    old_text = ''
    while not status.done():
        sleeper(3)
        try:
            if update.message.from_user.username:
                uname = f'@{update.message.from_user.username}'
            else:
                uname = f'<a href="tg://user?id={update.message.from_user.id}">{update.message.from_user.first_name}</a>'
            text=f'🔗 *Cloning:* [{status.MainFolderName}]({status.MainFolderLink})\n━━━━━━━━━━━━━━\n' \
                 f'🗃️ *Current File:* `{status.get_name()}`\n📚 *Total File:* `{int(len(status.get_name()))}`\n' \
                 f'⬆️ *Transferred*: `{status.get_size()}`\n📁 *Destination:* [{status.DestinationFolderName}]({status.DestinationFolderLink})\n\n' \
                 f'*👤 Clone by: {uname} ID:* `{update.message.from_user.id}`'
            if status.checkFileStatus():
                text += f"\n🕒 *Checking Existing Files:* `{str(status.checkFileStatus())}`"
            if not text == old_text:
                msg.edit_text(text=text, parse_mode="Markdown", timeout=200)
                old_text = text
        except Exception as e:
            LOGGER.error(e)
            if str(e) == "Message to edit not found":
                break
            sleeper(2)
            continue
    return

def sleeper(value, enabled=True):
    time.sleep(int(value))
    return

@run_async
@is_authorised
def countNode(update,context):
    LOGGER.info('UID: {} - UN: {} - MSG: {}'.format(update.message.chat.id, update.message.chat.username, update.message.text))
    args = update.message.text.split(" ", maxsplit=1)
    reply_to = update.message.reply_to_message
    if len(args) > 1:
        link = args[1]
    elif reply_to is not None:
        link = reply_to.text
    else:
        link = None
    
    if is_gdtot_link(link):
        link = gdtot(link)
        if link is None:
            return sendMessage("<code>Something Wrong In Your GDTot Link !</code>", context.bot, update)
    
    if link is not None:
        msg = sendMessage(f"Counting: <code>{link}</code>",context.bot,update)
        gd = GoogleDriveHelper()
        result = gd.count(link)
        deleteMessage(context.bot,msg)
        if update.message.from_user.username:
            uname = f'@{update.message.from_user.username}'
        else:
            uname = f'<a href="tg://user?id={update.message.from_user.id}">{update.message.from_user.first_name}</a>'
        if uname is not None:
            cc = f'\n\n<b>Count by: {uname} ID:</b> <code>{update.message.from_user.id}</code>'
        sendMessage(result + cc, context.bot, update)
    else:
        sendMessage("<b>Provide G-Drive Shareable Link to Count.</b>", context.bot, update)

@run_async
@is_owner
def sendLogs(update, context):
    LOGGER.info('UID: {} - UN: {} - MSG: {}'.format(update.message.chat.id, update.message.chat.username, update.message.text))
    with open('log.txt', 'rb') as f:
        bot.send_document(document=f, filename=f.name,
                        reply_to_message_id=update.message.message_id,
                        chat_id=update.message.chat_id)

@run_async
@is_owner
def shell(update, context):
    message = update.effective_message
    cmd = message.text.split(' ', 1)
    if len(cmd) == 1:
        message.reply_text('No command to execute was given.')
        return
    cmd = cmd[1]
    process = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    stdout, stderr = process.communicate()
    reply = ''
    stderr = stderr.decode()
    stdout = stdout.decode()
    if stdout:
        reply += f"*Stdout*\n`{stdout}`\n"
        LOGGER.info(f"Shell - {cmd} - {stdout}")
    if stderr:
        reply += f"*Stderr*\n`{stderr}`\n"
        LOGGER.error(f"Shell - {cmd} - {stderr}")
    if len(reply) > 3000:
        with open('shell_output.txt', 'w') as file:
            file.write(reply)
        with open('shell_output.txt', 'rb') as doc:
            context.bot.send_document(
                document=doc,
                filename=doc.name,
                reply_to_message_id=message.message_id,
                chat_id=message.chat_id)
    else:
        message.reply_text(reply, parse_mode=ParseMode.MARKDOWN)

@run_async
@is_owner
def gitpull(update, context):
    try:
        out = subprocess.check_output(["git", "pull"]).decode("UTF-8")
        if "Already up to date." in str(out):
            return sendMessage("<b>Its already up-to date !</b>", context.bot, update)
        sendMessage(f"<code>{out}</code>", context.bot, update) # Changelog
        restart_message = sendMessage(f"<b>Updated with default branch, restarting now.</b>", context.bot, update)
        with open(".restartmsg", "w") as f:
            f.truncate(0)
            f.write(f"{restart_message.chat.id}\n{restart_message.message_id}\n")
        os.execl(executable, executable, "-m", "bot")
    except Exception as e:
        sendMessage(f'<b>ERROR :</b> <code>{e}</code>', context.bot, update)


@run_async
@is_owner
def restart(update, context):
    restart_message = sendMessage("Restarting, Please wait!", context.bot, update)
    # Save restart message object in order to reply to it after restarting
    with open(".restartmsg", "w") as f:
        f.truncate(0)
        f.write(f"{restart_message.chat.id}\n{restart_message.message_id}\n")
    os.execl(executable, executable, "-m", "bot")

botcmds = [
    BotCommand('clone','Copy file/folder to Drive'),
    BotCommand('count','Count file/folder of Drive link')
]


def main():
    LOGGER.info("Bot Started!")
    if os.path.isfile(".restartmsg"):
        with open(".restartmsg") as f:
            chat_id, msg_id = map(int, f)
        bot.edit_message_text("𝐁𝐨𝐭 𝐑𝐞𝐬𝐭𝐚𝐫𝐭𝐞𝐝 𝐒𝐮𝐜𝐜𝐞𝐬𝐬𝐟𝐮𝐥𝐥𝐲!", chat_id, msg_id)
        os.remove(".restartmsg")
    bot.set_my_commands(botcmds)
    
    bot.sendMessage(chat_id=OWNER_ID, text=f"<b>Bot Started Successfully!</b>", parse_mode=ParseMode.HTML)
    try:
        for i in AUTHORISED_USERS:
            bot.sendMessage(chat_id=i, text=f"<b>Bot Started Successfully!</b>", parse_mode=ParseMode.HTML)
    except Exception:
        pass
    
    #regex_clone_handler = MessageHandler(filters=Filters.regex(CLONE_REGEX), callback=cloneNode)
    clone_handler = CommandHandler('clone', cloneNode)
    start_handler = CommandHandler('start', start)
    help_handler = CommandHandler('help', helper)
    log_handler = CommandHandler('logs', sendLogs)
    count_handler = CommandHandler('count', countNode)
    shell_handler = CommandHandler(['shell', 'sh', 'tr', 'term', 'terminal'], shell)
    GITPULL_HANDLER = CommandHandler('update', gitpull)
    restart_handler = CommandHandler('restart', restart)
    
    dispatcher.add_handler(restart_handler)
    dispatcher.add_handler(GITPULL_HANDLER)
    dispatcher.add_handler(shell_handler)
    dispatcher.add_handler(count_handler)
    dispatcher.add_handler(log_handler)
    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(clone_handler)
    #dispatcher.add_handler(regex_clone_handler)
    dispatcher.add_handler(help_handler)
    updater.start_polling()

main()
