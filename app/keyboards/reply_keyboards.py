from telegram import ReplyKeyboardMarkup, KeyboardButton

def main_menu_keyboard():
    """Keyboard menu utama yang persistent"""
    keyboard = [
        [KeyboardButton("📋 Menu")]
    ]
    return ReplyKeyboardMarkup(
        keyboard, 
        resize_keyboard=True, 
        is_persistent=True
    )
