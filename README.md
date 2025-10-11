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
git clone https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
cd YOUR_REPO_NAME
```

2. Install required dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `config.json` file in the root directory:
```json
{
    "token": "YOUR_BOT_TOKEN_HERE"
}
```

4. Run the bot:
```bash
python main.py
```

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
