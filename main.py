import os
import io
import requests
from PIL import Image
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# Get the bot token from environment variables
TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')

# Dictionary to store user states
user_states = {}

# ============================
# COMMAND HANDLERS
# ============================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a welcome message with inline keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("🖼️ Image Converter", callback_data="converter"),
            InlineKeyboardButton("🎨 Image Generator", callback_data="generator"),
        ],
        [
            InlineKeyboardButton("🔗 URL Shortener", callback_data="shortener"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🏴‍☠️ **Welcome to PixelPirate Bot!**\n\n"
        "I can help you with:\n"
        "• 🖼️ Convert images to different formats\n"
        "• 🎨 Generate images from text prompts\n"
        "• 🔗 Shorten long URLs\n\n"
        "Choose an option below or use commands:\n"
        "/convert - Convert an image\n"
        "/generate - Generate an image\n"
        "/shorten - Shorten a URL\n"
        "/help - Show this message again",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a help message."""
    await start(update, context)

async def convert_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /convert command."""
    user_id = update.effective_user.id
    user_states[user_id] = {"mode": "converter"}
    
    await update.message.reply_text(
        "🖼️ **Image Converter**\n\n"
        "Please send me an image you want to convert.\n"
        "After that, I'll ask you for the output format.\n\n"
        "Supported formats: JPG, PNG, WEBP, BMP, GIF",
        parse_mode="Markdown"
    )

async def generate_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /generate command."""
    user_id = update.effective_user.id
    user_states[user_id] = {"mode": "generator"}
    
    await update.message.reply_text(
        "🎨 **Image Generator**\n\n"
        "Please send me a text description of the image you want to generate.\n\n"
        "Example: 'A sunset over a mountain lake with pine trees'\n\n"
        "⚠️ Note: This uses a free AI API and may take a few seconds.",
        parse_mode="Markdown"
    )

async def shorten_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /shorten command."""
    user_id = update.effective_user.id
    user_states[user_id] = {"mode": "shortener"}
    
    await update.message.reply_text(
        "🔗 **URL Shortener**\n\n"
        "Please send me the URL you want to shorten.\n\n"
        "Example: https://example.com/very/long/url/that/needs/shortening",
        parse_mode="Markdown"
    )

# ============================
# BUTTON CALLBACK HANDLER
# ============================

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline keyboard button presses."""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    action = query.data
    
    if action == "converter":
        user_states[user_id] = {"mode": "converter"}
        await query.edit_message_text(
            "🖼️ **Image Converter**\n\n"
            "Please send me an image you want to convert.\n"
            "After that, I'll ask you for the output format.\n\n"
            "Supported formats: JPG, PNG, WEBP, BMP, GIF",
            parse_mode="Markdown"
        )
    elif action == "generator":
        user_states[user_id] = {"mode": "generator"}
        await query.edit_message_text(
            "🎨 **Image Generator**\n\n"
            "Please send me a text description of the image you want to generate.\n\n"
            "Example: 'A sunset over a mountain lake with pine trees'\n\n"
            "⚠️ Note: This uses a free AI API and may take a few seconds.",
            parse_mode="Markdown"
        )
    elif action == "shortener":
        user_states[user_id] = {"mode": "shortener"}
        await query.edit_message_text(
            "🔗 **URL Shortener**\n\n"
            "Please send me the URL you want to shorten.\n\n"
            "Example: https://example.com/very/long/url/that/needs/shortening",
            parse_mode="Markdown"
        )

# ============================
# MESSAGE HANDLERS
# ============================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle user messages based on their current mode."""
    user_id = update.effective_user.id
    
    # If user hasn't set a mode, prompt them to use /start
    if user_id not in user_states:
        await update.message.reply_text(
            "Please use /start to see available options first! 🏴‍☠️"
        )
        return
    
    mode = user_states[user_id].get("mode")
    
    if mode == "converter":
        await handle_converter(update, context)
    elif mode == "generator":
        await handle_generator(update, context)
    elif mode == "shortener":
        await handle_shortener(update, context)
    else:
        await update.message.reply_text(
            "I'm not sure what you want to do. Please use /start to begin."
        )

# ============================
# IMAGE CONVERTER
# ============================

async def handle_converter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle image conversion."""
    user_id = update.effective_user.id
    
    # Check if user sent a photo
    if update.message.photo:
        # Get the largest photo
        photo = update.message.photo[-1]
        file = await context.bot.get_file(photo.file_id)
        
        # Download the image
        image_bytes = await file.download_as_bytearray()
        
        # Store the image in context for later use
        context.user_data['image_data'] = image_bytes
        context.user_data['image_format'] = 'jpg'  # Default input format
        
        # Ask for output format
        keyboard = [
            [
                InlineKeyboardButton("JPG", callback_data="fmt_jpg"),
                InlineKeyboardButton("PNG", callback_data="fmt_png"),
                InlineKeyboardButton("WEBP", callback_data="fmt_webp"),
            ],
            [
                InlineKeyboardButton("BMP", callback_data="fmt_bmp"),
                InlineKeyboardButton("GIF", callback_data="fmt_gif"),
            ],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "📸 Image received!\n\n"
            "Select the output format:",
            reply_markup=reply_markup
        )
    
    elif update.message.document:
        # Handle document uploads
        document = update.message.document
        if document.mime_type and document.mime_type.startswith('image/'):
            file = await context.bot.get_file(document.file_id)
            image_bytes = await file.download_as_bytearray()
            
            context.user_data['image_data'] = image_bytes
            context.user_data['image_format'] = document.mime_type.split('/')[-1]
            
            keyboard = [
                [
                    InlineKeyboardButton("JPG", callback_data="fmt_jpg"),
                    InlineKeyboardButton("PNG", callback_data="fmt_png"),
                    InlineKeyboardButton("WEBP", callback_data="fmt_webp"),
                ],
                [
                    InlineKeyboardButton("BMP", callback_data="fmt_bmp"),
                    InlineKeyboardButton("GIF", callback_data="fmt_gif"),
                ],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                "📄 Image received!\n\n"
                "Select the output format:",
                reply_markup=reply_markup
            )
        else:
            await update.message.reply_text(
                "❌ Please send a valid image file (JPG, PNG, etc.)"
            )
    else:
        await update.message.reply_text(
            "❌ Please send an image (as a photo or document)."
        )

async def handle_format_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle format selection for image conversion."""
    query = update.callback_query
    await query.answer()
    
    # Extract format from callback data
    output_format = query.data.replace('fmt_', '')
    
    # Get the stored image
    image_data = context.user_data.get('image_data')
    if not image_data:
        await query.edit_message_text(
            "❌ Image not found. Please start over with /convert."
        )
        return
    
    try:
        # Convert the image
        input_image = Image.open(io.BytesIO(image_data))
        
        # Handle RGBA to RGB for JPG
        if output_format == 'jpg' and input_image.mode == 'RGBA':
            background = Image.new('RGB', input_image.size, (255, 255, 255))
            background.paste(input_image, mask=input_image.split()[3] if input_image.mode == 'RGBA' else None)
            input_image = background
        
        # Save to bytes
        output = io.BytesIO()
        input_image.save(output, format=output_format.upper())
        output.seek(0)
        
        # Send the converted image
        await query.edit_message_text(
            f"✅ Conversion complete!\n\n"
            f"📦 Original: {context.user_data.get('image_format', 'unknown')}\n"
            f"📦 Converted to: {output_format.upper()}\n\n"
            f"Sending your image now..."
        )
        
        await context.bot.send_document(
            chat_id=update.effective_chat.id,
            document=output,
            filename=f"converted.{output_format}",
            caption=f"🏴‍☠️ Converted to {output_format.upper()}"
        )
        
        # Clean up
        del context.user_data['image_data']
        del context.user_data['image_format']
        
    except Exception as e:
        await query.edit_message_text(
            f"❌ Error converting image: {str(e)}\n\n"
            "Please try again with /convert"
        )

# ============================
# IMAGE GENERATOR (using free Hugging Face API)
# ============================

async def handle_generator(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle image generation from text."""
    prompt = update.message.text
    
    # Check if the prompt is valid
    if len(prompt.strip()) < 3:
        await update.message.reply_text(
            "❌ Please provide a longer description (at least 3 characters)."
        )
        return
    
    await update.message.reply_text(
        f"🎨 Generating image for: *{prompt[:50]}...*\n\n"
        "⏳ This may take 10-30 seconds...",
        parse_mode="Markdown"
    )
    
    try:
        # Using Hugging Face API (free)
        API_URL = "https://api-inference.huggingface.co/models/runwayml/stable-diffusion-v1-5"
        headers = {"Authorization": f"Bearer {os.environ.get('HUGGINGFACE_API_KEY', '')}"}
        
        # If no API key, use a fallback or inform user
        if not headers["Authorization"] or headers["Authorization"] == "Bearer ":
            await update.message.reply_text(
                "⚠️ Image generation is currently unavailable.\n\n"
                "Please set up a Hugging Face API key or try again later.\n"
                "You can get a free key at: https://huggingface.co/settings/tokens"
            )
            return
        
        response = requests.post(
            API_URL,
            headers=headers,
            json={"inputs": prompt},
            timeout=60
        )
        
        if response.status_code == 200:
            image_data = response.content
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=image_data,
                caption=f"🎨 Generated from: {prompt[:100]}\n\n🏴‍☠️ PixelPirate Bot"
            )
        else:
            # Fallback to a simpler model or error message
            await update.message.reply_text(
                f"⚠️ The AI model is currently busy or unavailable.\n"
                f"Status: {response.status_code}\n\n"
                "Please try again in a few moments, or use a more specific prompt."
            )
            
    except requests.exceptions.Timeout:
        await update.message.reply_text(
            "⏰ The AI model took too long to respond.\n\n"
            "Please try again with a simpler prompt."
        )
    except Exception as e:
        await update.message.reply_text(
            f"❌ Error generating image: {str(e)[:200]}\n\n"
            "Please try again with /generate"
        )

# ============================
# URL SHORTENER (using free is.gd API)
# ============================

async def handle_shortener(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle URL shortening."""
    url = update.message.text.strip()
    
    # Validate URL
    if not url.startswith(('http://', 'https://')):
        await update.message.reply_text(
            "❌ Please send a valid URL starting with http:// or https://"
        )
        return
    
    try:
        # Using is.gd API (free, no API key needed)
        import urllib.parse
        encoded_url = urllib.parse.quote(url, safe='')
        api_url = f"https://is.gd/create.php?format=json&url={encoded_url}"
        
        response = requests.get(api_url, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            if 'shorturl' in data:
                short_url = data['shorturl']
                
                # Generate a QR code using qrserver.com (free)
                qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data={short_url}"
                
                await update.message.reply_text(
                    f"🔗 **URL Shortened!**\n\n"
                    f"📎 **Original:** {url[:50]}...\n"
                    f"✂️ **Shortened:** {short_url}\n\n"
                    f"📱 Here's a QR code for it:",
                    parse_mode="Markdown"
                )
                
                # Send QR code
                await context.bot.send_photo(
                    chat_id=update.effective_chat.id,
                    photo=qr_url,
                    caption=f"🏴‍☠️ Scan this QR code to visit the shortened URL"
                )
            else:
                await update.message.reply_text(
                    "❌ Could not shorten the URL. Please try again."
                )
        else:
            await update.message.reply_text(
                "❌ Error connecting to URL shortener service. Please try again later."
            )
            
    except requests.exceptions.Timeout:
        await update.message.reply_text(
            "⏰ The URL shortener service timed out. Please try again."
        )
    except Exception as e:
        await update.message.reply_text(
            f"❌ Error shortening URL: {str(e)[:200]}\n\n"
            "Please try again with /shorten"
        )

# ============================
# MAIN APPLICATION
# ============================

if __name__ == '__main__':
    # Create the Application
    application = ApplicationBuilder().token(TOKEN).build()
    
    # Add command handlers
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(CommandHandler('convert', convert_command))
    application.add_handler(CommandHandler('generate', generate_command))
    application.add_handler(CommandHandler('shorten', shorten_command))
    
    # Add callback query handlers (for buttons)
    application.add_handler(CallbackQueryHandler(button_callback, pattern='^(converter|generator|shortener)$'))
    application.add_handler(CallbackQueryHandler(handle_format_selection, pattern='^fmt_'))
    
    # Add message handler for all other messages
    application.add_handler(MessageHandler(filters.ALL, handle_message))
    
    # Start the bot
    print("🏴‍☠️ PixelPirate Bot is starting...")
    application.run_polling()
