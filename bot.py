import telebot
from googlesearch import search
import requests
import time

# Replace 'YOUR_TELEGRAM_BOT_TOKEN' with your actual Telegram bot token
bot = telebot.TeleBot('7261872696:AAEH1K74ieC8mLSyt7Uj2H1w_DBSnchEto4')

# Owner ID
OWNER_ID = 5460343986

# Channel and group usernames
FORCE_JOIN_CHANNELS = ["@FALCON_SECURITY", "@Bot_Colony", "@Found_Us"]
FORCE_JOIN_GROUPS = ["@Indian_Hacker_Group"]

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

# Welcome message
@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = telebot.types.InlineKeyboardMarkup()
    
    # Add inline buttons for each channel and group
    for channel in FORCE_JOIN_CHANNELS:
        button = telebot.types.InlineKeyboardButton(channel, url=f'https://t.me/{channel[1:]}')
        markup.add(button)
    for group in FORCE_JOIN_GROUPS:
        button = telebot.types.InlineKeyboardButton(group, url=f'https://t.me/{group[1:]}')
        markup.add(button)
    
    # Add a verification button
    verify_button = telebot.types.InlineKeyboardButton("Verify", callback_data='verify')
    markup.add(verify_button)
    
    bot.send_message(message.chat.id, "Please join all the required channels and groups first. After joining, click the 'Verify' button.", reply_markup=markup)

# Verify button callback
@bot.callback_query_handler(func=lambda call: call.data == 'verify')
def verify_user(call):
    user_id = call.from_user.id
    if is_user_member(user_id):
        bot.send_message(call.message.chat.id, "Thank you for joining all the required channels and groups! You can now use the bot. Use /help to see available commands.")
        # Optionally, add the user to the authorized list if you want to
        authorized_users.add(user_id)
    else:
        bot.send_message(call.message.chat.id, "Please join all the required channels and groups first before clicking 'Verify'.")
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
            results = list(search(query, num=80, stop=300, pause=2))
            txt_result = "\n".join(results)
            for i in range(0, len(txt_result), MAX_MESSAGE_LENGTH):
                bot.send_message(message.chat.id, txt_result[i:i + MAX_MESSAGE_LENGTH])
            bot.reply_to(message, "Search results in TXT format have been sent.")
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
        results = list(search(query, num=80, stop=300, pause=2))

        if results:
            user_search_results[message.from_user.id] = {'query': query, 'results': results, 'index': 0}
            send_search_results(message.chat.id, message.from_user.id)
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
        if len(message.text.split()) > 1:
            user_id = message.text.split(' ', 1)[1]
            authorized_users.add(int(user_id))
            bot.reply_to(message, "User {} has been added.".format(user_id))
        else:
            bot.reply_to(message, "Please provide the user ID to add. Example: /add user_id")
    else:
        bot.reply_to(message, "Only the owner can use this command.")

# Command handler to remove user
@bot.message_handler(commands=['remove'])
def remove_user(message):
    if message.from_user.id == OWNER_ID:
        if len(message.text.split()) > 1:
            user_id = message.text.split(' ', 1)[1]
            if int(user_id) in authorized_users:
                authorized_users.remove(int(user_id))
                bot.reply_to(message, "User {} has been removed.".format(user_id))
            else:
                bot.reply_to(message, "User {} is not in the authorized list.".format(user_id))
        else:
            bot.reply_to(message, "Please provide the user ID to remove. Example: /remove user_id")
    else:
        bot.reply_to(message, "Only the owner can use this command.")

# Command handler to broadcast message
@bot.message_handler(commands=['broadcast'])
def broadcast_message(message):
    if message.from_user.id == OWNER_ID:
        if len(message.text.split()) > 1:
            text = message.text.split(' ', 1)[1]
            for user_id in authorized_users:
                bot.send_message(user_id, text)
            bot.reply_to(message, "Broadcast sent to {} users.".format(len(authorized_users)))
        else:
            bot.reply_to(message, "Please provide a message to broadcast. Example: /broadcast your_message_here")
    else:
        bot.reply_to(message, "Only the owner can use this command.")

# Command handler to show all authorized users
@bot.message_handler(commands=['users'])
def show_users(message):
    if message.from_user.id == OWNER_ID:
        user_list = '\n'.join(str(user_id) for user_id in authorized_users)
        response = f"List of authorized users:\n{user_list}"
        bot.reply_to(message, response)
    else:
        bot.reply_to(message, "Only the owner can use this command. Please click on /help for more information.")

# Start polling with error handling
while True:
    try:
        bot.polling()
    except requests.exceptions.ReadTimeout:
        print("Read timeout occurred, retrying in 15 seconds...")
        time.sleep(15)
    except requests.exceptions.ConnectionError:
        print("Connection error occurred, retrying in 15 seconds...")
        time.sleep(15)
    except Exception as e:
        print(f"An error occurred: {e}")
        time.sleep(15)
