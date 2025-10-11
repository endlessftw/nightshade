import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional
import random


# Common words for hangman
WORD_LIST = [
    "PYTHON", "DISCORD", "GAMING", "PUZZLE", "COMPUTER", "KEYBOARD", "INTERNET",
    "CHALLENGE", "ADVENTURE", "TREASURE", "MYSTERY", "FANTASY", "DRAGON", "WIZARD",
    "CASTLE", "KNIGHT", "WARRIOR", "BATTLE", "VICTORY", "CHAMPION", "LEGEND",
    "MONSTER", "POTION", "MAGIC", "SPELL", "QUEST", "JOURNEY", "EXPLORE",
    "GALAXY", "PLANET", "ROCKET", "ASTRONAUT", "UNIVERSE", "SCIENCE", "TECHNOLOGY",
    "ROBOT", "ANDROID", "CYBORG", "FUTURE", "VIRTUAL", "DIGITAL", "NETWORK",
    "STREAM", "CONTENT", "CHANNEL", "AUDIENCE", "CREATIVE", "ARTIST", "MUSIC",
    "GUITAR", "PIANO", "CONCERT", "RHYTHM", "MELODY", "HARMONY", "SYMPHONY"
]

# Letter to emoji mapping (using regional indicators)
LETTER_EMOJI = {
    'A': '🇦', 'B': '🇧', 'C': '🇨', 'D': '🇩', 'E': '🇪', 'F': '🇫', 'G': '🇬',
    'H': '🇭', 'I': '🇮', 'J': '🇯', 'K': '🇰', 'L': '🇱', 'M': '🇲', 'N': '🇳',
    'O': '🇴', 'P': '🇵', 'Q': '🇶', 'R': '🇷', 'S': '🇸', 'T': '🇹', 'U': '🇺',
    'V': '🇻', 'W': '🇼', 'X': '🇽', 'Y': '🇾', 'Z': '🇿'
}

BLANK_EMOJI = '⬜'


class LetterButton(discord.ui.Button):
    def __init__(self, letter: str, hangman_view: 'HangmanView'):
        self.letter = letter
        self.hangman_view = hangman_view
        
        # Check if already guessed
        disabled = letter in hangman_view.guessed_letters
        style = discord.ButtonStyle.secondary if not disabled else discord.ButtonStyle.success
        
        super().__init__(
            label=letter,
            style=style,
            disabled=disabled,
            custom_id=f"hangman_{letter}"
        )
    
    async def callback(self, interaction: discord.Interaction):
        await self.hangman_view.process_guess(interaction, self.letter)


class LastLettersSelect(discord.ui.Select):
    def __init__(self, hangman_view: 'HangmanView'):
        self.hangman_view = hangman_view
        
        # Create options for letters U-Z (last 6 letters)
        options = []
        for letter in 'UVWXYZ':
            options.append(
                discord.SelectOption(
                    label=letter,
                    value=letter,
                    emoji=LETTER_EMOJI[letter],
                    description=f"Guess the letter {letter}",
                    default=False
                )
            )
        
        super().__init__(
            placeholder="Select U-Z...",
            min_values=1,
            max_values=1,
            options=options,
            row=4  # Last row
        )
    
    async def callback(self, interaction: discord.Interaction):
        await self.hangman_view.process_guess(interaction, self.values[0])


class HangmanView(discord.ui.View):
    def __init__(self, player1: discord.User, player2: Optional[discord.User] = None, word: str = None):
        super().__init__(timeout=600)  # 10 minute timeout
        self.player1 = player1
        self.player2 = player2
        self.is_multiplayer = player2 is not None
        
        # Game state
        self.word = word or random.choice(WORD_LIST)
        self.word = self.word.upper()
        self.guessed_letters = set()
        self.wrong_guesses = 0
        self.max_tries = 10
        self.game_over = False
        self.winner = None
        
        # Turn management for multiplayer
        self.current_player = player1  # Player 1 starts
        
        # Track correct guesses per player in multiplayer
        self.player1_correct = 0
        self.player2_correct = 0
        
        # Message reference
        self.game_message = None
        
        # Add letter buttons
        self.update_buttons()
    
    def update_buttons(self):
        # Remove old buttons and selects if they exist
        for item in self.children[:]:
            if isinstance(item, (LetterButton, LastLettersSelect)):
                self.remove_item(item)
        
        # Add new buttons with updated state
        if not self.game_over:
            # Discord allows max 5 rows with 5 buttons each = 25 total buttons
            # We have 26 letters, so we'll use:
            # - Buttons for A-T (20 letters, 4 rows of 5 buttons each)
            # - Select menu for U-Z (6 letters in row 4)
            letters = 'ABCDEFGHIJKLMNOPQRST'  # First 20 letters (A-T)
            for i, letter in enumerate(letters):
                row = i // 5  # 5 buttons per row (rows 0-3)
                button = LetterButton(letter, self)
                button.row = row
                self.add_item(button)
            
            # Add select menu for U-Z
            self.add_item(LastLettersSelect(self))
    
    def get_display_word(self) -> str:
        """Return the word with blanks for unguessed letters as emojis."""
        display = []
        for letter in self.word:
            if letter in self.guessed_letters:
                display.append(LETTER_EMOJI[letter])
            else:
                display.append(BLANK_EMOJI)
        return ' '.join(display)
    
    def check_win(self) -> bool:
        """Check if all letters have been guessed."""
        return all(letter in self.guessed_letters for letter in self.word)
    
    def get_hangman_drawing(self) -> str:
        """Return ASCII art for hangman based on wrong guesses."""
        stages = [
            # Stage 0
            """
            ┌─────┐
            │     
            │     
            │     
            │     
            └─────
            """,
            # Stage 1
            """
            ┌─────┐
            │     │
            │     
            │     
            │     
            └─────
            """,
            # Stage 2
            """
            ┌─────┐
            │     │
            │     😟
            │     
            │     
            └─────
            """,
            # Stage 3
            """
            ┌─────┐
            │     │
            │     😟
            │     │
            │     
            └─────
            """,
            # Stage 4
            """
            ┌─────┐
            │     │
            │     😟
            │    ╱│
            │     
            └─────
            """,
            # Stage 5
            """
            ┌─────┐
            │     │
            │     😟
            │    ╱│╲
            │     
            └─────
            """,
            # Stage 6
            """
            ┌─────┐
            │     │
            │     😟
            │    ╱│╲
            │    ╱
            └─────
            """,
            # Stage 7
            """
            ┌─────┐
            │     │
            │     😟
            │    ╱│╲
            │    ╱ ╲
            └─────
            """,
            # Stage 8
            """
            ┌─────┐
            │     │
            │     😵
            │    ╱│╲
            │    ╱ ╲
            └─────
            """,
            # Stage 9
            """
            ┌─────┐
            │     │
            │     💀
            │    ╱│╲
            │    ╱ ╲
            └─────
            """,
            # Stage 10 (Game Over)
            """
            ┌─────┐
            │     │
            │     ☠️
            │    ╱│╲
            │    ╱ ╲
            └─────
            """
        ]
        return f"```{stages[min(self.wrong_guesses, len(stages) - 1)]}```"
    
    async def process_guess(self, interaction: discord.Interaction, letter: str):
        # Check if it's the right player's turn
        if self.is_multiplayer:
            if interaction.user.id != self.current_player.id:
                await interaction.response.send_message(
                    f"<a:warning:1424944783587147868> It's **{self.current_player.display_name}**'s turn!",
                    ephemeral=True
                )
                return
        else:
            # In singleplayer, only the original player can guess
            if interaction.user.id != self.player1.id:
                await interaction.response.send_message(
                    "<a:warning:1424944783587147868> This is not your game!",
                    ephemeral=True
                )
                return
        
        # Check if game is already over
        if self.game_over:
            await interaction.response.send_message(
                "<a:warning:1424944783587147868> This game has already ended!",
                ephemeral=True
            )
            return
        
        # Check if letter was already guessed
        if letter in self.guessed_letters:
            await interaction.response.send_message(
                f"<a:warning:1424944783587147868> **{letter}** has already been guessed!",
                ephemeral=True
            )
            return
        
        # Process the guess
        self.guessed_letters.add(letter)
        
        correct_guess = letter in self.word
        
        if correct_guess:
            # Correct guess - don't switch turn in multiplayer
            # Track correct guesses per player in multiplayer
            if self.is_multiplayer:
                if self.current_player.id == self.player1.id:
                    self.player1_correct += self.word.count(letter)  # Count how many times letter appears
                else:
                    self.player2_correct += self.word.count(letter)
            await interaction.response.defer()
        else:
            # Wrong guess - increment counter and switch turn in multiplayer
            self.wrong_guesses += 1
            if self.is_multiplayer:
                # Switch turn
                self.current_player = self.player2 if self.current_player == self.player1 else self.player1
            await interaction.response.defer()
        
        # Check win/loss conditions
        if self.check_win():
            self.game_over = True
            if self.is_multiplayer:
                # In multiplayer, winner is determined by who got the most correct letters
                if self.player1_correct > self.player2_correct:
                    self.winner = self.player1
                elif self.player2_correct > self.player1_correct:
                    self.winner = self.player2
                else:
                    self.winner = None  # Tie - no winner
            else:
                self.winner = self.player1
        elif self.wrong_guesses >= self.max_tries:
            self.game_over = True
            # In multiplayer, determine winner based on who got more correct letters
            if self.is_multiplayer:
                if self.player1_correct > self.player2_correct:
                    self.winner = self.player1
                elif self.player2_correct > self.player1_correct:
                    self.winner = self.player2
                else:
                    self.winner = None  # Tie - no winner
            else:
                self.winner = None  # Singleplayer loss
        
        # Track wins if game is over and there's a winner
        if self.game_over and self.winner:
            try:
                bot = getattr(interaction.client, 'bot', None) or interaction.client
                wins = getattr(bot, 'user_wins_hangman', None)
                if wins is not None:
                    wins[self.winner.id] = wins.get(self.winner.id, 0) + 1
                    # Persist stats if available
                    save_fn = getattr(bot, 'save_stats', None)
                    if save_fn is not None:
                        try:
                            await save_fn()
                        except Exception:
                            pass
            except Exception:
                pass
        
        # Update the view
        await self.update_game_message(interaction, letter, correct_guess)
    
    async def update_game_message(self, interaction: discord.Interaction, last_guess: str, was_correct: bool):
        # Create updated embed
        if self.is_multiplayer:
            title = f"<:hangpepe:1425770634415444028> Hangman: {self.player1.display_name} vs {self.player2.display_name}"
        else:
            title = f"<:hangpepe:1425770634415444028> Hangman: {self.player1.display_name}"
        
        embed = discord.Embed(title=title, color=discord.Color.blue())
        
        # Add word display
        embed.add_field(name="Word", value=self.get_display_word(), inline=False)
        
        # Add hangman drawing
        embed.add_field(name="Hangman", value=self.get_hangman_drawing(), inline=False)
        
        # Add guessed letters
        if self.guessed_letters:
            guessed_str = ' '.join(sorted(self.guessed_letters))
            embed.add_field(name="Guessed Letters", value=guessed_str, inline=False)
        
        # Add tries remaining
        tries_left = self.max_tries - self.wrong_guesses
        embed.add_field(name="Tries Left", value=f"❤️ {tries_left}/{self.max_tries}", inline=True)
        
        # Add scores in multiplayer
        if self.is_multiplayer:
            score_text = f"{self.player1.display_name}: **{self.player1_correct}** | {self.player2.display_name}: **{self.player2_correct}**"
            embed.add_field(name="Score (Correct Letters)", value=score_text, inline=False)
        
        # Add last guess result
        if last_guess:
            if was_correct:
                embed.add_field(name="Last Guess", value=f"✅ **{last_guess}** - Correct!", inline=True)
            else:
                embed.add_field(name="Last Guess", value=f"<a:warning:1424944783587147868> **{last_guess}** - Wrong!", inline=True)
        
        # Add game status
        if self.game_over:
            if self.winner:
                if self.is_multiplayer and self.wrong_guesses >= self.max_tries:
                    # Ran out of tries in multiplayer - winner by score
                    embed.description = f"💀 Out of tries!\n🎉 **{self.winner.display_name}** wins with more correct letters!\nThe word was: **{self.word}**"
                else:
                    # Normal win
                    embed.description = f"🎉 **{self.winner.display_name}** wins!\nThe word was: **{self.word}**"
                embed.color = discord.Color.green()
            else:
                # No winner (tie or singleplayer loss)
                if self.is_multiplayer:
                    embed.description = f"💀 Game Over! It's a tie!\nBoth players got **{self.player1_correct}** correct letters.\nThe word was: **{self.word}**"
                else:
                    embed.description = f"💀 Game Over! You ran out of tries.\nThe word was: **{self.word}**"
                embed.color = discord.Color.red()
            
            # Disable all buttons
            for item in self.children:
                item.disabled = True
        else:
            # Show whose turn it is
            if self.is_multiplayer:
                embed.description = f"**{self.current_player.display_name}**'s turn"
            else:
                embed.description = "Click a letter button to guess!"
        
        # Update buttons with new state
        self.update_buttons()
        
        # Edit the message
        try:
            if self.game_message:
                await self.game_message.edit(embed=embed, view=self)
            else:
                # Should not happen, but fallback
                await interaction.followup.send(embed=embed, view=self)
        except Exception as e:
            print(f"[hangman] Failed to update message: {e}")


class ChallengeView(discord.ui.View):
    def __init__(self, challenger: discord.User, opponent: discord.User, timeout: float = 60):
        super().__init__(timeout=timeout)
        self.challenger = challenger
        self.opponent = opponent
    
    @discord.ui.button(label="Accept", style=discord.ButtonStyle.success)
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.opponent.id:
            await interaction.response.send_message("<a:warning:1424944783587147868> Only the challenged user can accept.", ephemeral=True)
            return
        
        # Start the game
        await interaction.response.edit_message(
            content=f"✅ **{self.opponent.display_name}** accepted the challenge! Starting game...",
            view=None
        )
        
        # Create game
        word = random.choice(WORD_LIST)
        view = HangmanView(self.challenger, self.opponent, word)
        
        # Create initial embed
        embed = discord.Embed(
            title=f"<:hangpepe:1425770634415444028> Hangman: {self.challenger.display_name} vs {self.opponent.display_name}",
            description=f"**{self.challenger.display_name}**'s turn",
            color=discord.Color.blue()
        )
        
        embed.add_field(name="Word", value=view.get_display_word(), inline=False)
        embed.add_field(name="Hangman", value=view.get_hangman_drawing(), inline=False)
        embed.add_field(name="Tries Left", value=f"❤️ {view.max_tries}/{view.max_tries}", inline=True)
        
        # Send game message
        game_msg = await interaction.followup.send(embed=embed, view=view)
        view.game_message = game_msg
    
    @discord.ui.button(label="Decline", style=discord.ButtonStyle.danger)
    async def decline(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.opponent.id and interaction.user.id != self.challenger.id:
            await interaction.response.send_message("<a:warning:1424944783587147868> Only the challenger or challenged can decline.", ephemeral=True)
            return
        
        who = interaction.user
        if who.id == self.challenger.id:
            content = f"<a:warning:1424944783587147868> **{who.display_name}** canceled the challenge."
        else:
            content = f"<a:warning:1424944783587147868> **{who.display_name}** declined the challenge."
        
        await interaction.response.edit_message(content=content, view=None)


class HangmanCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @app_commands.command(name='hangman', description='Play a game of Hangman')
    @app_commands.describe(opponent='Challenge another user to multiplayer (leave empty for singleplayer)')
    async def hangman(self, interaction: discord.Interaction, opponent: Optional[discord.User] = None):
        challenger = interaction.user
        
        # Check if challenging self
        if opponent and opponent.id == challenger.id:
            await interaction.response.send_message("<a:warning:1424944783587147868> You can't challenge yourself!", ephemeral=True)
            return
        
        # Check if challenging a bot
        if opponent and opponent.bot:
            await interaction.response.send_message("<a:warning:1424944783587147868> You can't challenge a bot!", ephemeral=True)
            return
        
        if opponent:
            # Multiplayer mode - send challenge
            view = ChallengeView(challenger, opponent)
            await interaction.response.send_message(
                f"<:hangpepe:1425770634415444028> {opponent.mention}, **{challenger.display_name}** has challenged you to Hangman!",
                view=view
            )
        else:
            # Singleplayer mode - start immediately
            await interaction.response.defer()
            
            word = random.choice(WORD_LIST)
            view = HangmanView(challenger, None, word)
            
            # Create initial embed
            embed = discord.Embed(
                title=f"<:hangpepe:1425770634415444028> Hangman: {challenger.display_name}",
                description="Click a letter button to guess!",
                color=discord.Color.blue()
            )
            
            embed.add_field(name="Word", value=view.get_display_word(), inline=False)
            embed.add_field(name="Hangman", value=view.get_hangman_drawing(), inline=False)
            embed.add_field(name="Tries Left", value=f"❤️ {view.max_tries}/{view.max_tries}", inline=True)
            
            # Send game message
            game_msg = await interaction.followup.send(embed=embed, view=view)
            view.game_message = game_msg


async def setup(bot: commands.Bot):
    await bot.add_cog(HangmanCog(bot))
