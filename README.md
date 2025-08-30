# MaxTelegramBot

**Telegram bot for forwarding messages from MAX messenger to Telegram**

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://python.org)
[![Aiogram](https://img.shields.io/badge/Aiogram-3.x-green.svg)](https://docs.aiogram.dev/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE.txt)

## Quick Start

### Prerequisites

- Python 3.8 or higher
- Telegram Bot Token from [@BotFather](https://t.me/BotFather)
- MAX session token from browser

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/nixaty/MaxTelegramBot.git
   cd MaxTelegramBot
   ```

2. **Create virtual environment**
   ```bash
   python -m venv .venv
   ```

3. **Activate virtual environment**
   - Windows:
     ```bash
     .venv\Scripts\activate
     ```
   - Linux/MacOS:
     ```bash
     source .venv/bin/activate
     ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Configure environment variables**
   Create a `.env` file using the sample in the root directory:
   ```env
   # Telegram Configuration
   TG_BOT_TOKEN=123456789:qwertyuiopASDFGHJKLZXCVBNM
   TG_CHAT_ID=-100123456789

   # MAX API Configuration
   MAX_PAYLOAD_TOKEN=...
   MAX_DEVICE_ID=12345678-abcd-efgh-0673-987a654a3210

   # Settings
   ALLOWED_MAX_CHATS="-62349573987, -5723478753, -1234567890"
   ```

6. **Start bot**
   ```bash
   python main.py
   ```

### Configuration

#### 🔧 Environment Variables

| Variable | Description | How to Get |
|----------|-------------|------------|
| `TG_BOT_TOKEN` | Your Telegram bot token | From [@BotFather](https://t.me/BotFather) |
| `TG_CHAT_ID` | Target Telegram chat ID | You can get it in the group description by enabling the "Show Peer IDs in profile" setting, which is located in Settings > Advanced > Experimental settings. **Note: You need add "-100" at the beginning of the obtained chat ID.** |
| `MAX_PAYLOAD_TOKEN` | MAX authentication token | See "MAX Authentication" section below |
| `MAX_DEVICE_ID` | MAX device identifier | See "MAX Authentication" section below |
| `ALLOWED_MAX_CHATS` | Comma-separated list of MAX chat IDs to forward | Get from url when chat opened |

## 🔐 MAX Authentication

### Extracting session data

1. **Open and https://web.max.ru and sign in**
2. **Open google Developer Tools** by pressing F12 button
3. **Open `Application` tab**
4. **Find section `Local Storage > https://web.max.ru`**, open and look fields :

   - `__oneme_auth`: In this field, after the solve "token", there is a token that you need insert into **MAX_PAYLOAD_TOKEN**
   - `__oneme_device_id`: Unique device identifier that you need insert into **MAX_DEVICE_ID**


---

**Note**: This project is not officially affiliated with MAX messenger or Telegram. Use at your own responsibility.
