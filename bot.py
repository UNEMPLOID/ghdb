import telebot
import requests
import time

# Replace with your actual credentials
BOT_TOKEN = '6945433492:AAHPvr6R1tqKiyyzAtZ2N2kcOy6AncEe5QY'
GOOGLE_API_KEY = 'AIzaSyBiBPVUGk-JARig_YklRDMbebm2vKhUY2w'
CSE_ID = 'your_custom_search_engine_id'

bot = telebot.TeleBot(BOT_TOKEN)

# Owner ID
OWNER_ID = 5460343986

# Channel username
CHANNEL_USERNAME = "@FALCON_SECURITY"

# Dictionary to store authorized users
authorized_users = {OWNER_ID}

# Dictionary to store search results for each user
user_search_results = {}

# Function to get proxies from the API
proxy_api_url = 'https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all'
def get_proxies():
    response = requests.get(proxy_api_url)
    proxies = response.text.splitlines()
    return proxies

proxies = get_proxies()

# Function to check if a user is a member of the channel
def is_user_member(user_id):
    try:
        member_status = bot.get_chat_member(CHANNEL_USERNAME, user_id).status
        return member_status in ['member', 'administrator', 'creator']
    except:
        return False

# Function to perform Google search using Custom Search API
def google_search(query, num_results=10):
    search_url = f"https://www.googleapis.com/customsearch/v1?key={GOOGLE_API_KEY}&cx={CSE_ID}&q={query}&num={num_results}"
    response = requests.get(search_url)
    data = response.json()
    results = []
    for item in data.get('items', []):
        results.append(item['link'])
    return results

# Welcome message
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Welcome to the Google Dork Search Bot! Use /help to see available commands.")

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
        bot.reply_to(message, f"You must join {CHANNEL_USERNAME} to use this bot.")
        return

    if message.from_user.id in authorized_users:
        if len(message.text.split()) > 1:
            query = message.text.split(' ', 1)[1]
            results = google_search(query, num_results=80)
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
        bot.reply_to(message, f"You must join {CHANNEL_USERNAME} to use this bot.")
        return

    if message.from_user.id in authorized_users:
        if len(message.text.split()) == 1:
            bot.reply_to(message, "Please provide a query to search.")
            return

        query = message.text.split(' ', 1)[1]
        results = google_search(query, num_results=10)

        if results:
            user_search_results[message.from_user.id] = {'query': query, 'results': results, 'index': 0}
            send_search_results(message.chat.id, message.from_user.id)
        else:
            bot.reply_to(message, "No results found for '{}'. Please try a different query.".format(query))
    else:
        bot.reply_to(message, "You are not authorized to use this command.")

# Function to send search results in parts
def send_search_results(chat_id, user_id, num_results=10):
    if user_id in user_search_results:
        user_data = user_search_results[user_id]
        results = user_data['results']
        start_index = user_data['index']
        end_index = min(start_index + num_results, len(results))

        response = "Search results for '{}':\n".format(user_data['query'])
        for i, result in enumerate(results[start_index:end_index], start=start_index + 1):
            response += "{}. {}\n".format(i, result)

        # If the response is too long, send it in chunks
        if len(response) > MAX_MESSAGE_LENGTH:
            parts = [response[i:i + MAX_MESSAGE_LENGTH] for i in range(0, len(response), MAX_MESSAGE_LENGTH)]
            for part in parts:
                bot.send_message(chat_id, part)
        else:
            bot.send_message(chat_id, response)

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
    except telebot.apihelper.ApiTelegramException as e:
        print(f"Telegram API error: {e}")
        time.sleep(15)
    except Exception as e:
        print(f"An error occurred: {e}")
        time.sleep(15)
