import telebot
from googlesearch import search
import requests
import os
from pymongo import MongoClient
from datetime import datetime
import urllib.parse

# Initialize MongoDB client
mongo_client = MongoClient('mongodb+srv://admin22:admin22@cluster0.9lqp0ci.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')
db = mongo_client.bot_logs
logs_collection = db.logs

# Replace 'YOUR_TELEGRAM_BOT_TOKEN' with your actual Telegram bot token
bot = telebot.TeleBot('7261872696:AAEH1K74ieC8mLSyt7Uj2H1w_DBSnchEto4')

# Owner ID
OWNER_ID = 5460343986

# Channel and group usernames
FORCE_JOIN_CHANNELS = ["@FALCON_SECURITY", "@QuantumEthics", "@Bot_Colony"]
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
        except Exception as e:
            print(f"Error checking membership in channel {channel}: {e}")
            return False

    for group in FORCE_JOIN_GROUPS:
        try:
            member_status = bot.get_chat_member(group, user_id).status
            if member_status not in ['member', 'administrator', 'creator']:
                return False
        except Exception as e:
            print(f"Error checking membership in group {group}: {e}")
            return False

    return True

# Log user actions to MongoDB and log group
def log_user_action(user_id, action, extra_info=""):
    log_entry = {
        'user_id': user_id,
        'action': action,
        'extra_info': extra_info,
        'timestamp': datetime.utcnow()
    }
    logs_collection.insert_one(log_entry)
    log_message = f"Action: {action}\nUser ID: {user_id}\nExtra Info: {extra_info}\nTimestamp: {datetime.utcnow()}"
    bot.send_message(LOG_GROUP_ID, log_message)

# Welcome message with inline button layout
@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    
    # Add inline buttons for each channel and group
    buttons = [
        telebot.types.InlineKeyboardButton("FALCON SECURITY", url='https://t.me/FALCON_SECURITY'),
        telebot.types.InlineKeyboardButton("BOT COLONY", url='https://t.me/Bot_Colony'),
        telebot.types.InlineKeyboardButton("QuantumEthics", url='https://t.me/QuantumEthics'),
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
/search <query> - Search Google with the given query and get 500 links. Provides 100 links per user with a 'More' button to fetch more.
/add <user_id> - Add a user to the authorized list (Owner only).
/remove <user_id> - Remove a user from the authorized list (Owner only).
/broadcast <message> - Send a broadcast message to all authorized users (Owner only).
/txt <query> - Get search results in TXT format.
/users - Show all authorized users (Owner only).
/help - Show this help message.
"""
    bot.reply_to(message, help_message)

MAX_MESSAGE_LENGTH = 4096  # Maximum length of a message that Telegram allows
RESULTS_PER_PAGE = 20  # Number of results per page
RESULTS_PER_USER = 100  # Total number of results each user can get
TOTAL_RESULTS = 300  # Total number of results to fetch

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
        file_path = f"search_results_{urllib.parse.quote(query)}.txt"

        if os.path.exists(file_path):
            # File exists, load and send results
            send_search_results(message.chat.id, message.from_user.id, file_path)
        else:
            # Perform search and save to file
            results = list(search(query, num_results=TOTAL_RESULTS))
            with open(file_path, 'w') as file:
                for result in results:
                    file.write(result + '\n')

            user_search_results[message.from_user.id] = {
                'query': query,
                'file_path': file_path,
                'index': 0
            }

            send_search_results(message.chat.id, message.from_user.id, file_path)
            log_user_action(message.from_user.id, 'searched', f"Query: {query}")
    else:
        bot.reply_to(message, "You are not authorized to use this command.")

def send_search_results(chat_id, user_id, file_path):
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            lines = file.readlines()
        
        user_data = user_search_results.get(user_id, {'index': 0})
        start_index = user_data['index']
        end_index = min(start_index + RESULTS_PER_PAGE, RESULTS_PER_USER)
        
        results_to_send = lines[start_index:end_index]
        response = "Search results:\n"
        for i, result in enumerate(results_to_send, start=start_index + 1):
            response += "{}. {}\n".format(i, result.strip())

        # Send results in chunks if the response is too long
        for i in range(0, len(response), MAX_MESSAGE_LENGTH):
            bot.send_message(chat_id, response[i:i + MAX_MESSAGE_LENGTH])
        
        user_data['index'] = end_index
        user_search_results[user_id] = user_data
        
        if end_index < RESULTS_PER_USER:
            markup = telebot.types.InlineKeyboardMarkup()
            more_button = telebot.types.InlineKeyboardButton("More", callback_data=f'more:{urllib.parse.quote(file_path)}:{end_index}:{user_id}')
            markup.add(more_button)
            bot.send_message(chat_id, "Click 'More' for additional results.", reply_markup=markup)
        
        # Update file to remove sent results
        with open(file_path, 'w') as file:
            file.writelines(lines[end_index:])

# Handle 'More' button callback
@bot.callback_query_handler(func=lambda call: call.data.startswith('more:'))
def handle_more_results(call):
    try:
        data = call.data.split(':', 3)
        if len(data) != 4:
            raise ValueError("Invalid callback data format")

        safe_file_path = data[1]
        start_index = int(data[2])
        user_id = int(data[3])

        file_path = urllib.parse.unquote(safe_file_path)  # Decode file path
        
        if user_id in user_search_results and user_search_results[user_id]['file_path'] == file_path:
            with open(file_path, 'r') as file:
                lines = file.readlines()

            user_data = user_search_results[user_id]
            end_index = min(start_index + RESULTS_PER_PAGE, RESULTS_PER_USER)
            results_to_send = lines[start_index:end_index]

            response = "Search results:\n"
            for i, result in enumerate(results_to_send, start=start_index + 1):
                response += "{}. {}\n".format(i, result.strip())

            # Send results in chunks if the response is too long
            for i in range(0, len(response), MAX_MESSAGE_LENGTH):
                bot.send_message(call.message.chat.id, response[i:i + MAX_MESSAGE_LENGTH])
            
            user_data['index'] = end_index
            user_search_results[user_id] = user_data
            
            if end_index < RESULTS_PER_USER:
                markup = telebot.types.InlineKeyboardMarkup()
                more_button = telebot.types.InlineKeyboardButton("More", callback_data=f'more:{urllib.parse.quote(file_path)}:{end_index}:{user_id}')
                markup.add(more_button)
                bot.send_message(call.message.chat.id, "Click 'More' for additional results.", reply_markup=markup)
            
            # Update file to remove sent results
            with open(file_path, 'w') as file:
                file.writelines(lines[end_index:])
        
        bot.answer_callback_query(call.id)
    except Exception as e:
        print(f"Error handling 'More' callback: {e}")
        bot.answer_callback_query(call.id, text="Failed to load more results.")

# Add user to the authorized list (Owner only)
@bot.message_handler(commands=['add'])
def add_user(message):
    if message.from_user.id == OWNER_ID:
        try:
            user_id = int(message.text.split()[1])
            authorized_users.add(user_id)
            bot.reply_to(message, f"User {user_id} has been added to the authorized list.")
            log_user_action(message.from_user.id, 'added_user', f"User ID: {user_id}")
        except (IndexError, ValueError) as e:
            bot.reply_to(message, "Please provide a valid user ID.")
            print(f"Error adding user: {e}")
    else:
        bot.reply_to(message, "You are not authorized to use this command.")

# Remove user from the authorized list (Owner only)
@bot.message_handler(commands=['remove'])
def remove_user(message):
    if message.from_user.id == OWNER_ID:
        try:
            user_id = int(message.text.split()[1])
            if user_id in authorized_users:
                authorized_users.remove(user_id)
                bot.reply_to(message, f"User {user_id} has been removed from the authorized list.")
                log_user_action(message.from_user.id, 'removed_user', f"User ID: {user_id}")
            else:
                bot.reply_to(message, f"User {user_id} is not in the authorized list.")
        except (IndexError, ValueError) as e:
            bot.reply_to(message, "Please provide a valid user ID.")
            print(f"Error removing user: {e}")
    else:
        bot.reply_to(message, "You are not authorized to use this command.")

# Broadcast message to all authorized users (Owner only)
@bot.message_handler(commands=['broadcast'])
def broadcast_message(message):
    if message.from_user.id == OWNER_ID:
        msg = ' '.join(message.text.split()[1:])
        for user_id in authorized_users:
            try:
                bot.send_message(user_id, msg)
            except Exception as e:
                print(f"Error sending broadcast to {user_id}: {e}")
        bot.reply_to(message, "Message broadcasted to all authorized users.")
        log_user_action(message.from_user.id, 'broadcasted_message', f"Message: {msg}")
    else:
        bot.reply_to(message, "You are not authorized to use this command.")

# Get search results in TXT format
@bot.message_handler(commands=['txt'])
def get_txt_results(message):
    if not is_user_member(message.from_user.id):
        bot.reply_to(message, "You must join the required channels and groups to use this bot.")
        return

    if message.from_user.id in authorized_users:
        if len(message.text.split()) == 1:
            bot.reply_to(message, "Please provide a query to search.")
            return

        query = message.text.split(' ', 1)[1]
        file_path = f"search_results_{urllib.parse.quote(query)}.txt"

        if os.path.exists(file_path):
            with open(file_path, 'r') as file:
                result_text = file.read()
            bot.send_document(message.chat.id, document=open(file_path, 'rb'))
            log_user_action(message.from_user.id, 'retrieved_txt_results', f"Query: {query}")
        else:
            bot.reply_to(message, "No results found. Please perform a search first.")
    else:
        bot.reply_to(message, "You are not authorized to use this command.")

# Show all authorized users (Owner only)
@bot.message_handler(commands=['users'])
def show_users(message):
    if message.from_user.id == OWNER_ID:
        users_list = '\n'.join(str(user_id) for user_id in authorized_users)
        bot.reply_to(message, f"Authorized users:\n{users_list}")
        log_user_action(message.from_user.id, 'viewed_authorized_users')
    else:
        bot.reply_to(message, "You are not authorized to use this command.")

# Start polling
bot.polling(none_stop=True)
