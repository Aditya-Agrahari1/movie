import logging
import os
import random
import re
import pytz
import time
from telegram import Update,InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from datetime import datetime, timedelta
from functools import wraps

# Replace with your bot token and private group ID
BOT_TOKEN = '6666329738:AAFj6ziEoQQW9ppEg-3EINbgHheuxU7K7MM'
CHANNEL_ID = -1002077386138  # Use the numeric ID for your private group

ist_timezone = pytz.timezone('Asia/Kolkata')


# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Global counter variable and usage tracking
counter = 0
user_command_usage = {}  # Dictionary to track each user's /surprise usage
user_ids = set()  # Set to store unique user IDs

# Load user IDs from file on startup
WATCHLIST_FOLDER = 'watchlists/'



def custom_retry():
    retries = 3
    delay = 5  # seconds
    while retries > 0:
        try:
            # Your bot code to connect to Telegram
            break  # If successful, break the loop
        except Exception as e:
            retries -= 1
            if retries > 0:
                time.sleep(delay)
            else:
                raise e  # After exhausting retries, raise the exception

# Function to handle the /start command
def is_user_subscribed(user_id, bot, channel_username):
    try:
        member_status = bot.get_chat_member(chat_id=channel_username, user_id=user_id).status
        return member_status in ['member', 'administrator', 'creator']
    except Exception as e:
        logger.error(f"Error checking subscription status: {e}")
        return False

def require_subscription(func):
    @wraps(func)
    def wrapper(update, context, *args, **kwargs):
        user_id = update.effective_user.id
        first_name = update.effective_user.first_name  # Get the user's first name
        channel_username = '@StarkFlixx'  # Your channel username
        video_id = context.args[0] if context.args and context.args[0].isdigit() else None  # Capture video_id if passed

        # Check if the user is subscribed
        if not is_user_subscribed(user_id, context.bot, channel_username):
            # Send a message prompting the user to subscribe with an inline keyboard
            try_again_url = f"https://t.me/starksventures_bot?start={video_id}" if video_id else "https://t.me/starksventures_bot"
            keyboard = [
                [InlineKeyboardButton("Join Channel", url=f"https://t.me/{channel_username[1:]}")],
                [InlineKeyboardButton("Try Again!", url=try_again_url)]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            message = update.message or update.callback_query.message
            message.reply_text(
                f"⚠️ Dear {first_name}, you must join our official channel to use this bot.\n"
                "Please join and then tap 'Try Again!' to access the bot.",
                reply_markup=reply_markup
            )
            return  # Exit if the user is not subscribed

        # If the user is subscribed, proceed with the command
        return func(update, context, *args, **kwargs)
    return wrapper


# Global dictionary to track usage stats
command_usage = {
    "start": 0,
    "contact_owner": 0,
    "request": 0,
    "surpriseme": 0,
    "feedback": 0,
    "reply7398": 0,
    "broadcast": 0,
    "add_to_watchlist": 0,
    "remove_from_watchlist": 0,
    "show_watchlist": 0,
    "admin_show_watchlist": 0,
    "handle_message": 0
}

# Increment command usage each time a command is called
def increment_usage(command_name):
    if command_name in command_usage:
        command_usage[command_name] += 1

# Function to load watchlist for a specific user
def load_user_watchlist(user_id):
    user_file = f"{WATCHLIST_FOLDER}{user_id}.txt"
    try:
        with open(user_file, 'r') as f:
            return f.read().splitlines()
    except FileNotFoundError:
        return []

def save_user_watchlist(user_id, movies):
    user_file = f"{WATCHLIST_FOLDER}{user_id}.txt"
    try:
        with open(user_file, 'w') as f:
            for movie in movies:
                f.write(f"{movie}\n")
        print(f"Watchlist saved for user {user_id}.")  # Debugging line
    except Exception as e:
        print(f"Error saving watchlist for user {user_id}: {e}")

# Add movie to individual user's watchlist
def add_to_watchlist(user_id, movie_name):
    movies = load_user_watchlist(user_id)
    if len(movies) < 20:
        movies.append(movie_name)
        save_user_watchlist(user_id, movies)
        return True
    return False

# Command to add movie to watchlist
@require_subscription
def add_to_watchlist_command(update: Update, context: CallbackContext):
    increment_usage("add_to_watchlist")
    user_id = update.effective_user.id
    movie_name = ' '.join(context.args)

    if movie_name:
        success = add_to_watchlist(user_id, movie_name)
        if success:
            update.message.reply_text(f"'{movie_name}' has been added to your watchlist.")
        else:
            update.message.reply_text("Your watchlist is full. Please remove a movie before adding more.")
    else:
        update.message.reply_text("Please specify a movie name after the command, e.g., /add_to_watchlist Inception")

# Command to show user's watchlist
@require_subscription
def show_watchlist_command(update: Update, context: CallbackContext):
    increment_usage("show_watchlist_command")
    user_id = update.effective_user.id
    movies = load_user_watchlist(user_id)

    if movies:
        update.message.reply_text("Your Watchlist:\n" + "\n".join(movies))
    else:
        update.message.reply_text("Your watchlist is empty.")

# Command to remove movie from watchlist
@require_subscription
def remove_from_watchlist_command(update: Update, context: CallbackContext):
    increment_usage("remove_from_watchlist_command")
    user_id = update.effective_user.id
    movie_name = ' '.join(context.args)
    movies = load_user_watchlist(user_id)
    if movie_name in movies:
        movies.remove(movie_name)
        save_user_watchlist(user_id, movies)
        update.message.reply_text(f"'{movie_name}' has been removed from your watchlist.")
    else:
        update.message.reply_text(f"'{movie_name}' is not in your watchlist.")

def admin_show_watchlist_command(update: Update, context: CallbackContext):
    admin_user_id = update.effective_user.id  # ID of the user who invoked the command
    user_id = context.args[0] if context.args else None  # The user ID passed as an argument
    # Define your admin IDs
    admin_ids = [1264390578]  # Replace with your admin Telegram user ID
    if admin_user_id not in admin_ids:
        update.message.reply_text("You do not have permission to view other users' watchlists.")
        return
    if user_id:
        movies = load_user_watchlist(user_id)
        if movies:
            update.message.reply_text(f"Watchlist for user {user_id}:\n" + "\n".join(movies))
        else:
            update.message.reply_text(f"User {user_id}'s watchlist is empty.")
    else:
        update.message.reply_text("Please specify a user ID after the command, e.g., /admin_show_watchlist 987654321")

def save_user_id(user_id):
    try:
        # Read the existing IDs from the file
        with open("user_ids.txt", "r") as file:
            existing_ids = file.read().splitlines()

        # Check if the user ID is already in the file
        if str(user_id) not in existing_ids:
            # Append the new ID if it's unique
            with open("user_ids.txt", "a") as file:
                file.write(f"{user_id}\n")
    except FileNotFoundError:
        # If the file doesn't exist, create it and add the user ID
        with open("user_ids.txt", "w") as file:
            file.write(f"{user_id}\n")

# Function to handle the /start command
@require_subscription
def start(update: Update, context: CallbackContext):
    global counter
    increment_usage("start")
    user_id = update.effective_user.id
    channel_username = '@StarkFlixx'  # Replace with your channel username

    # Increment the counter and add user ID to the set
    counter += 1
    user_ids.add(user_id)
    save_user_id(user_id)  # Save user ID to file
    username = update.effective_user.username
    first_name = update.effective_user.first_name
    last_name = update.effective_user.last_name if update.effective_user.last_name else "N/A"

    logger.info(f"Start command received from {first_name} (@{username}, ID: {user_id}). Total count: {counter}")

    # Customize the welcome message
    welcome_message = f"Welcome, {first_name}! I'm here to help you find and share movies.\nCheck out our song channel for more music updates!"

    # Inline keyboard with a button linking to @StarkFlixx
    keyboard = [
        [InlineKeyboardButton("Song Channel 🎶", url="https://t.me/StarkSongss")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Check if context.args has a video_id, otherwise show the welcome message
    if context.args and context.args[0].isdigit():
        video_id = context.args[0]
        try:
            # Send the movie message and save it
            message = context.bot.copy_message(
                chat_id=update.effective_chat.id,
                from_chat_id=CHANNEL_ID,
                message_id=int(video_id)
            )
            # Send the warning message and store it for later editing
            warning_message = update.message.reply_text(
                f"Here is the movie you requested.\n❗️ IMPORTANT ❗️\n"
                f"This Media Will Be Deleted In 2 minutes (Due To Copyright Issues).\n\n"
                f"📌 Please Forward This Media To Your 𝗣𝗲𝗿𝘀𝗼𝗻𝗮𝗹 𝗦𝗮𝘃𝗲𝗱 𝗠𝗲𝘀𝘀𝗮𝗴𝗲 And Start Downloading There.\n\n"
                f"🎶 Also, check out our 𝗦𝗼𝗻𝗴 channel for more music updates!❤",
                reply_markup=reply_markup
            )

            # Schedule the deletion of the movie message and editing of the warning message after 120 seconds
            context.job_queue.run_once(
                handle_message_lifecycle, 120, context=(update.effective_chat.id, message.message_id, warning_message.message_id), name=f"delete_{message.message_id}"
            )

            # Send details to the admin with the requested movie ID
            admin_message = (
                f"User @{username} (ID: {user_id}) requested movie with ID: {video_id}.\n"
                f"Generated link: https://t.me/starksventures_bot?start={video_id}\n"
                f"First Name: {first_name}\n"
                f"Last Name: {last_name}\n"
                f"Total Start Count: {counter}"
            )
            context.bot.send_message(chat_id=1264390578, text=admin_message)

        except Exception as e:
            update.message.reply_text("Something went wrong. Please try again later.")
            logger.error(f"Error while sending movie message: {e}")

    else:
        # Send the welcome message with the button
        update.message.reply_text(welcome_message, reply_markup=reply_markup)

        # Send details to the admin (without a specific movie ID since none was requested)
        admin_message = (
            f"User @{username} (ID: {user_id}) just used the /start command.\n"
            f"First Name: {first_name}\n"
            f"Last Name: {last_name}\n"
            f"Total Start Count: {counter}"
        )
        context.bot.send_message(chat_id=1264390578, text=admin_message)



# def handle_new_channel_post(update: Update, context: CallbackContext):
#     # Replace with your private channel's ID (use a negative ID, e.g., -100XXXXXXXXXX)
#     private_channel_id = -1002077386138  # Replace this with the actual channel ID

#     # Check if the post is from the specified private channel
#     if update.effective_chat.id == private_channel_id:
#         video_id = update.channel_post.message_id  # Get the message ID as the video
#         # Create the link with the secure token
#         generated_link = f"https://t.me/starksventures_bot?start={video_id}"

#         # Send the generated link to the admin (your Telegram ID)
#         context.bot.send_message(
#             chat_id=1264390578,  # Replace with your admin Telegram ID
#             text=f"New movie posted with ID {video_id}.\nGenerated link: {generated_link}"
#         )

#         logger.info(f"Generated link sent to admin: {generated_link}")

def handle_message_lifecycle(context: CallbackContext):
    job = context.job
    chat_id, message_id, warning_message_id = job.context
    logger.info(f"Job triggered: Deleting movie message {message_id} and editing warning message {warning_message_id}")

    # Delete the media message
    context.bot.delete_message(chat_id=chat_id, message_id=message_id)

    # Edit the warning message
    context.bot.edit_message_text(
        chat_id=chat_id,
        message_id=warning_message_id,
        text="Media deleted successfully✅"
    )



def greet_new_user(update: Update, context: CallbackContext):
    new_chat_members = update.message.new_chat_members

    for member in new_chat_members:
        # Create an inline keyboard with the "Request Movie" button
        keyboard = [[InlineKeyboardButton("Request Movie", url="https://t.me/starkxmoviess/526")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Send a welcome message with the button
        update.message.reply_text(
            f"Welcome, {member.first_name}! 🎉 Welcome to Stark's movie group! "
            "Let us know if you're looking for a movie!",
            reply_markup=reply_markup
        )




# Function to handle the /surprise command
@require_subscription
def surpriseme(update: Update, context: CallbackContext):
    increment_usage("surpriseme")
    user_id = update.effective_user.id
    current_time = datetime.now()

    # Check if user has used the /surprise command before
    if user_id not in user_command_usage:
        user_command_usage[user_id] = {'count': 0, 'reset_time': current_time + timedelta(days=1)}

    # Reset the command usage if a day has passed
    if current_time >= user_command_usage[user_id]['reset_time']:
        user_command_usage[user_id] = {'count': 0, 'reset_time': current_time + timedelta(days=1)}

    # Check if the user has exceeded the daily limit
    if user_command_usage[user_id]['count'] >= 5:
        update.message.reply_text("You have reached the daily limit for /surpriseme commands. Please try again tomorrow.")
        return

    try:
        # Increment the command usage count
        user_command_usage[user_id]['count'] += 1

        # Define the range of movie message IDs in your channel
        min_message_id = 461
        max_message_id = 644  # Adjust based on your actual range

        # Choose a random message ID within the specified range
        random_message_id = random.randint(min_message_id, max_message_id)

        # Forward the random movie message
        message = context.bot.copy_message(
            chat_id=update.effective_chat.id,
            from_chat_id=CHANNEL_ID,
            message_id=random_message_id
        )

        # Inline keyboard with a button linking to @StarkFlixx
        keyboard = [
            [InlineKeyboardButton("Song Channel 🎶", url="https://t.me/StarkSongss")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Send message with button to join @StarkFlixx and store it for later deletion
        warning_message = update.message.reply_text( "Here is a surprise movie for you!\n\nDidn't like this one? 🎥✨ Try /surpriseme again, and I'll find another movie for you! 🍿🎬🎶 \n\nCheck out our 𝗦𝗼𝗻𝗴 channel for more music updates", reply_markup=reply_markup )

        # Schedule the deletion of both the movie and warning messages after 60 seconds
        context.job_queue.run_once(
            handle_message_lifecycle, 60, context=(update.effective_chat.id, message.message_id, warning_message.message_id), name=str(message.message_id)
        )

    except Exception as e:
        update.message.reply_text("Couldn't fetch a surprise movie at the moment. Please send /surpriseMe command again.")
        logger.error(f"Error while sending a surprise movie: {e}")


# Function to handle the /contact_admin command
def contact_owner(update: Update, context: CallbackContext):
    increment_usage("contact_owner")
    keyboard = [
        [InlineKeyboardButton("Contact Owner", url="https://t.me/ContackStarkOwner_bot")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("You can contact the owner:", reply_markup=reply_markup)


def escape_markdown_v2(text: str) -> str:
    """Escape special characters for MarkdownV2."""
    # List of special characters that need to be escaped
    special_chars = r'[_*{}\[\]()#+-.!`]'
    # Use a regular expression to escape the characters
    return re.sub(r'([_*{}\[\]()#+-.!`])', r'\\\1', text)


def stats(update: Update, context: CallbackContext):
    # Check if the user is the admin
    user_id = update.effective_user.id
    if user_id == 1264390578:  # Admin's Telegram ID
        unique_users = len(user_ids)
        last_used = datetime.now(ist_timezone).strftime('%Y-%m-%d %H:%M:%S')

        # Prepare the stats message
        stats_message = (
            f"Welcome! Looks like you are an authorized member!\n\n"
            f"📊 *Bot Statistics*\n\n"
            f"👥 *Total Unique Users*: {unique_users}\n"
            f"🔄 *Total /start Count*: {counter}\n"
            f"🕒 *Last Used*: {last_used}\n\n"
            f"🔹 *Per-Command Usage Stats*\n"
        )

        # Append each command’s usage to the stats message
        for command, count in command_usage.items():
            stats_message += f"/{command}: {count} uses\n"

        # Escape special characters in the message
        stats_message = escape_markdown_v2(stats_message)

        # Send stats to admin
        try:
            context.bot.send_message(
                chat_id=user_id,
                text=stats_message,
                parse_mode="MarkdownV2"  # Use MarkdownV2 for better handling
            )
        except Exception as e:
            update.message.reply_text(f"An error occurred while sending stats: {e}")
    else:
        # Inform other users that this command is only for the admin
        update.message.reply_text("❌ Sorry, this command is restricted to the bot administrator.")


@require_subscription
def request(update: Update, context: CallbackContext):
    increment_usage("request")
    req_message = "You can request your movie here:"

    # Create an inline keyboard with a button
    keyboard = [
        [InlineKeyboardButton("Request Movie 🎬", url="https://t.me/starkxmoviess/526")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Send the message with the button
    update.message.reply_text(req_message, reply_markup=reply_markup)

# Function to handle general messages
# Function to handle the /feedback command
def feedback(update: Update, context: CallbackContext):
    increment_usage("feedback")
    update.message.reply_text(
        "Please share your feedback or suggestions below. Type 'cancel' to stop."
    )
    # Set the state to wait for feedback
    context.user_data['waiting_for_feedback'] = True




def is_admin(update: Update, context: CallbackContext) -> bool:
    # Get the chat and user ID
    chat = update.message.chat
    user_id = update.effective_user.id

    # If it's a private chat, there are no admins, so return False
    if chat.type == 'private':
        return False

    # Otherwise, get the list of administrators in the group chat
    admins = context.bot.get_chat_administrators(chat.id)

    # Check if the user's ID is in the list of admin IDs
    return any(admin.user.id == user_id for admin in admins)



# Function to handle messages
MOVIE_KEYWORDS = [
    '720', '1080', 'movie', 'mov', 'film', 'filim', 'show', 'series', 'web', 'hd', 'quality', 'upload','marvel',
    'part', 'file', 'bluray', 'camrip', 'dvd', 'link', 'send', 'share', 'release', 'adult', 'ep', 'available',
    'please', 'hindi', 'eng', 'english', 'tamil', 'telugu', 'kannada', 'marathi', '18+', 'ullu','the','hotstar'
    'dubbed', 'hin', 'malayalam', 'bengali', 'punjabi', 'drama', 'season', 'anime', 'comedy', 'horror',
    'action', 'romance', 'thriller', 'sci-fi', 'netflix', 'amazon', 'disney', 'hulu', '2023', '2022', '20', '19'
]
movie_pattern = re.compile(r'\b(?:' + '|'.join(MOVIE_KEYWORDS) + r')\b', re.IGNORECASE)

# Function to handle messages
def handle_message(update: Update, context: CallbackContext):
    # Skip replying if the message is from an anonymous admin
    if update.message.sender_chat:
        return

    # Ignore messages from a specific user (additional admin check function)
    if is_admin(update, context):
        return

    increment_usage("handle_message")

    # Feedback handling
    if context.user_data.get('waiting_for_feedback'):
        feedback_text = update.message.text
        if feedback_text.lower() == 'cancel':
            update.message.reply_text("Feedback cancelled.")
            context.user_data['waiting_for_feedback'] = False
            return

        user_id = update.effective_user.id
        admin_feedback_message = (
            f"User @{update.effective_user.username} (ID: {user_id}) "
            f"sent feedback: {feedback_text}"
        )
        context.bot.send_message(chat_id=1264390578, text=admin_feedback_message)

        # Thank user
        update.message.reply_text("Thank you for your feedback! 😊")
        update.message.reply_text("We may reply to your feedback shortly!")
        context.user_data['waiting_for_feedback'] = False
        return

    # Normal message handling
    user_message = update.message.text.lower()

    # Check if the message contains keywords or a year format
    if movie_pattern.search(user_message) or re.search(r'\b(19|20)\d{2}\b', user_message):
        update.message.reply_text("Got it!🎬 We’ll upload it shortly! Please wait.")


    # Additional responses based on common phrases
    elif any(ok in user_message for ok in ['ok', 'okay', 'theek', 'acha']):
        update.message.reply_text("Thank you for understanding!")
    elif any(tq in user_message for tq in ['tq', 'thank', 'thank you', 'thankyou', 'tysm']):
        update.message.reply_text("You're welcome!")
    elif any(yes in user_message for yes in ['yes', 'no', 'nahi']):
        update.message.reply_text("Ok!")
    elif 'bye' in user_message:
        update.message.reply_text("Goodbye! It was nice chatting with you.")
    else:
        # Prompt user to include release year if no keywords or year format found
        update.message.reply_text("Please mention the release year as well.")


def reply_feedback(update: Update, context: CallbackContext):
    # Ensure there are enough arguments
    if len(context.args) < 2:
        update.message.reply_text("Usage: /reply <user_id> <your_message>")
        return

    user_id = context.args[0]  # User ID to reply to
    reply_message = ' '.join(context.args[1:])  # The reply message

    try:
        context.bot.send_message(chat_id=user_id, text=reply_message)
        update.message.reply_text(f"Replied to user {user_id}.")
    except Exception as e:
        update.message.reply_text("Failed to send reply.")
        logger.error(f"Error while sending reply: {e}")
# Import necessary modules at the top of the script


# Function to broadcast a message to all saved users
def broadcast(update: Update, context: CallbackContext):
    # Ensure the command is only accessible to the admin (replace '1264390578' with your actual Telegram ID)
    if update.effective_user.id != 1264390578:
        update.message.reply_text("You are not authorized to use this command.")
        return

    # Check if there's a message to broadcast
    if not context.args:
        update.message.reply_text("Please provide a message to broadcast. Usage: /broadcast <message>")
        return

    # Construct the broadcast message from the command arguments
    message = ' '.join(context.args)

    # Load user IDs from the file
    if os.path.exists('user_ids.txt'):
        with open('user_ids.txt', 'r') as file:
            user_ids = {int(line.strip()) for line in file}

        # Send the message to each user
        for user_id in user_ids:
            try:
                context.bot.send_message(chat_id=user_id, text=message)
            except Exception as e:
                logger.error(f"Failed to send message to {user_id}: {e}")

        update.message.reply_text("Broadcast message sent to all users.")
    else:
        update.message.reply_text("No users found to broadcast the message.")



# Main function to set up the bot
def main():

    updater = Updater(token=BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("contact_owner", contact_owner))
    dp.add_handler(CommandHandler("request", request))
    dp.add_handler(CommandHandler("surpriseme", surpriseme))  # Add the new /surpriseme handler
    dp.add_handler(CommandHandler("stats", stats))
    dp.add_handler(CommandHandler('feedback', feedback))
    dp.add_handler(CommandHandler('reply7398', reply_feedback))
    dp.add_handler(CommandHandler("broadcast", broadcast))
    dp.add_handler(CommandHandler("add_to_watchlist", add_to_watchlist_command))
    dp.add_handler(CommandHandler("remove_from_watchlist", remove_from_watchlist_command))
    dp.add_handler(CommandHandler("show_watchlist", show_watchlist_command))
    dp.add_handler(CommandHandler("admin_show_watchlist", admin_show_watchlist_command))
    dp.add_handler(MessageHandler(Filters.status_update.new_chat_members, greet_new_user))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    # Register the handler in your bot's dispatcher
    # dp.add_handler(MessageHandler(Filters.chat(-1002077386138) & Filters.update.channel_post, handle_new_channel_post))
    # Ensure job queue is initialized
    dp.job_queue = updater.job_queue

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    # Ensure the watchlist folder exists
    if not os.path.exists(WATCHLIST_FOLDER):
        os.makedirs(WATCHLIST_FOLDER)
    main()


