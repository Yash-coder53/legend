import logging
import random
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatPermissions, ChatMember
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, CallbackContext
import telegram

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration
TOKEN = 'your_bot_token_here'  # Replace with your bot token
OWNER_ID = 123456789  # Replace with your Telegram user ID
OWNER_USERNAME = "@yourusername"

# Data storage
user_data = {}
sudo_users = []  # List of sudo user IDs
DATA_FILE = 'legendbot_data.json'

def load_data():
    """Load data from file."""
    global user_data, sudo_users
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r') as f:
                data = json.load(f)
                user_data = data.get('user_data', {})
                sudo_users = data.get('sudo_users', [])
                logger.info("Data loaded successfully")
    except Exception as e:
        logger.error(f"Error loading data: {e}")

def save_data():
    """Save data to file."""
    try:
        data = {
            'user_data': user_data,
            'sudo_users': sudo_users
        }
        with open(DATA_FILE, 'w') as f:
            json.dump(data, f, indent=2)
        logger.info("Data saved successfully")
    except Exception as e:
        logger.error(f"Error saving data: {e}")

# Load data on startup
load_data()

def is_owner(user_id: int) -> bool:
    """Check if the user is the bot owner."""
    return user_id == OWNER_ID

def is_sudo(user_id: int) -> bool:
    """Check if the user is a sudo user."""
    return user_id in sudo_users or user_id == OWNER_ID

def is_admin(update: Update, context: CallbackContext) -> bool:
    """Check if the user is an admin, sudo user, or bot owner."""
    user_id = update.effective_user.id
    
    if is_sudo(user_id):
        return True
    
    chat_id = update.effective_chat.id
    try:
        chat_member = context.bot.get_chat_member(chat_id, user_id)
        return chat_member.status in ['creator', 'administrator']
    except Exception as e:
        logger.error(f"Error checking admin status: {e}")
        return False

def bot_has_admin_rights(context: CallbackContext, chat_id: int) -> bool:
    """Check if the bot has admin rights in the chat."""
    try:
        bot_member = context.bot.get_chat_member(chat_id, context.bot.id)
        return bot_member.status in ['creator', 'administrator']
    except Exception as e:
        logger.error(f"Error checking bot admin status: {e}")
        return False

def start(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    welcome_message = (
        f"🔥 Welcome to LegendBot, {user.mention_markdown_v2()}\! 🔥\n\n"
        f"I'm an elite group management bot with professional-grade features\.\n\n"
        f"👑 Managed by: {OWNER_USERNAME}\n"
        f"⚡ Version: 2\.0\n"
        f"💡 Use /help to see available commands\n"
        f"🔐 Use /sudohelp for sudo commands\n\n"
        f"Let's build a legendary community together\! 🏆"
    )
    update.message.reply_markdown_v2(welcome_message)
    main_menu(update, context)

def main_menu(update: Update, context: CallbackContext) -> None:
    """Show the main menu."""
    keyboard = [
        [InlineKeyboardButton("⚔️ Admin Commands", callback_data='admin_commands')],
        [InlineKeyboardButton("👥 User Commands", callback_data='user_commands')],
        [InlineKeyboardButton("🎮 Fun Commands", callback_data='fun_commands')],
        [InlineKeyboardButton("⚙️ Settings", callback_data='settings')],
        [InlineKeyboardButton("🛡️ Sudo Menu", callback_data='sudo_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.message:
        update.message.reply_text('Please choose a category:', reply_markup=reply_markup)
    else:
        query = update.callback_query
        query.answer()
        query.edit_message_text('Please choose a category:', reply_markup=reply_markup)

def sudo_menu(update: Update, context: CallbackContext) -> None:
    """Show sudo commands menu."""
    if not is_sudo(update.effective_user.id):
        update.message.reply_text("🚫 You don't have permission to access sudo commands.")
        return
    
    keyboard = [
        [InlineKeyboardButton("👑 Add Sudo", callback_data='add_sudo'),
         InlineKeyboardButton("👑 Remove Sudo", callback_data='remove_sudo')],
        [InlineKeyboardButton("📋 List Sudo Users", callback_data='list_sudo')],
        [InlineKeyboardButton("💾 Backup Data", callback_data='backup_data')],
        [InlineKeyboardButton("🔄 Restore Data", callback_data='restore_data')],
        [InlineKeyboardButton("📊 Bot Stats", callback_data='bot_stats')],
        [InlineKeyboardButton("🌐 Global Broadcast", callback_data='global_broadcast')],
        [InlineKeyboardButton("🔧 Maintenance Mode", callback_data='maintenance_mode')],
        [InlineKeyboardButton("🔙 Back to Main Menu", callback_data='main_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query = update.callback_query
    query.answer()
    query.edit_message_text('Sudo Commands Menu:', reply_markup=reply_markup)

# SUDO COMMANDS

def addsudo(update: Update, context: CallbackContext) -> None:
    """Add a user to sudo."""
    if not is_owner(update.effective_user.id):
        update.message.reply_text("🚫 Only the bot owner can add sudo users.")
        return
    
    if not context.args:
        update.message.reply_text("Please provide a user ID. Usage: /addsudo <user_id>")
        return
    
    try:
        user_id = int(context.args[0])
        if user_id in sudo_users:
            update.message.reply_text(f"User {user_id} is already a sudo user.")
        else:
            sudo_users.append(user_id)
            save_data()
            update.message.reply_text(f"✅ User {user_id} has been added to sudo users.")
    except ValueError:
        update.message.reply_text("Please provide a valid user ID.")

def removesudo(update: Update, context: CallbackContext) -> None:
    """Remove a user from sudo."""
    if not is_owner(update.effective_user.id):
        update.message.reply_text("🚫 Only the bot owner can remove sudo users.")
        return
    
    if not context.args:
        update.message.reply_text("Please provide a user ID. Usage: /removesudo <user_id>")
        return
    
    try:
        user_id = int(context.args[0])
        if user_id == OWNER_ID:
            update.message.reply_text("Cannot remove the bot owner from sudo.")
        elif user_id in sudo_users:
            sudo_users.remove(user_id)
            save_data()
            update.message.reply_text(f"✅ User {user_id} has been removed from sudo users.")
        else:
            update.message.reply_text(f"User {user_id} is not a sudo user.")
    except ValueError:
        update.message.reply_text("Please provide a valid user ID.")

def listsudo(update: Update, context: CallbackContext) -> None:
    """List all sudo users."""
    if not is_sudo(update.effective_user.id):
        update.message.reply_text("🚫 You don't have permission to use this command.")
        return
    
    if not sudo_users:
        update.message.reply_text("No sudo users configured.")
        return
    
    sudo_list = "👑 Sudo Users:\n\n"
    sudo_list += f"• Owner: {OWNER_ID}\n"
    for user_id in sudo_users:
        sudo_list += f"• {user_id}\n"
    
    update.message.reply_text(sudo_list)

def backup(update: Update, context: CallbackContext) -> None:
    """Backup bot data."""
    if not is_sudo(update.effective_user.id):
        update.message.reply_text("🚫 You don't have permission to use this command.")
        return
    
    try:
        save_data()
        update.message.reply_text("✅ Bot data has been backed up successfully.")
    except Exception as e:
        update.message.reply_text(f"❌ Failed to backup data: {str(e)}")

def stats(update: Update, context: CallbackContext) -> None:
    """Show bot statistics."""
    if not is_sudo(update.effective_user.id):
        update.message.reply_text("🚫 You don't have permission to use this command.")
        return
    
    total_chats = len(user_data)
    total_filters = 0
    total_warnings = 0
    
    for chat_id in user_data:
        if "filters" in user_data[chat_id]:
            total_filters += len(user_data[chat_id]["filters"])
        
        for user_id in user_data[chat_id]:
            if isinstance(user_data[chat_id][user_id], dict):
                if "warnings" in user_data[chat_id][user_id]:
                    total_warnings += user_data[chat_id][user_id]["warnings"]
    
    stats_text = (
        f"📊 LegendBot Statistics:\n\n"
        f"• Total Groups: {total_chats}\n"
        f"• Total Filters: {total_filters}\n"
        f"• Total Warnings: {total_warnings}\n"
        f"• Sudo Users: {len(sudo_users)}\n"
        f"• Bot Owner: {OWNER_ID}\n"
        f"• Version: 2.0"
    )
    
    update.message.reply_text(stats_text)

def broadcast(update: Update, context: CallbackContext) -> None:
    """Broadcast message to all groups."""
    if not is_sudo(update.effective_user.id):
        update.message.reply_text("🚫 You don't have permission to use this command.")
        return
    
    if not context.args and not update.message.reply_to_message:
        update.message.reply_text("Please provide a message to broadcast or reply to a message.")
        return
    
    message_text = ' '.join(context.args) if context.args else None
    reply_message = update.message.reply_to_message
    
    if not message_text and not reply_message:
        update.message.reply_text("Please provide a message to broadcast.")
        return
    
    update.message.reply_text("Starting broadcast... This may take a while.")
    
    successful = 0
    failed = 0
    
    for chat_id in user_data:
        try:
            if reply_message:
                context.bot.forward_message(
                    chat_id=chat_id,
                    from_chat_id=update.effective_chat.id,
                    message_id=reply_message.message_id
                )
            else:
                context.bot.send_message(chat_id=chat_id, text=message_text)
            successful += 1
        except Exception as e:
            logger.error(f"Failed to send broadcast to {chat_id}: {e}")
            failed += 1
    
    update.message.reply_text(
        f"📢 Broadcast completed!\n"
        f"✅ Successful: {successful}\n"
        f"❌ Failed: {failed}"
    )

def maintenance(update: Update, context: CallbackContext) -> None:
    """Toggle maintenance mode."""
    if not is_owner(update.effective_user.id):
        update.message.reply_text("🚫 Only the bot owner can toggle maintenance mode.")
        return
    
    # This would require persistent storage for maintenance state
    # For now, just show a message
    update.message.reply_text("⚠️ Maintenance mode is a placeholder feature.")

def sudohelp(update: Update, context: CallbackContext) -> None:
    """Show sudo help."""
    if not is_sudo(update.effective_user.id):
        update.message.reply_text("🚫 You don't have permission to view sudo commands.")
        return
    
    help_text = (
        "👑 LegendBot Sudo Commands:\n\n"
        "/addsudo <user_id> - Add user to sudo\n"
        "/removesudo <user_id> - Remove user from sudo\n"
        "/listsudo - List all sudo users\n"
        "/backup - Backup bot data\n"
        "/stats - Show bot statistics\n"
        "/broadcast <message> - Broadcast to all groups\n"
        "/maintenance - Toggle maintenance mode\n"
        "/sudohelp - Show this help message\n\n"
        f"Bot Owner: {OWNER_USERNAME}"
    )
    
    update.message.reply_text(help_text)

# ADMIN COMMANDS MENU
def admin_commands(update: Update, context: CallbackContext) -> None:
    """Show admin commands."""
    keyboard = [
        [InlineKeyboardButton("🚫 Ban", callback_data='ban'),
         InlineKeyboardButton("✅ Unban", callback_data='unban')],
        [InlineKeyboardButton("👢 Kick", callback_data='kick'),
         InlineKeyboardButton("🔇 Mute", callback_data='mute')],
        [InlineKeyboardButton("🔊 Unmute", callback_data='unmute'),
         InlineKeyboardButton("⚠️ Warn", callback_data='warn')],
        [InlineKeyboardButton("🔄 Unwarn", callback_data='unwarn'),
         InlineKeyboardButton("🎖️ Promote", callback_data='promote')],
        [InlineKeyboardButton("⬇️ Demote", callback_data='demote'),
         InlineKeyboardButton("🧹 Purge", callback_data='purge')],
        [InlineKeyboardButton("🔍 Filter", callback_data='filter'),
         InlineKeyboardButton("🛑 Stop Filter", callback_data='stop')],
        [InlineKeyboardButton("📋 Filter List", callback_data='filterlist'),
         InlineKeyboardButton("🌐🚫 Global Ban", callback_data='gban')],
        [InlineKeyboardButton("🔒 Lock All", callback_data='lockall'),
         InlineKeyboardButton("🔓 Unlock All", callback_data='unlockall')],
        [InlineKeyboardButton("🗑️⚠️ Delete & Warn", callback_data='dwarn'),
         InlineKeyboardButton("🗑️🔇 Delete & Mute", callback_data='dmute')],
        [InlineKeyboardButton("🔙 Back to Main Menu", callback_data='main_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query = update.callback_query
    query.answer()
    query.edit_message_text('Admin Commands:', reply_markup=reply_markup)

# USER COMMANDS MENU
def user_commands(update: Update, context: CallbackContext) -> None:
    """Show user commands."""
    keyboard = [
        [InlineKeyboardButton("ℹ️ Info", callback_data='info'),
         InlineKeyboardButton("🆔 IDs", callback_data='id')],
        [InlineKeyboardButton("📜 Rules", callback_data='rules'),
         InlineKeyboardButton("❓ Help", callback_data='help')],
        [InlineKeyboardButton("🔙 Back to Main Menu", callback_data='main_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query = update.callback_query
    query.answer()
    query.edit_message_text('User Commands:', reply_markup=reply_markup)

# FUN COMMANDS MENU
def fun_commands(update: Update, context: CallbackContext) -> None:
    """Show fun commands."""
    keyboard = [
        [InlineKeyboardButton("🎲 Roll Dice", callback_data='roll_dice'),
         InlineKeyboardButton("🪙 Flip Coin", callback_data='flip_coin')],
        [InlineKeyboardButton("🔢 Random Number", callback_data='random_number'),
         InlineKeyboardButton("💬 Quote", callback_data='quote')],
        [InlineKeyboardButton("🎯 Trivia", callback_data='trivia'),
         InlineKeyboardButton("🎨 Random Color", callback_data='random_color')],
        [InlineKeyboardButton("🔙 Back to Main Menu", callback_data='main_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query = update.callback_query
    query.answer()
    query.edit_message_text('Fun Commands:', reply_markup=reply_markup)

# SETTINGS MENU
def settings(update: Update, context: CallbackContext) -> None:
    """Show settings."""
    keyboard = [
        [InlineKeyboardButton("👋 Welcome Message", callback_data='set_welcome'),
         InlineKeyboardButton("👋 Goodbye Message", callback_data='set_goodbye')],
        [InlineKeyboardButton("📜 Chat Rules", callback_data='set_rules'),
         InlineKeyboardButton("🛡️ Anti-Spam", callback_data='set_antispam')],
        [InlineKeyboardButton("🌊 Anti-Flood", callback_data='set_antiflood'),
         InlineKeyboardButton("🚫 Blacklist", callback_data='set_blacklist')],
        [InlineKeyboardButton("🔙 Back to Main Menu", callback_data='main_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query = update.callback_query
    query.answer()
    query.edit_message_text('Settings:', reply_markup=reply_markup)

# ADMIN COMMAND IMPLEMENTATIONS
def ban(update: Update, context: CallbackContext) -> None:
    """Ban a user."""
    if not is_admin(update, context):
        update.message.reply_text("🚫 You don't have permission to use this command.")
        return
    
    chat_id = update.effective_chat.id
    
    if not bot_has_admin_rights(context, chat_id):
        update.message.reply_text("❌ I don't have admin rights in this chat. I can't ban users.")
        return
    
    if update.message.reply_to_message:
        user_id = update.message.reply_to_message.from_user.id
        reason = ' '.join(context.args) if context.args else "No reason provided"
        
        try:
            context.bot.ban_chat_member(chat_id, user_id)
            update.message.reply_text(
                f"🚫 User {user_id} has been banned.\n"
                f"Reason: {reason}"
            )
        except telegram.error.TelegramError as e:
            update.message.reply_text(f"❌ Failed to ban user: {str(e)}")
    else:
        update.message.reply_text("Please reply to a message to ban the user.")

def unban(update: Update, context: CallbackContext) -> None:
    """Unban a user."""
    if not is_admin(update, context):
        update.message.reply_text("🚫 You don't have permission to use this command.")
        return
    
    chat_id = update.effective_chat.id
    
    if not bot_has_admin_rights(context, chat_id):
        update.message.reply_text("❌ I don't have admin rights in this chat. I can't unban users.")
        return
    
    if context.args:
        try:
            user_id = int(context.args[0])
            context.bot.unban_chat_member(chat_id, user_id, only_if_banned=True)
            update.message.reply_text(f"✅ User {user_id} has been unbanned.")
        except ValueError:
            update.message.reply_text("Please provide a valid user ID.")
        except telegram.error.TelegramError as e:
            update.message.reply_text(f"❌ Failed to unban user: {str(e)}")
    else:
        update.message.reply_text("Please provide a user ID to unban.")

def kick(update: Update, context: CallbackContext) -> None:
    """Kick a user."""
    if not is_admin(update, context):
        update.message.reply_text("🚫 You don't have permission to use this command.")
        return
    
    chat_id = update.effective_chat.id
    
    if not bot_has_admin_rights(context, chat_id):
        update.message.reply_text("❌ I don't have admin rights in this chat. I can't kick users.")
        return
    
    if update.message.reply_to_message:
        user_id = update.message.reply_to_message.from_user.id
        try:
            context.bot.kick_chat_member(chat_id, user_id)
            context.bot.unban_chat_member(chat_id, user_id)
            update.message.reply_text(f"👢 User {user_id} has been kicked.")
        except telegram.error.TelegramError as e:
            update.message.reply_text(f"❌ Failed to kick user: {str(e)}")
    else:
        update.message.reply_text("Please reply to a message to kick the user.")

def mute(update: Update, context: CallbackContext) -> None:
    """Mute a user."""
    if not is_admin(update, context):
        update.message.reply_text("🚫 You don't have permission to use this command.")
        return
    
    chat_id = update.effective_chat.id
    
    if not bot_has_admin_rights(context, chat_id):
        update.message.reply_text("❌ I don't have admin rights in this chat. I can't mute users.")
        return
    
    if update.message.reply_to_message:
        user_id = update.message.reply_to_message.from_user.id
        
        # Parse duration
        duration = None
        if context.args:
            try:
                duration = int(context.args[0])
            except ValueError:
                pass
        
        until_date = None
        if duration:
            until_date = datetime.now() + timedelta(minutes=duration)
        
        try:
            context.bot.restrict_chat_member(
                chat_id=chat_id,
                user_id=user_id,
                permissions=ChatPermissions(
                    can_send_messages=False,
                    can_send_media_messages=False,
                    can_send_other_messages=False,
                    can_add_web_page_previews=False
                ),
                until_date=until_date
            )
            
            if duration:
                update.message.reply_text(f"🔇 User {user_id} has been muted for {duration} minutes.")
            else:
                update.message.reply_text(f"🔇 User {user_id} has been muted.")
        except telegram.error.TelegramError as e:
            update.message.reply_text(f"❌ Failed to mute user: {str(e)}")
    else:
        update.message.reply_text("Please reply to a message to mute the user.")

def unmute(update: Update, context: CallbackContext) -> None:
    """Unmute a user."""
    if not is_admin(update, context):
        update.message.reply_text("🚫 You don't have permission to use this command.")
        return
    
    chat_id = update.effective_chat.id
    
    if not bot_has_admin_rights(context, chat_id):
        update.message.reply_text("❌ I don't have admin rights in this chat. I can't unmute users.")
        return
    
    if update.message.reply_to_message:
        user_id = update.message.reply_to_message.from_user.id
        try:
            context.bot.restrict_chat_member(
                chat_id=chat_id,
                user_id=user_id,
                permissions=ChatPermissions(
                    can_send_messages=True,
                    can_send_media_messages=True,
                    can_send_other_messages=True,
                    can_add_web_page_previews=True
                )
            )
            update.message.reply_text(f"🔊 User {user_id} has been unmuted.")
        except telegram.error.TelegramError as e:
            update.message.reply_text(f"❌ Failed to unmute user: {str(e)}")
    else:
        update.message.reply_text("Please reply to a message to unmute the user.")

def warn(update: Update, context: CallbackContext) -> None:
    """Warn a user."""
    if not is_admin(update, context):
        update.message.reply_text("🚫 You don't have permission to use this command.")
        return
    
    if update.message.reply_to_message:
        warned_user = update.message.reply_to_message.from_user
        user_id = warned_user.id
        chat_id = update.effective_chat.id
        
        if str(chat_id) not in user_data:
            user_data[str(chat_id)] = {}
        if str(user_id) not in user_data[str(chat_id)]:
            user_data[str(chat_id)][str(user_id)] = {"warnings": 0}
        
        user_data[str(chat_id)][str(user_id)]["warnings"] += 1
        warn_count = user_data[str(chat_id)][str(user_id)]["warnings"]
        save_data()
        
        update.message.reply_text(
            f"⚠️ User {warned_user.mention_markdown_v2()} has been warned\.\n"
            f"Warning count: {warn_count}/3",
            parse_mode='MarkdownV2'
        )
        
        if warn_count >= 3:
            try:
                if bot_has_admin_rights(context, chat_id):
                    context.bot.kick_chat_member(chat_id, user_id)
                    update.message.reply_text(
                        f"🚫 User {warned_user.mention_markdown_v2()} has been banned due to excessive warnings\.",
                        parse_mode='MarkdownV2'
                    )
            except telegram.error.TelegramError as e:
                update.message.reply_text(f"❌ Failed to ban user: {str(e)}")
    else:
        update.message.reply_text("Please reply to a message to warn the user.")

def unwarn(update: Update, context: CallbackContext) -> None:
    """Remove a warning from a user."""
    if not is_admin(update, context):
        update.message.reply_text("🚫 You don't have permission to use this command.")
        return
    
    if update.message.reply_to_message:
        user = update.message.reply_to_message.from_user
        user_id = user.id
        chat_id = update.effective_chat.id
        
        chat_id_str = str(chat_id)
        user_id_str = str(user_id)
        
        if chat_id_str in user_data and user_id_str in user_data[chat_id_str]:
            if user_data[chat_id_str][user_id_str]["warnings"] > 0:
                user_data[chat_id_str][user_id_str]["warnings"] -= 1
                warn_count = user_data[chat_id_str][user_id_str]["warnings"]
                save_data()
                update.message.reply_text(
                    f"🔄 One warning has been removed from {user.mention_markdown_v2()}\.\n"
                    f"Current warning count: {warn_count}",
                    parse_mode='MarkdownV2'
                )
            else:
                update.message.reply_text(
                    f"{user.mention_markdown_v2()} has no warnings to remove\.",
                    parse_mode='MarkdownV2'
                )
        else:
            update.message.reply_text(
                f"{user.mention_markdown_v2()} has no warnings\.",
                parse_mode='MarkdownV2'
            )
    else:
        update.message.reply_text("Please reply to a message to remove a warning from the user.")

def promote(update: Update, context: CallbackContext) -> None:
    """Promote a user to admin."""
    if not is_admin(update, context):
        update.message.reply_text("🚫 You don't have permission to use this command.")
        return
    
    chat_id = update.effective_chat.id
    
    if not bot_has_admin_rights(context, chat_id):
        update.message.reply_text("❌ I don't have admin rights in this chat. I can't promote users.")
        return
    
    if update.message.reply_to_message:
        user_id = update.message.reply_to_message.from_user.id
        custom_title = ' '.join(context.args) if context.args else "Admin"
        
        try:
            context.bot.promote_chat_member(
                chat_id=chat_id,
                user_id=user_id,
                can_change_info=True,
                can_delete_messages=True,
                can_invite_users=True,
                can_restrict_members=True,
                can_pin_messages=True,
                can_promote_members=False
            )
            
            try:
                context.bot.set_chat_administrator_custom_title(chat_id, user_id, custom_title)
            except:
                pass  # Some chats don't allow custom titles
            
            update.message.reply_text(f"🎖️ User {user_id} has been promoted to admin.")
        except telegram.error.TelegramError as e:
            update.message.reply_text(f"❌ Failed to promote user: {str(e)}")
    else:
        update.message.reply_text("Please reply to a message to promote the user.")

def demote(update: Update, context: CallbackContext) -> None:
    """Demote an admin to regular user."""
    if not is_admin(update, context):
        update.message.reply_text("🚫 You don't have permission to use this command.")
        return
    
    chat_id = update.effective_chat.id
    
    if not bot_has_admin_rights(context, chat_id):
        update.message.reply_text("❌ I don't have admin rights in this chat. I can't demote users.")
        return
    
    if update.message.reply_to_message:
        user_id = update.message.reply_to_message.from_user.id
        try:
            context.bot.promote_chat_member(
                chat_id=chat_id,
                user_id=user_id,
                can_change_info=False,
                can_delete_messages=False,
                can_invite_users=False,
                can_restrict_members=False,
                can_pin_messages=False,
                can_promote_members=False
            )
            update.message.reply_text(f"⬇️ User {user_id} has been demoted to regular user.")
        except telegram.error.TelegramError as e:
            update.message.reply_text(f"❌ Failed to demote user: {str(e)}")
    else:
        update.message.reply_text("Please reply to a message to demote the user.")

def purge(update: Update, context: CallbackContext) -> None:
    """Purge messages."""
    if not is_admin(update, context):
        update.message.reply_text("🚫 You don't have permission to use this command.")
        return
    
    chat_id = update.effective_chat.id
    
    if not context.args:
        update.message.reply_text("Please specify the number of messages to purge.")
        return
    
    try:
        num_messages = int(context.args[0])
        if num_messages < 1 or num_messages > 100:
            update.message.reply_text("Please specify a number between 1 and 100.")
            return
    except ValueError:
        update.message.reply_text("Please provide a valid number.")
        return
    
    if update.message.reply_to_message:
        start_id = update.message.reply_to_message.message_id
        deleted = 0
        
        for i in range(start_id, start_id - num_messages, -1):
            try:
                context.bot.delete_message(chat_id, i)
                deleted += 1
            except:
                pass
        
        update.message.reply_text(f"🧹 Purged {deleted} messages.")
    else:
        update.message.reply_text("Please reply to the starting message.")

def filter_message(update: Update, context: CallbackContext) -> None:
    """Add a filter."""
    if not is_admin(update, context):
        update.message.reply_text("🚫 You don't have permission to use this command.")
        return
    
    chat_id = update.effective_chat.id
    
    if update.message.reply_to_message:
        if not context.args:
            update.message.reply_text("Please provide a keyword for the filter.")
            return
        
        keyword = context.args[0].lower()
        message = update.message.reply_to_message
        
        if str(chat_id) not in user_data:
            user_data[str(chat_id)] = {}
        if "filters" not in user_data[str(chat_id)]:
            user_data[str(chat_id)]["filters"] = {}
        
        filter_data = {
            "text": message.text if message.text else None,
            "photo": message.photo[-1].file_id if message.photo else None,
            "sticker": message.sticker.file_id if message.sticker else None,
        }
        
        user_data[str(chat_id)]["filters"][keyword] = filter_data
        save_data()
        
        update.message.reply_text(f"✅ Filter '{keyword}' has been added.")
    else:
        update.message.reply_text("Please reply to a message to create a filter.")

def stop_filter(update: Update, context: CallbackContext) -> None:
    """Remove a filter."""
    if not is_admin(update, context):
        update.message.reply_text("🚫 You don't have permission to use this command.")
        return
    
    chat_id = update.effective_chat.id
    
    if not context.args:
        update.message.reply_text("Please specify the filter keyword to remove.")
        return
    
    keyword = context.args[0].lower()
    
    if str(chat_id) in user_data and "filters" in user_data[str(chat_id)]:
        if keyword in user_data[str(chat_id)]["filters"]:
            del user_data[str(chat_id)]["filters"][keyword]
            save_data()
            update.message.reply_text(f"✅ Filter '{keyword}' has been removed.")
        else:
            update.message.reply_text(f"Filter '{keyword}' not found.")
    else:
        update.message.reply_text("No filters found in this chat.")

def filter_list(update: Update, context: CallbackContext) -> None:
    """List all filters."""
    chat_id = update.effective_chat.id
    
    if str(chat_id) in user_data and "filters" in user_data[str(chat_id)]:
        filters = user_data[str(chat_id)]["filters"]
        if filters:
            filter_text = "📋 Active Filters:\n\n"
            for keyword in filters:
                filter_text += f"• {keyword}\n"
            update.message.reply_text(filter_text)
        else:
            update.message.reply_text("No active filters in this chat.")
    else:
        update.message.reply_text("No active filters in this chat.")

def gban(update: Update, context: CallbackContext) -> None:
    """Global ban a user."""
    if not is_sudo(update.effective_user.id):
        update.message.reply_text("🚫 You don't have permission to use this command.")
        return
    
    if update.message.reply_to_message:
        user_id = update.message.reply_to_message.from_user.id
        
        # Store globally banned users
        if "gban" not in user_data:
            user_data["gban"] = []
        
        if user_id not in user_data["gban"]:
            user_data["gban"].append(user_id)
            save_data()
            
            update.message.reply_text(f"🌐 User {user_id} has been globally banned.")
        else:
            update.message.reply_text(f"User {user_id} is already globally banned.")
    else:
        update.message.reply_text("Please reply to a message to globally ban the user.")

def lockall(update: Update, context: CallbackContext) -> None:
    """Lock all permissions."""
    if not is_admin(update, context):
        update.message.reply_text("🚫 You don't have permission to use this command.")
        return
    
    chat_id = update.effective_chat.id
    
    if not bot_has_admin_rights(context, chat_id):
        update.message.reply_text("❌ I don't have admin rights in this chat. I can't lock permissions.")
        return
    
    try:
        context.bot.set_chat_permissions(
            chat_id=chat_id,
            permissions=ChatPermissions(
                can_send_messages=False,
                can_send_media_messages=False,
                can_send_polls=False,
                can_send_other_messages=False,
                can_add_web_page_previews=False,
                can_change_info=False,
                can_invite_users=False,
                can_pin_messages=False
            )
        )
        update.message.reply_text("🔒 All permissions have been locked.")
    except telegram.error.TelegramError as e:
        update.message.reply_text(f"❌ Failed to lock permissions: {str(e)}")

def unlockall(update: Update, context: CallbackContext) -> None:
    """Unlock all permissions."""
    if not is_admin(update, context):
        update.message.reply_text("🚫 You don't have permission to use this command.")
        return
    
    chat_id = update.effective_chat.id
    
    if not bot_has_admin_rights(context, chat_id):
        update.message.reply_text("❌ I don't have admin rights in this chat. I can't unlock permissions.")
        return
    
    try:
        context.bot.set_chat_permissions(
            chat_id=chat_id,
            permissions=ChatPermissions(
                can_send_messages=True,
                can_send_media_messages=True,
                can_send_polls=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True,
                can_change_info=True,
                can_invite_users=True,
                can_pin_messages=True
            )
        )
        update.message.reply_text("🔓 All permissions have been unlocked.")
    except telegram.error.TelegramError as e:
        update.message.reply_text(f"❌ Failed to unlock permissions: {str(e)}")

def delete_and_warn(update: Update, context: CallbackContext) -> None:
    """Delete message and warn user."""
    if not is_admin(update, context):
        update.message.reply_text("🚫 You don't have permission to use this command.")
        return
    
    chat_id = update.effective_chat.id
    
    if not bot_has_admin_rights(context, chat_id):
        update.message.reply_text("❌ I don't have admin rights in this chat.")
        return
    
    if update.message.reply_to_message:
        message = update.message.reply_to_message
        user = message.from_user
        
        try:
            # Delete message
            context.bot.delete_message(chat_id, message.message_id)
            
            # Warn user
            if str(chat_id) not in user_data:
                user_data[str(chat_id)] = {}
            if str(user.id) not in user_data[str(chat_id)]:
                user_data[str(chat_id)][str(user.id)] = {"warnings": 0}
            
            user_data[str(chat_id)][str(user.id)]["warnings"] += 1
            warn_count = user_data[str(chat_id)][str(user.id)]["warnings"]
            save_data()
            
            update.message.reply_text(
                f"🗑️⚠️ Message deleted and user warned\.\n"
                f"Warning count: {warn_count}/3",
                parse_mode='MarkdownV2'
            )
        except telegram.error.TelegramError as e:
            update.message.reply_text(f"❌ Failed to delete and warn: {str(e)}")
    else:
        update.message.reply_text("Please reply to a message.")

def delete_and_mute(update: Update, context: CallbackContext) -> None:
    """Delete message and mute user."""
    if not is_admin(update, context):
        update.message.reply_text("🚫 You don't have permission to use this command.")
        return
    
    chat_id = update.effective_chat.id
    
    if not bot_has_admin_rights(context, chat_id):
        update.message.reply_text("❌ I don't have admin rights in this chat.")
        return
    
    if update.message.reply_to_message:
        message = update.message.reply_to_message
        user = message.from_user
        
        try:
            # Delete message
            context.bot.delete_message(chat_id, message.message_id)
            
            # Mute user
            context.bot.restrict_chat_member(
                chat_id=chat_id,
                user_id=user.id,
                permissions=ChatPermissions(
                    can_send_messages=False,
                    can_send_media_messages=False,
                    can_send_other_messages=False,
                    can_add_web_page_previews=False
                ),
                until_date=datetime.now() + timedelta(hours=1)
            )
            
            update.message.reply_text(f"🗑️🔇 Message deleted and user muted for 1 hour.")
        except telegram.error.TelegramError as e:
            update.message.reply_text(f"❌ Failed to delete and mute: {str(e)}")
    else:
        update.message.reply_text("Please reply to a message.")

# USER COMMANDS
def info(update: Update, context: CallbackContext) -> None:
    """Get user info."""
    user = update.effective_user
    chat = update.effective_chat
    
    info_text = f"👤 User Info:\n"
    info_text += f"• Name: {user.full_name}\n"
    info_text += f"• Username: @{user.username if user.username else 'N/A'}\n"
    info_text += f"• ID: {user.id}\n\n"
    
    if chat.type != 'private':
        info_text += f"💬 Chat Info:\n"
        info_text += f"• Title: {chat.title}\n"
        info_text += f"• Type: {chat.type}\n"
        info_text += f"• ID: {chat.id}\n"
    
    # Check warnings
    chat_id_str = str(chat.id)
    user_id_str = str(user.id)
    
    if chat_id_str in user_data and user_id_str in user_data[chat_id_str]:
        warnings = user_data[chat_id_str][user_id_str].get("warnings", 0)
        info_text += f"\n⚠️ Warnings: {warnings}/3"
    
    update.message.reply_text(info_text)

def id_command(update: Update, context: CallbackContext) -> None:
    """Get user and chat IDs."""
    user = update.effective_user
    chat = update.effective_chat
    
    id_text = f"👤 Your ID: `{user.id}`\n"
    
    if chat.type != 'private':
        id_text += f"💬 Chat ID: `{chat.id}`"
    
    update.message.reply_text(id_text, parse_mode='Markdown')

def rules(update: Update, context: CallbackContext) -> None:
    """Show chat rules."""
    chat_id = update.effective_chat.id
    
    if str(chat_id) in user_data and "rules" in user_data[str(chat_id)]:
        rules_text = user_data[str(chat_id)]["rules"]
        update.message.reply_text(f"📜 Chat Rules:\n\n{rules_text}")
    else:
        update.message.reply_text("No rules have been set for this chat.")

def help_command(update: Update, context: CallbackContext) -> None:
    """Show help."""
    help_text = (
        "🔥 LegendBot Help\n\n"
        "⚔️ Admin Commands:\n"
        "/ban - Ban a user\n"
        "/unban - Unban a user\n"
        "/kick - Kick a user\n"
        "/mute - Mute a user\n"
        "/unmute - Unmute a user\n"
        "/warn - Warn a user\n"
        "/unwarn - Remove warning\n"
        "/purge - Delete messages\n"
        "/filter - Add auto-reply\n"
        "/lockall - Lock chat\n\n"
        
        "👥 User Commands:\n"
        "/info - User info\n"
        "/id - Get IDs\n"
        "/rules - Chat rules\n"
        "/help - This message\n\n"
        
        "🎮 Fun Commands:\n"
        "/roll - Roll dice\n"
        "/flip - Flip coin\n"
        "/random - Random number\n\n"
        
        f"👑 Owner: {OWNER_USERNAME}"
    )
    
    update.message.reply_text(help_text)

# FUN COMMANDS
def roll_dice(update: Update, context: CallbackContext) -> None:
    """Roll a dice."""
    result = random.randint(1, 6)
    update.message.reply_text(f"🎲 You rolled: {result}")

def flip_coin(update: Update, context: CallbackContext) -> None:
    """Flip a coin."""
    result = random.choice(["Heads", "Tails"])
    update.message.reply_text(f"🪙 {result}!")

def random_number(update: Update, context: CallbackContext) -> None:
    """Generate random number."""
    if context.args:
        try:
            max_num = int(context.args[0])
            if max_num < 1:
                update.message.reply_text("Please provide a positive number.")
                return
            result = random.randint(1, max_num)
        except ValueError:
            update.message.reply_text("Please provide a valid number.")
            return
    else:
        result = random.randint(1, 100)
    
    update.message.reply_text(f"🔢 Random number: {result}")

def quote(update: Update, context: CallbackContext) -> None:
    """Get a random quote."""
    quotes = [
        "The only way to do great work is to love what you do. - Steve Jobs",
        "Innovation distinguishes between a leader and a follower. - Steve Jobs",
        "Your time is limited, so don't waste it living someone else's life. - Steve Jobs",
        "Stay hungry, stay foolish. - Steve Jobs",
        "The future belongs to those who believe in the beauty of their dreams. - Eleanor Roosevelt",
        "It does not matter how slowly you go as long as you do not stop. - Confucius",
        "Everything you've ever wanted is on the other side of fear. - George Addair",
        "Believe you can and you're halfway there. - Theodore Roosevelt"
    ]
    
    chosen = random.choice(quotes)
    update.message.reply_text(f"💬 {chosen}")

def trivia(update: Update, context: CallbackContext) -> None:
    """Ask a trivia question."""
    questions = [
        {"q": "What is the capital of France?", "a": "Paris"},
        {"q": "How many continents are there?", "a": "7"},
        {"q": "What is the largest planet in our solar system?", "a": "Jupiter"},
        {"q": "Who wrote 'Romeo and Juliet'?", "a": "William Shakespeare"},
        {"q": "What is the chemical symbol for gold?", "a": "Au"}
    ]
    
    question = random.choice(questions)
    update.message.reply_text(f"🎯 Trivia Question:\n\n{question['q']}\n\nAnswer will be revealed in 30 seconds!")
    
    # Schedule answer
    context.job_queue.run_once(
        lambda ctx: update.message.reply_text(f"Answer: {question['a']}"),
        30,
        context=update.message.chat_id
    )

def random_color(update: Update, context: CallbackContext) -> None:
    """Generate random color."""
    colors = {
        "🔴 Red": "#FF0000",
        "🟢 Green": "#00FF00",
        "🔵 Blue": "#0000FF",
        "🟡 Yellow": "#FFFF00",
        "🟣 Purple": "#800080",
        "🟠 Orange": "#FFA500",
        "⚫ Black": "#000000",
        "⚪ White": "#FFFFFF"
    }
    
    color_name, hex_code = random.choice(list(colors.items()))
    update.message.reply_text(f"🎨 Random Color: {color_name}\nHex: {hex_code}")

# SETTINGS COMMANDS
def set_welcome(update: Update, context: CallbackContext) -> None:
    """Set welcome message."""
    if not is_admin(update, context):
        update.message.reply_text("🚫 You don't have permission to use this command.")
        return
    
    if not context.args:
        update.message.reply_text("Please provide a welcome message.")
        return
    
    chat_id = update.effective_chat.id
    welcome_msg = ' '.join(context.args)
    
    if str(chat_id) not in user_data:
        user_data[str(chat_id)] = {}
    
    user_data[str(chat_id)]["welcome"] = welcome_msg
    save_data()
    
    update.message.reply_text("✅ Welcome message set.")

def set_goodbye(update: Update, context: CallbackContext) -> None:
    """Set goodbye message."""
    if not is_admin(update, context):
        update.message.reply_text("🚫 You don't have permission to use this command.")
        return
    
    if not context.args:
        update.message.reply_text("Please provide a goodbye message.")
        return
    
    chat_id = update.effective_chat.id
    goodbye_msg = ' '.join(context.args)
    
    if str(chat_id) not in user_data:
        user_data[str(chat_id)] = {}
    
    user_data[str(chat_id)]["goodbye"] = goodbye_msg
    save_data()
    
    update.message.reply_text("✅ Goodbye message set.")

def set_rules_command(update: Update, context: CallbackContext) -> None:
    """Set chat rules."""
    if not is_admin(update, context):
        update.message.reply_text("🚫 You don't have permission to use this command.")
        return
    
    if not context.args:
        update.message.reply_text("Please provide chat rules.")
        return
    
    chat_id = update.effective_chat.id
    rules_msg = ' '.join(context.args)
    
    if str(chat_id) not in user_data:
        user_data[str(chat_id)] = {}
    
    user_data[str(chat_id)]["rules"] = rules_msg
    save_data()
    
    update.message.reply_text("✅ Chat rules set.")

def set_antispam(update: Update, context: CallbackContext) -> None:
    """Set anti-spam settings."""
    if not is_admin(update, context):
        update.message.reply_text("🚫 You don't have permission to use this command.")
        return
    
    if not context.args or len(context.args) != 2:
        update.message.reply_text("Usage: /set_antispam <messages> <seconds>")
        return
    
    try:
        messages = int(context.args[0])
        seconds = int(context.args[1])
        
        chat_id = update.effective_chat.id
        
        if str(chat_id) not in user_data:
            user_data[str(chat_id)] = {}
        
        user_data[str(chat_id)]["antispam"] = {
            "messages": messages,
            "seconds": seconds
        }
        save_data()
        
        update.message.reply_text(
            f"✅ Anti-spam set: {messages} messages in {seconds} seconds"
        )
    except ValueError:
        update.message.reply_text("Please provide valid numbers.")

def set_antiflood(update: Update, context: CallbackContext) -> None:
    """Set anti-flood settings."""
    if not is_admin(update, context):
        update.message.reply_text("🚫 You don't have permission to use this command.")
        return
    
    if not context.args or len(context.args) != 2:
        update.message.reply_text("Usage: /set_antiflood <messages> <seconds>")
        return
    
    try:
        messages = int(context.args[0])
        seconds = int(context.args[1])
        
        chat_id = update.effective_chat.id
        
        if str(chat_id) not in user_data:
            user_data[str(chat_id)] = {}
        
        user_data[str(chat_id)]["antiflood"] = {
            "messages": messages,
            "seconds": seconds
        }
        save_data()
        
        update.message.reply_text(
            f"✅ Anti-flood set: {messages} messages in {seconds} seconds"
        )
    except ValueError:
        update.message.reply_text("Please provide valid numbers.")

# MESSAGE HANDLER
def handle_message(update: Update, context: CallbackContext) -> None:
    """Handle incoming messages."""
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    message_text = update.message.text.lower() if update.message.text else ""
    
    # Check filters
    if str(chat_id) in user_data and "filters" in user_data[str(chat_id)]:
        for keyword, filter_data in user_data[str(chat_id)]["filters"].items():
            if keyword in message_text:
                if filter_data.get("text"):
                    update.message.reply_text(filter_data["text"])
                if filter_data.get("photo"):
                    update.message.reply_photo(filter_data["photo"])
                if filter_data.get("sticker"):
                    update.message.reply_sticker(filter_data["sticker"])
                break

# BUTTON HANDLER
def button(update: Update, context: CallbackContext) -> None:
    """Handle button presses."""
    query = update.callback_query
    query.answer()
    
    data = query.data
    
    if data == 'main_menu':
        main_menu(update, context)
    elif data == 'admin_commands':
        admin_commands(update, context)
    elif data == 'user_commands':
        user_commands(update, context)
    elif data == 'fun_commands':
        fun_commands(update, context)
    elif data == 'settings':
        settings(update, context)
    elif data == 'sudo_menu':
        sudo_menu(update, context)
    elif data == 'add_sudo':
        query.edit_message_text("Use /addsudo <user_id> to add a sudo user.")
    elif data == 'remove_sudo':
        query.edit_message_text("Use /removesudo <user_id> to remove a sudo user.")
    elif data == 'list_sudo':
        listsudo(update, context)
    elif data == 'backup_data':
        backup(update, context)
    elif data == 'restore_data':
        query.edit_message_text("Restore feature coming soon.")
    elif data == 'bot_stats':
        stats(update, context)
    elif data == 'global_broadcast':
        query.edit_message_text("Use /broadcast <message> to send a global message.")
    elif data == 'maintenance_mode':
        maintenance(update, context)
    elif data in ['ban', 'unban', 'kick', 'mute', 'unmute', 'warn', 'unwarn', 
                  'promote', 'demote', 'purge', 'filter', 'stop', 'filterlist', 
                  'gban', 'lockall', 'unlockall', 'dwarn', 'dmute']:
        query.edit_message_text(f"Use /{data} command to {data.replace('_', ' ')}.")
    elif data in ['info', 'id', 'rules', 'help']:
        query.edit_message_text(f"Use /{data} command to get {data.replace('_', ' ')}.")
    elif data in ['roll_dice', 'flip_coin', 'random_number', 'quote', 'trivia', 'random_color']:
        query.edit_message_text(f"Use /{data} command for {data.replace('_', ' ')}.")
    elif data in ['set_welcome', 'set_goodbye', 'set_rules', 'set_antispam', 'set_antiflood', 'set_blacklist']:
        query.edit_message_text(f"Use /{data} command to set {data.replace('set_', '').replace('_', ' ')}.")

def main():
    """Start the bot."""
    updater = Updater(TOKEN, use_context=True)
    dispatcher = updater.dispatcher
    
    # Command handlers
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(CommandHandler("sudohelp", sudohelp))
    
    # Admin commands
    dispatcher.add_handler(CommandHandler("ban", ban))
    dispatcher.add_handler(CommandHandler("unban", unban))
    dispatcher.add_handler(CommandHandler("kick", kick))
    dispatcher.add_handler(CommandHandler("mute", mute))
    dispatcher.add_handler(CommandHandler("unmute", unmute))
    dispatcher.add_handler(CommandHandler("warn", warn))
    dispatcher.add_handler(CommandHandler("unwarn", unwarn))
    dispatcher.add_handler(CommandHandler("promote", promote))
    dispatcher.add_handler(CommandHandler("demote", demote))
    dispatcher.add_handler(CommandHandler("purge", purge))
    dispatcher.add_handler(CommandHandler("filter", filter_message))
    dispatcher.add_handler(CommandHandler("stop", stop_filter))
    dispatcher.add_handler(CommandHandler("filterlist", filter_list))
    dispatcher.add_handler(CommandHandler("gban", gban))
    dispatcher.add_handler(CommandHandler("lockall", lockall))
    dispatcher.add_handler(CommandHandler("unlockall", unlockall))
    dispatcher.add_handler(CommandHandler("dwarn", delete_and_warn))
    dispatcher.add_handler(CommandHandler("dmute", delete_and_mute))
    
    # User commands
    dispatcher.add_handler(CommandHandler("info", info))
    dispatcher.add_handler(CommandHandler("id", id_command))
    dispatcher.add_handler(CommandHandler("rules", rules))
    
    # Fun commands
    dispatcher.add_handler(CommandHandler("roll", roll_dice))
    dispatcher.add_handler(CommandHandler("flip", flip_coin))
    dispatcher.add_handler(CommandHandler("random", random_number))
    dispatcher.add_handler(CommandHandler("quote", quote))
    dispatcher.add_handler(CommandHandler("trivia", trivia))
    dispatcher.add_handler(CommandHandler("color", random_color))
    
    # Settings
    dispatcher.add_handler(CommandHandler("set_welcome", set_welcome))
    dispatcher.add_handler(CommandHandler("set_goodbye", set_goodbye))
    dispatcher.add_handler(CommandHandler("set_rules", set_rules_command))
    dispatcher.add_handler(CommandHandler("set_antispam", set_antispam))
    dispatcher.add_handler(CommandHandler("set_antiflood", set_antiflood))
    
    # Sudo commands
    dispatcher.add_handler(CommandHandler("addsudo", addsudo))
    dispatcher.add_handler(CommandHandler("removesudo", removesudo))
    dispatcher.add_handler(CommandHandler("listsudo", listsudo))
    dispatcher.add_handler(CommandHandler("backup", backup))
    dispatcher.add_handler(CommandHandler("stats", stats))
    dispatcher.add_handler(CommandHandler("broadcast", broadcast))
    dispatcher.add_handler(CommandHandler("maintenance", maintenance))
    
    # Message handler
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    
    # Button handler
    dispatcher.add_handler(CallbackQueryHandler(button))
    
    # Start bot
    updater.start_polling()
    print(f"🔥 LegendBot is now online! Managed by {OWNER_USERNAME}")
    
    # Save data on shutdown
    import atexit
    atexit.register(save_data)
    
    updater.idle()

if __name__ == '__main__':
    main()
