import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional

# Simple Rock-Paper-Scissors game
# Usage: /rockpaperscissor opponent:@user

class RPSChallengeView(discord.ui.View):
    def __init__(self, challenger: discord.User, opponent: discord.User, timeout: float = 60.0):
        super().__init__(timeout=timeout)
        self.challenger = challenger
        self.opponent = opponent

    @discord.ui.button(label='Accept', style=discord.ButtonStyle.success)
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.opponent.id:
            await interaction.response.send_message("<a:warning:1424944783587147868> Only the challenged user can accept.", ephemeral=True)
            return
        await interaction.response.edit_message(content=f"{self.opponent.display_name} accepted the challenge! Starting Rock-Paper-Scissors...", view=None)

        # start the game: send the initial game message with the move buttons
        game_view = RPSGameView(self.challenger, self.opponent)
        embed = discord.Embed(title="<a:rockpaperscissor:1425347479389470720> Rock — Paper — Scissors", description=f"{self.challenger.mention} vs {self.opponent.mention}\nBoth players: pick your move.")
        await interaction.followup.send(embed=embed, view=game_view)

    @discord.ui.button(label='Decline', style=discord.ButtonStyle.danger)
    async def decline(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.opponent.id and interaction.user.id != self.challenger.id:
            await interaction.response.send_message("<a:warning:1424944783587147868> Only the challenger or challenged can decline.", ephemeral=True)
            return
        await interaction.response.edit_message(content=f"{interaction.user.display_name} declined the challenge.", view=None)


class RPSButton(discord.ui.Button):
    def __init__(self, move: str, row: int = 0):
        super().__init__(label=move.capitalize(), style=discord.ButtonStyle.secondary, row=row)
        self.move = move.lower()

    async def callback(self, interaction: discord.Interaction):
        view: RPSGameView = self.view  # type: ignore
        await view.player_choice(interaction.user, self.move, interaction)


class RPSGameView(discord.ui.View):
    def __init__(self, player1: discord.User, player2: discord.User, timeout: float = 120.0):
        super().__init__(timeout=timeout)
        self.player1 = player1
        self.player2 = player2
        self.choices = {}  # user_id -> 'rock'|'paper'|'scissors'

        # Add move buttons for both players to click
        self.add_item(RPSButton('🪨', row=0))
        self.add_item(RPSButton('📃', row=0))
        self.add_item(RPSButton('✂️', row=0))

    async def player_choice(self, user: discord.User, move: str, interaction: discord.Interaction):
        # Only allow the two players to pick
        if user.id not in (self.player1.id, self.player2.id):
            await interaction.response.send_message("<a:warning:1424944783587147868> You are not part of this game.", ephemeral=True)
            return

        # Record choice
        if user.id in self.choices:
            await interaction.response.send_message("<a:warning:1424944783587147868> You already picked a move.", ephemeral=True)
            return

        self.choices[user.id] = move
        # Acknowledge for privacy
        try:
            await interaction.response.send_message(f"You selected **{move}**.", ephemeral=True)
        except Exception:
            try:
                await interaction.followup.send(f"You selected **{move}**.", ephemeral=True)
            except Exception:
                pass

        # If both players have chosen, determine winner
        if self.player1.id in self.choices and self.player2.id in self.choices:
            await self.finish_game(interaction)

    def _determine_winner(self, move1: str, move2: str) -> int:
        # return 0 for tie, 1 if move1 wins, 2 if move2 wins
        beats = {
            'rock': 'scissors',
            'scissors': 'paper',
            'paper': 'rock',
        }
        if move1 == move2:
            return 0
        if beats.get(move1) == move2:
            return 1
        return 2

    async def finish_game(self, interaction: discord.Interaction):
        m1 = self.choices[self.player1.id]
        m2 = self.choices[self.player2.id]
        result = self._determine_winner(m1, m2)

        if result == 0:
            desc = f"It's a tie! Both players chose **{m1}**."
        elif result == 1:
            desc = f"<a:trophy:1424944527315042415> {self.player1.mention} wins! **{m1}** beats **{m2}**."
        else:
            desc = f"<a:trophy:1424944527315042415> {self.player2.mention} wins! **{m2}** beats **{m1}**."

        embed = discord.Embed(title="Rock — Paper — Scissors — Result", description=desc)
        embed.add_field(name=self.player1.display_name, value=m1, inline=True)
        embed.add_field(name=self.player2.display_name, value=m2, inline=True)

        # Disable all buttons now that the game is over
        for child in self.children:
            child.disabled = True
        try:
            # Try to edit the original message if possible
            if getattr(interaction, 'message', None) is not None:
                await interaction.message.edit(embed=embed, view=self)
            else:
                await interaction.response.send_message(embed=embed)
        except Exception:
            try:
                await interaction.response.send_message(embed=embed)
            except Exception:
                try:
                    await interaction.followup.send(embed=embed)
                except Exception:
                    pass
        # If there was a winner, increment their RPS win count on the bot and persist
        try:
            bot = getattr(interaction, 'client', None) or getattr(interaction, 'bot', None)
            if bot is None:
                bot = getattr(self, 'bot', None)
            if bot is not None:
                inc_fn = getattr(bot, 'increment_win_rps', None)
                if inc_fn is not None and result in (1, 2):
                    winner_id = self.player1.id if result == 1 else self.player2.id
                    try:
                        await inc_fn(winner_id)
                    except Exception as e:
                        print(f"Failed to save rps win: {e}")
        except Exception:
            pass


class RPSCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name='rockpaperscissors', description='Challenge a user to Rock-Paper-Scissors')
    @app_commands.describe(opponent='The user you want to challenge')
    async def rps(self, interaction: discord.Interaction, opponent: discord.User):
        if opponent.id == interaction.user.id:
            await interaction.response.send_message("<a:warning:1424944783587147868> You can't challenge yourself.", ephemeral=True)
            return
        # Send challenge view
        view = RPSChallengeView(interaction.user, opponent)
        await interaction.response.send_message(f"<a:rockpaperscissor:1425347479389470720> {interaction.user.mention} challenged {opponent.mention} to Rock-Paper-Scissors!", view=view)


async def setup(bot: commands.Bot):
    await bot.add_cog(RPSCog(bot))
