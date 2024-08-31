import telebot
from googlesearch import search
import requests
import time
from pymongo import MongoClient
from datetime import datetime

# Initialize MongoDB client
mongo_client = MongoClient('mongodb+srv://admin22:admin22@cluster0.9lqp0ci.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')
db = mongo_client.bot_logs
logs_collection = db.logs

# Replace 'YOUR_TELEGRAM_BOT_TOKEN' with your actual Telegram bot token
bot = telebot.TeleBot('7261872696:AAEH1K74ieC8mLSyt7Uj2H1w_DBSnchEto4')

# Owner ID
OWNER_ID = 5460343986

# Channel and group usernames
FORCE_JOIN_CHANNELS = ["@FALCON_SECURITY", "@Bot_Colony"]
FORCE_JOIN_GROUPS = ["@Indian_Hacker_Group"]

# Group ID for logging
LOG_GROUP_ID = -1002155266073

# Dictionary to store authorized users
authorized_users = {OWNER_ID}
proxy_api_url = 'https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all'

# Dictionary to store search results for each user
user_search_results = {}

# Function to get proxies from the API
def get_proxies():
    response = requests.get(proxy_api_url)
    proxies = response.text.splitlines()
    return proxies

proxies = get_proxies()

# Function to check if a user is a member of the required channels/groups
def is_user_member(user_id):
    for channel in FORCE_JOIN_CHANNELS:
        try:
            member_status = bot.get_chat_member(channel, user_id).status
            if member_status not in ['member', 'administrator', 'creator']:
                return False
        except:
            return False
    for group in FORCE_JOIN_GROUPS:
        try:
            member_status = bot.get_chat_member(group, user_id).status
            if member_status not in ['member', 'administrator', 'creator']:
                return False
        except:
            return False
    return True

# Log user actions to MongoDB and log group
def log_user_action(user_id, action, extra_info=""):
    log_entry = {
        'user_id': user_id,
        'action': action,
        'extra_info': extra_info,
        'timestamp': datetime.now(datetime.timezone.utc)  # Updated to use timezone-aware datetime
    }
    logs_collection.insert_one(log_entry)
    log_message = f"Action: {action}\nUser ID: {user_id}\nExtra Info: {extra_info}\nTimestamp: {datetime.now(datetime.timezone.utc)}"  # Updated to use timezone-aware datetime
    bot.send_message(LOG_GROUP_ID, log_message)

# Welcome message with inline button layout
@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    
    # Add inline buttons for each channel and group
    buttons = [
        telebot.types.InlineKeyboardButton("FALCON SECURITY", url='https://t.me/FALCON_SECURITY'),
        telebot.types.InlineKeyboardButton("BOT COLONY", url='https://t.me/Bot_Colony'),
        telebot.types.InlineKeyboardButton("INDIAN HACKER", url='https://t.me/Indian_Hacker_Group'),
        telebot.types.InlineKeyboardButton("INDIAN HACKER GROUP", url='https://t.me/Indian_Hacker_Group')
    ]
    
    # Arrange buttons in the specified format
    markup.add(buttons[0], buttons[1])  # Button1 : Button2
    markup.add(buttons[2], buttons[3])  # Button3 : Button4

    # Add a verification button
    verify_button = telebot.types.InlineKeyboardButton("VERIFY", callback_data='verify')
    markup.add(verify_button)
    
    # Send the image with the message
    bot.send_photo(message.chat.id, photo='https://i.ibb.co/Jcf4gyy/20240126-165040-0000.png', caption="Please join all the required channels and groups first. After joining, click the 'VERIFY' button.", reply_markup=markup)
    
    # Log the start command
    log_user_action(message.from_user.id, 'started_bot')

# Verify button callback
@bot.callback_query_handler(func=lambda call: call.data == 'verify')
def verify_user(call):
    user_id = call.from_user.id
    if is_user_member(user_id):
        bot.send_message(call.message.chat.id, "Thank you for joining all the required channels and groups! You can now use the bot. Use /help to see available commands.")
        # Optionally, add the user to the authorized list if you want to
        authorized_users.add(user_id)
        log_user_action(user_id, 'verified')
    else:
        bot.send_message(call.message.chat.id, "Please join all the required channels and groups first before clicking 'VERIFY'.")
    bot.answer_callback_query(call.id)

# Help command
@bot.message_handler(commands=['help'])
def send_help(message):
    help_message = """
Available commands:
/search <query> - Search Google with the given query.
/add <user_id> - Add a user to the authorized list (Owner only).
/remove <user_id> - Remove a user from the authorized list (Owner only).
/broadcast <message> - Send a broadcast message to all authorized users (Owner only).
/txt <query> - Get search results in TXT format.
/users - Show all authorized users (Owner only).
/help - Show this help message.
"""
    bot.reply_to(message, help_message)

MAX_MESSAGE_LENGTH = 4096  # Maximum length of a message that Telegram allows

# Command handler to provide search results in TXT format
@bot.message_handler(commands=['txt'])
def provide_results_txt(message):
    if not is_user_member(message.from_user.id):
        bot.reply_to(message, "You must join the required channels and groups to use this bot.")
        return

    if message.from_user.id in authorized_users:
        if len(message.text.split()) > 1:
            query = message.text.split(' ', 1)[1]
            results = list(search(query, num_results=80))
            txt_result = "\n".join(results)
            for i in range(0, len(txt_result), MAX_MESSAGE_LENGTH):
                bot.send_message(message.chat.id, txt_result[i:i + MAX_MESSAGE_LENGTH])
            bot.reply_to(message, "Search results in TXT format have been sent.")
            log_user_action(message.from_user.id, 'searched', f"Query: {query}")
        else:
            bot.reply_to(message, "Please provide a query to search. Example: /txt your_query_here")
    else:
        bot.reply_to(message, "You are not authorized to use this command.")

# Command handler to search Google
@bot.message_handler(commands=['search'])
def search_google(message):
    if not is_user_member(message.from_user.id):
        bot.reply_to(message, "You must join the required channels and groups to use this bot.")
        return

    if message.from_user.id in authorized_users:
        if len(message.text.split()) == 1:
            bot.reply_to(message, "Please provide a query to search.")
            return

        query = message.text.split(' ', 1)[1]
        results = list(search(query, num_results=80))

        if results:
            user_search_results[message.from_user.id] = {'query': query, 'results': results, 'index': 0}
            send_search_results(message.chat.id, message.from_user.id)
            log_user_action(message.from_user.id, 'searched', f"Query: {query}")
        else:
            bot.reply_to(message, "No results found for '{}'. Please try a different query.".format(query))
    else:
        bot.reply_to(message, "You are not authorized to use this command.")

def send_search_results(chat_id, user_id, num_results=20):
    if user_id in user_search_results:
        user_data = user_search_results[user_id]
        results = user_data['results']
        start_index = user_data['index']
        end_index = min(start_index + num_results, len(results))

        response = "Search results for '{}':\n".format(user_data['query'])
        for i, result in enumerate(results[start_index:end_index], start=start_index + 1):
            response += "{}. {}\n".format(i, result)

        # Split the response if it's too long
        for i in range(0, len(response), MAX_MESSAGE_LENGTH):
            bot.send_message(chat_id, response[i:i + MAX_MESSAGE_LENGTH])

        user_data['index'] = end_index

        if end_index < len(results):
            markup = telebot.types.InlineKeyboardMarkup()
            more_button = telebot.types.InlineKeyboardButton("More", callback_data='more')
            markup.add(more_button)
            bot.send_message(chat_id, "Click 'More' for additional results.", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == 'more')
def handle_more(call):
    user_id = call.from_user.id
    if user_id in user_search_results:
        send_search_results(call.message.chat.id, user_id)
    bot.answer_callback_query(call.id)

# Command handler to add user
@bot.message_handler(commands=['add'])
def add_user(message):
    if message.from_user.id == OWNER_ID:
        if len(message.text.split()) == 2:
            try:
                user_id = int(message.text.split()[1])
                authorized_users.add(user_id)
                bot.reply_to(message, f"User {user_id} added to the authorized list.")
                log_user_action(user_id, 'added_to_authorized_list')
            except ValueError:
                bot.reply_to(message, "Invalid user ID format. Please provide a numeric user ID.")
        else:
            bot.reply_to(message, "Please provide the user ID to add.")
    else:
        bot.reply_to(message, "You are not authorized to use this command.")

# Command handler to remove user
@bot.message_handler(commands=['remove'])
def remove_user(message):
    if message.from_user.id == OWNER_ID:
        if len(message.text.split()) == 2:
            try:
                user_id = int(message.text.split()[1])
                if user_id in authorized_users:
                    authorized_users.remove(user_id)
                    bot.reply_to(message, f"User {user_id} removed from the authorized list.")
                    log_user_action(user_id, 'removed_from_authorized_list')
                else:
                    bot.reply_to(message, "User ID not found in the authorized list.")
            except ValueError:
                bot.reply_to(message, "Invalid user ID format. Please provide a numeric user ID.")
        else:
            bot.reply_to(message, "Please provide the user ID to remove.")
    else:
        bot.reply_to(message, "You are not authorized to use this command.")

# Command handler to broadcast a message
@bot.message_handler(commands=['broadcast'])
def broadcast_message(message):
    if message.from_user.id == OWNER_ID:
        if len(message.text.split()) > 1:
            broadcast_text = message.text.split(' ', 1)[1]
            for user_id in authorized_users:
                try:
                    bot.send_message(user_id, broadcast_text)
                except Exception as e:
                    print(f"Failed to send message to user {user_id}: {e}")
            bot.reply_to(message, "Broadcast message sent to all authorized users.")
            log_user_action(message.from_user.id, 'broadcast_message', broadcast_text)
        else:
            bot.reply_to(message, "Please provide a message to broadcast.")
    else:
        bot.reply_to(message, "You are not authorized to use this command.")

# Command handler to show authorized users
@bot.message_handler(commands=['users'])
def show_users(message):
    if message.from_user.id == OWNER_ID:
        if authorized_users:
            users_list = "\n".join(str(user_id) for user_id in authorized_users)
            bot.reply_to(message, "Authorized users:\n" + users_list)
        else:
            bot.reply_to(message, "No authorized users found.")
    else:
        bot.reply_to(message, "You are not authorized to use this command.")

# Polling the bot
if __name__ == '__main__':
    bot.polling(none_stop=True)
