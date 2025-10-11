import io
import random
from typing import Optional
import discord
from discord.ext import commands
from discord import app_commands
from PIL import Image, ImageDraw, ImageFont # type: ignore


def _generate_empty_board_image(width: int = 600, height: int = 600) -> io.BytesIO:

    img = Image.new('RGBA', (width, height), (30, 30, 30, 255))
    draw = ImageDraw.Draw(img)
    # draw border
    pad = 20
    draw.rectangle([pad, pad, width - pad, height - pad], outline=(220, 220, 220), width=4)
    # draw 2 vertical and 2 horizontal lines to make 3x3
    # vertical positions
    third_w = (width - 2 * pad) / 3
    third_h = (height - 2 * pad) / 3
    for i in range(1, 3):
        x = pad + i * third_w
        draw.line([(x, pad), (x, height - pad)], fill=(220, 220, 220), width=6)
        y = pad + i * third_h
        draw.line([(pad, y), (width - pad, y)], fill=(220, 220, 220), width=6)

    bio = io.BytesIO()
    img.save(bio, 'PNG')
    bio.seek(0)
    return bio


class ChallengeView(discord.ui.View):
    def __init__(self, challenger: discord.User, opponent: discord.User, timeout: Optional[float] = 60):
        super().__init__(timeout=timeout)
        self.challenger = challenger
        self.opponent = opponent

    @discord.ui.button(label="Accept", style=discord.ButtonStyle.success)
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.opponent.id:
            await interaction.response.send_message("<a:warning:1424944783587147868> Only the challenged user can accept.", ephemeral=True)
            return

        # start the game
        await interaction.response.edit_message(content=f"**{self.opponent.display_name}** accepted the challenge! Starting game...", view=None)
        # send the board image and buttons
        try:
            bio = _generate_empty_board_image()
        except Exception:
            await interaction.followup.send("This command requires the Pillow library. Install it in the bot environment.")
            return

        file = discord.File(bio, filename='board.png')
        # Randomly assign X/O so challenger isn't always X
        if random.choice([True, False]):
            player_x, player_o = self.challenger, self.opponent
        else:
            player_x, player_o = self.opponent, self.challenger

        # Create the view
        view = TicTacToeView(player_x, player_o)

        # Create a single embed that references the attachment so the image, status, and buttons stay together
        status_embed = discord.Embed(title=f"<a:tictactoe:1424942287070433342> Tic-Tac-Toe: **{player_x.display_name}** (X) vs **{player_o.display_name}** (O)")
        status_embed.description = f"{player_x.display_name}'s turn (X)"
        status_embed.set_image(url="attachment://board.png")

        # Send one message containing the file, embed, and interactive view so they don't get separated by Discord
        game_msg = await interaction.followup.send(file=file, embed=status_embed, view=view)

        # store a single reference to the message on the view so callbacks can update/delete it
        view.game_message = game_msg

    @discord.ui.button(label="Decline", style=discord.ButtonStyle.danger)
    async def decline(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.opponent.id and interaction.user.id != self.challenger.id:
            await interaction.response.send_message("<a:warning:1424944783587147868> Only the challenger or challenged can decline.", ephemeral=True)
            return
        await interaction.response.edit_message(content=f"<a:tictactoe:1424942287070433342> **{self.opponent.display_name}** declined the challenge.", view=None)

        # Show who actually declined/canceled the challenge
        who = interaction.user
        if who.id == self.challenger.id:
            content = f"<a:tictactoe:1424942287070433342> **{who.display_name}** canceled the challenge."
        else:
            content = f"<a:tictactoe:1424942287070433342> **{who.display_name}** declined the challenge."

        try:
            await interaction.response.edit_message(content=content, view=None)
        except discord.errors.InteractionResponded:
            # If this interaction was already responded to, try editing the original message
            try:
                # interaction.message is the message that holds the view
                if getattr(interaction, 'message', None) is not None:
                    await interaction.message.edit(content=content, view=None)
                else:
                    # Last resort: send a followup message
                    await interaction.followup.send(content)
            except Exception:
                # If that also fails, send a followup so the user sees the result
                try:
                    await interaction.followup.send(content)
                except Exception:
                    # give up silently; log would be available in bot logs
                    pass


class TicTacToeButton(discord.ui.Button):
    def __init__(self, index: int, view: 'TicTacToeView'):
        # Use a visible placeholder label (middle dot) because empty or whitespace-only labels are rejected by the API
        super().__init__(label="·", style=discord.ButtonStyle.secondary, row=index // 3)
        self.index = index
        self.ttt_view = view

    async def callback(self, interaction: discord.Interaction):
        user = interaction.user
        # check allowed players
        if user.id not in (self.ttt_view.player_x.id, self.ttt_view.player_o.id):
            await interaction.response.send_message("<a:warning:1424944783587147868> You're not a participant in this game.", ephemeral=True)
            return

        # check turn
        if user.id != self.ttt_view.current_player_id:
            await interaction.response.send_message("<a:warning:1424944783587147868> Not your turn.", ephemeral=True)
            return

        symbol = self.ttt_view.current_symbol
        # update state
        if self.ttt_view.board[self.index] is not None:
            await interaction.response.send_message("<a:warning:1424944783587147868> This cell is already taken.", ephemeral=True)
            return

        self.ttt_view.board[self.index] = symbol
        # mark button (update this UI button instance)
        self.label = symbol
        self.disabled = True
        # use green for X (success) and red for O (danger)
        self.style = discord.ButtonStyle.success if symbol == 'X' else discord.ButtonStyle.danger

        # check win/draw
        winner = self.ttt_view.check_winner()

        # Acknowledge the button press and we will send a followup with the updated board image
        await interaction.response.defer()

        # regenerate the board image with current moves
        try:
            bio = _generate_empty_board_image()
            # draw X/O onto the image according to board state
            img = Image.open(bio).convert('RGBA')
            draw = ImageDraw.Draw(img)
            pad = 20
            w, h = img.size
            third_w = (w - 2 * pad) / 3
            third_h = (h - 2 * pad) / 3
            # choose a font size
            try:
                font = ImageFont.truetype('arial.ttf', int(min(third_w, third_h) * 0.6))
            except Exception:
                font = ImageFont.load_default()

            # Colors: green for X, red for O
            color_x = (50, 205, 50)    # lime green
            color_o = (220, 20, 60)    # crimson red
            stroke = max(3, int(min(third_w, third_h) * 0.12))
            for idx, mark in enumerate(self.ttt_view.board):
                if mark is None:
                    continue
                col = idx % 3
                row = idx // 3
                # calculate cell box
                x0 = int(pad + col * third_w + third_w * 0.12)
                y0 = int(pad + row * third_h + third_h * 0.12)
                x1 = int(pad + (col + 1) * third_w - third_w * 0.12)
                y1 = int(pad + (row + 1) * third_h - third_h * 0.12)
                if mark == 'X':
                    # draw two diagonal lines in green
                    draw.line([(x0, y0), (x1, y1)], fill=color_x, width=stroke)
                    draw.line([(x0, y1), (x1, y0)], fill=color_x, width=stroke)
                else:
                    # draw an O as an ellipse outline in red
                    # PIL's ellipse outline width supported in modern Pillow; fallback handled by width param
                    draw.ellipse([(x0, y0), (x1, y1)], outline=color_o, width=stroke)

            # If there's a winner, draw a connecting line across the three winning cells
            combo = self.ttt_view.get_winning_combo()
            if combo:
                a_idx, b_idx, c_idx = combo
                def cell_center(index):
                    col = index % 3
                    row = index // 3
                    cx = int(pad + col * third_w + third_w / 2)
                    cy = int(pad + row * third_h + third_h / 2)
                    return (cx, cy)

                p1 = cell_center(a_idx)
                p3 = cell_center(c_idx)
                # determine winner mark from board (safer than outer "winner")
                mark = self.ttt_view.board[a_idx]
                line_color = color_x if mark == 'X' else color_o

                # extend the line a bit beyond the centers so it covers the full cell region
                dx = p3[0] - p1[0]
                dy = p3[1] - p1[1]
                dist = (dx * dx + dy * dy) ** 0.5 or 1.0
                nx = dx / dist
                ny = dy / dist
                ext = max(third_w, third_h) * 0.35
                start = (int(p1[0] - nx * ext), int(p1[1] - ny * ext))
                end = (int(p3[0] + nx * ext), int(p3[1] + ny * ext))

                # draw a bold black outline first, then the colored line for contrast
                outline_width = max(8, int(stroke * 1.8))
                core_width = max(4, int(stroke * 1.1))
                draw.line([start, end], fill=(0, 0, 0), width=outline_width)
                draw.line([start, end], fill=line_color, width=core_width)

            # write image to bytes
            out = io.BytesIO()
            img.save(out, 'PNG')
            out.seek(0)
        except Exception as e:
            # If Pillow is missing or something else failed, notify and continue with button labels only
            print(f"<a:warning:1424944783587147868> Failed to render board image: {e}")
            out = None

        # disable buttons if game over or draw
        if winner or (all(cell is not None for cell in self.ttt_view.board) and not winner):
            for item in self.ttt_view.children:
                item.disabled = True

        # send updated board message (edit the original single game message to keep image, embed and view together)
        if out is not None:
            file = discord.File(out, filename='board.png')
            new_embed = discord.Embed(title=f"<a:tictactoe:1424942287070433342> Tic-Tac-Toe: {self.ttt_view.player_x.display_name} (X) vs {self.ttt_view.player_o.display_name} (O)")
            # make embed reference the attachment so updated attachment is shown in the embed
            new_embed.set_image(url="attachment://board.png")
            # status line
            if winner:
                new_embed.description = f"<a:trophy:1424944527315042415> Game over — **{winner}** wins! <a:trophy:1424944527315042415>"
            elif all(cell is not None for cell in self.ttt_view.board):
                new_embed.description = "Game over — Draw!"
            else:
                # show the NEXT player's turn (the one who will play next), not the player who just moved
                next_symbol = 'O' if self.ttt_view.current_symbol == 'X' else 'X'
                next_name = self.ttt_view.player_x.display_name if next_symbol == 'X' else self.ttt_view.player_o.display_name
                new_embed.description = f"<a:tictactoe:1424942287070433342> **{next_name}'s** turn ({next_symbol})"

            # Edit the original game message: replace attachment, embed and view in-place
            # Discord.py supports editing with attachments - we pass attachments=[] to clear old ones
            # and then provide the new file(s) in the edit call
            try:
                game_msg = getattr(self.ttt_view, 'game_message', None)
                if game_msg:
                    # Edit the existing message with new attachment, embed and view
                    # Use attachments=[] to clear old attachments, then pass new file via attachments parameter
                    await game_msg.edit(attachments=[file], embed=new_embed, view=self.ttt_view)
                else:
                    # No existing message stored; send a new combined message and keep a reference
                    new_msg = await interaction.followup.send(file=file, embed=new_embed, view=self.ttt_view)
                    self.ttt_view.game_message = new_msg
            except Exception as e:
                # log the exception to help debug why edit failed
                try:
                    print(f"[tictactoe] edit with attachments failed: {e}")
                except Exception:
                    pass
                # If edit fails, try without clearing attachments (just update embed and view)
                try:
                    game_msg = getattr(self.ttt_view, 'game_message', None)
                    if game_msg:
                        # Keep the existing attachment, just update embed text and view
                        await game_msg.edit(embed=new_embed, view=self.ttt_view)
                    else:
                        new_msg = await interaction.followup.send(file=file, embed=new_embed, view=self.ttt_view)
                        self.ttt_view.game_message = new_msg
                except Exception as e2:
                    try:
                        print(f"[tictactoe] fallback embed-only edit failed: {e2}")
                    except Exception:
                        pass

        # announce winner or draw
        if winner:
            player_name = self.ttt_view.player_x.display_name if winner == 'X' else self.ttt_view.player_o.display_name
            # increment persistent win counter if available on the bot
            try:
                bot = getattr(interaction.client, 'bot', None) or interaction.client
                # determine winner id
                winner_id = self.ttt_view.player_x.id if winner == 'X' else self.ttt_view.player_o.id
                wins = getattr(bot, 'user_wins_tictactoe', None)
                if wins is not None:
                    wins[winner_id] = wins.get(winner_id, 0) + 1
                    # persist stats if available
                    save_fn = getattr(bot, 'save_stats', None)
                    if save_fn is not None:
                        try:
                            await save_fn()
                        except Exception:
                            pass
            except Exception:
                pass

            await interaction.followup.send(f"<a:trophy:1424944527315042415> **{player_name}** ({winner}) wins! <a:trophy:1424944527315042415>")
            # disable the view to prevent more clicks and edit the game message to reflect final state
            try:
                game_msg = getattr(self.ttt_view, 'game_message', None)
                for item in self.ttt_view.children:
                    item.disabled = True
                if game_msg:
                    await game_msg.edit(view=self.ttt_view)
            except Exception:
                pass
            self.ttt_view.stop()
            return

        if all(cell is not None for cell in self.ttt_view.board) and not winner:
            await interaction.followup.send("<a:tictactoe:1424942287070433342> It's a draw!")
            try:
                game_msg = getattr(self.ttt_view, 'game_message', None)
                for item in self.ttt_view.children:
                    item.disabled = True
                if game_msg:
                    await game_msg.edit(view=self.ttt_view)
            except Exception:
                pass
            self.ttt_view.stop()
            return

        # switch player
        self.ttt_view.switch_turn()
        # Optionally send a short followup to indicate next player's turn (we already updated embed description)


class TicTacToeView(discord.ui.View):
    def __init__(self, player_x: discord.User, player_o: discord.User, timeout: Optional[float] = 3600):
        super().__init__(timeout=timeout)
        self.player_x = player_x
        self.player_o = player_o
        # X always starts
        self.current_symbol = 'X'
        self.player_map = {'X': player_x.id, 'O': player_o.id}
        self.board = [None] * 9
        # placeholder for the single combined message (file + embed + view)
        self.game_message = None
        # add 9 buttons
        for i in range(9):
            self.add_item(TicTacToeButton(i, self))

    @property
    def current_player_id(self):
        return self.player_map[self.current_symbol]

    def current_player_name(self):
        return self.player_x.display_name if self.current_symbol == 'X' else self.player_o.display_name

    def switch_turn(self):
        self.current_symbol = 'O' if self.current_symbol == 'X' else 'X'

    def check_winner(self) -> Optional[str]:
        combos = [(0,1,2),(3,4,5),(6,7,8),(0,3,6),(1,4,7),(2,5,8),(0,4,8),(2,4,6)]
        for a, b_idx, c in combos:
            if self.board[a] and self.board[a] == self.board[b_idx] == self.board[c]:
                return self.board[a]
        return None

    def get_winning_combo(self) -> Optional[tuple]:
        """Return the indices (a,b,c) of the winning combo or None if no winner."""
        combos = [(0,1,2),(3,4,5),(6,7,8),(0,3,6),(1,4,7),(2,5,8),(0,4,8),(2,4,6)]
        for a,b_idx,c in combos:
            if self.board[a] and self.board[a] == self.board[b_idx] == self.board[c]:
                return (a, b_idx, c)
        return None


class TicTacToeCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name='tictactoe', description='Challenge someone to a Tic-Tac-Toe match')
    @app_commands.describe(opponent='User to challenge')
    async def tictactoe(self, interaction: discord.Interaction, opponent: discord.User):
        challenger = interaction.user
        if opponent.id == challenger.id:
            await interaction.response.send_message("<a:warning:1424944783587147868> You can't challenge yourself.", ephemeral=True)
            return

        view = ChallengeView(challenger, opponent)
        try:
            await interaction.response.send_message(f"<a:tictactoe:1424942287070433342> {opponent.mention}, **{challenger.display_name}** is requesting a Tic-Tac-Toe battle!", view=view)
        except discord.errors.NotFound:
            # Interaction token may be invalid/expired. Fallback to sending a normal channel message so the challenge still appears.
            try:
                channel = interaction.channel
                if channel is None:
                    # last resort: fetch channel by id
                    channel = await self.bot.fetch_channel(interaction.channel_id)
                await channel.send(f"<a:tictactoe:1424942287070433342> {opponent.mention}, **{challenger.display_name}** is requesting a Tic-Tac-Toe battle!", view=view)
            except Exception:
                # If even that fails, try a simple DM to challenger so they at least know it failed
                try:
                    await challenger.send("Failed to send Tic-Tac-Toe challenge in the channel. Please try again.")
                except Exception:
                    pass
        except Exception:
            # generic fallback: try to send a channel message
            try:
                channel = interaction.channel or await self.bot.fetch_channel(interaction.channel_id)
                await channel.send(f"<a:tictactoe:1424942287070433342> {opponent.mention}, **{challenger.display_name}** is requesting a Tic-Tac-Toe battle!", view=view)
            except Exception:
                try:
                    await challenger.send("Failed to send Tic-Tac-Toe challenge due to an unexpected error.")
                except Exception:
                    pass


async def setup(bot: commands.Bot):
    await bot.add_cog(TicTacToeCog(bot))
