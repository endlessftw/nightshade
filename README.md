# Discord Bot

A feature-rich Discord bot with moderation, games, utilities, and more!

## Features

### 🎮 Games & Fun
- `/ship` - Ship calculator with custom generated images
- `/tictactoe` - Play Tic Tac Toe
- `/connectfour` - Play Connect Four
- `/hangman` - Word guessing game
- `/rockpaperscissors` - Rock Paper Scissors
- `/eightball` - Magic 8-Ball predictions
- `/coin` - Flip a coin

### 👮 Moderation
- `/ban` - Ban users from the server
- `/kick` - Kick users from the server
- `/timeout` - Timeout users temporarily
- `/untimeout` - Remove timeout from users
- `/warn` - Warn users for rule violations
- `/unwarn` - Remove specific warnings
- `/warnings` - View user warnings
- `/clearwarnings` - Clear all warnings for a user

### 📊 Utility
- `/userprofile` - View detailed user information
- `/timechannel` - Display world time clocks (auto-updating)
- `/ping` - Check bot latency
- `/help` - View all commands

### 🎉 Server Management
- `/giveaway` - Start giveaways with automatic winner selection
- `!reroll` - Reroll giveaway winners
- Welcomer system
- Snipe deleted messages

### 🎨 Profile & Stats
- `/myprofile` - View your profile
- `/aura` - Check your aura
- `/shadow` - Shadow effect
- `/quote` - Get random quotes

### 🎵 Voice (Coming Soon)
- Music playback features

## Installation

1. Clone this repository:
```bash
git clone https://github.com/endlessftw/nightshade.git
cd nightshade
```

2. Install required dependencies:
```bash
pip install -r requirements.txt
```

3. Set up data files from templates:
```bash
python setup.py
```

4. Set your bot token as an environment variable:

**Windows (PowerShell):**
```powershell
$env:DISCORD_TOKEN="YOUR_BOT_TOKEN_HERE"
```

**Linux/Mac:**
```bash
export DISCORD_TOKEN="YOUR_BOT_TOKEN_HERE"
```

**Or create a `.env` file:**
```
DISCORD_TOKEN=YOUR_BOT_TOKEN_HERE
```

5. Run the bot:
```bash
python main.py
```

## Deploying to Render or DigitalOcean

### Option 1: Render (Recommended - Easier Setup)

1. Fork/clone this repository
2. Create a new Web Service on [Render](https://render.com)
3. Connect your GitHub repository
4. Set the following:
   - **Build Command:** `pip install -r requirements.txt && python setup.py`
   - **Start Command:** `python main.py`
5. Add a **PostgreSQL database**:
   - Create a new PostgreSQL database on Render
   - Copy the **Internal Database URL**
6. Add environment variables:
   - Key: `DISCORD_TOKEN` / Value: Your Discord bot token
   - Key: `DATABASE_URL` / Value: Your PostgreSQL database URL

**Note:** Render's Linux servers include DejaVu fonts by default, which the bot will automatically use for image generation commands (`/aura`, `/ship`). No additional font installation needed!

### Option 2: DigitalOcean App Platform + Supabase (FREE!)

1. **Set up FREE database on Supabase:**
   - Go to [supabase.com](https://supabase.com) and create a free account
   - Create a new project (takes 2-3 minutes)
   - Get your database URL from Settings → Database → Connection string
   - See `DIGITALOCEAN_SETUP.md` for detailed steps

2. **Deploy on DigitalOcean:**
   - Create a new App on [DigitalOcean](https://www.digitalocean.com/products/app-platform)
   - Connect your GitHub repository
   - Set environment variables:
     - `DISCORD_TOKEN` - Your Discord bot token
     - `DATABASE_URL` - Your Supabase PostgreSQL URL
   - Deploy!

**Note:** Voice features (`/play`) may not work on DigitalOcean due to UDP restrictions. Consider using Railway.app for voice support.

## Database Setup

This bot uses **PostgreSQL** for persistent data storage (user stats, warnings, configs).

### For Local Development:
The bot will automatically use SQLite (`bot_data.db`) if no PostgreSQL is configured. No setup needed!

### For Production (FREE with Supabase):
1. Create a **FREE** account on [Supabase](https://supabase.com)
2. Create a new project (takes 2-3 minutes)
3. Get your connection URL from Settings → Database
4. Set the `DATABASE_URL` environment variable on your hosting platform
5. The bot will automatically create tables on first run

**See `DIGITALOCEAN_SETUP.md` for step-by-step Supabase setup instructions!**

### Why Supabase?
- ✅ **FREE Forever** (500MB database - perfect for Discord bots!)
- ✅ **No Credit Card Required**
- ✅ **Easy Setup** (5 minutes)
- ✅ **View Your Data** in built-in dashboard
- ✅ **Automatic Backups**

### Migrating Existing Data:
If you have existing JSON files with data:
```bash
python migrate_to_database.py
```

This will transfer all data from:
- `userphone_stats.json` → Database
- `warnings.json` → Database  
- Config files → Database

## Requirements

- Python 3.10 or higher
- discord.py 2.3.0+
- Pillow (PIL)
- aiohttp
- pytz

See `requirements.txt` for full list of dependencies.

## Configuration

### Bot Token
Add your bot token to `config.json`:
```json
{
    "token": "YOUR_BOT_TOKEN_HERE"
}
```

### Permissions Required
The bot needs the following permissions:
- Read Messages/View Channels
- Send Messages
- Embed Links
- Attach Files
- Read Message History
- Add Reactions
- Manage Messages
- Kick Members
- Ban Members
- Moderate Members
- Manage Channels (for time channels)

## Commands

Use `/help` in Discord to see all available commands and their descriptions.

## Support

For issues, questions, or suggestions, please open an issue on GitHub.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Credits

Created by [Your Name]

## Note

Remember to keep your bot token secret! Never share it or commit it to GitHub.
