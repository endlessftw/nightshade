import io
import random
from typing import Optional, List
import discord
from discord.ext import commands
from discord import app_commands
from PIL import Image, ImageDraw, ImageFont # type: ignore


def _generate_empty_board_image(width: int = 700, height: int = 600) -> io.BytesIO:

    cols = 7
    rows = 6
    bg = (30, 30, 30, 255)
    slot = (220, 220, 220)
    img = Image.new('RGBA', (width, height), bg)
    draw = ImageDraw.Draw(img)

    pad_x = 30
    pad_y = 30
    board_w = width - pad_x * 2
    board_h = height - pad_y * 2
    # draw rounded rectangle background for the board
    draw.rectangle([pad_x, pad_y, pad_x + board_w, pad_y + board_h], fill=(15, 94, 190), outline=slot)

    cell_w = board_w / cols
    cell_h = board_h / rows

    # draw empty circular slots
    for r in range(rows):
        for c in range(cols):
            cx = int(pad_x + c * cell_w + cell_w / 2)
            cy = int(pad_y + r * cell_h + cell_h / 2)
            radius = int(min(cell_w, cell_h) * 0.38)
            bbox = [cx - radius, cy - radius, cx + radius, cy + radius]
            draw.ellipse(bbox, fill=(40, 40, 40), outline=(10, 10, 10))

    # draw column numbers (1..cols) centered above each column
    # choose a readable font sized relative to cell height; prefer a TTF if available
    try:
        # compute a font size based on cell height
        font_size = max(12, int(cell_h * 0.28))
        try:
            # common Windows font path; Pillow will raise if not found
            font = ImageFont.truetype(r'C:\Windows\Fonts\arial.ttf', font_size)
        except Exception:
            # fallback to default bitmap font
            font = ImageFont.load_default()
    except Exception:
        font = None

    num_color = (245, 245, 245)
    stroke_color = (0, 0, 0)
    stroke_w = 1
    for c in range(cols):
        text = str(c + 1)
        # Compute text width/height in a Pillow-version-compatible way
        try:
            # Pillow >= 8.0: ImageDraw.textbbox
            bbox = draw.textbbox((0, 0), text, font=font) if hasattr(draw, 'textbbox') else None
            if bbox:
                tw = bbox[2] - bbox[0]
                th = bbox[3] - bbox[1]
            else:
                raise AttributeError
        except Exception:
            try:
                # fallback to font.getsize
                if font:
                    tw, th = font.getsize(text)
                else:
                    # last resort: estimate
                    tw, th = (10, 10)
            except Exception:
                tw, th = (10, 10)

        tx = int(pad_x + c * cell_w + cell_w / 2 - tw / 2)
        # place the numbers slightly above the board area with a small gap
        ty = int(pad_y - th - 6)
        # clamp into image bounds
        ty = max(2, min(ty, height - th - 2))
        if font:
            try:
                draw.text((tx, ty), text, fill=num_color, font=font, stroke_width=stroke_w, stroke_fill=stroke_color)
            except TypeError:
                # older Pillow may not support stroke args
                draw.text((tx, ty), text, fill=num_color, font=font)
        else:
            draw.text((tx, ty), text, fill=num_color)

    # draw column numbers centered below each column as well
    for c in range(cols):
        text = str(c + 1)
        # reuse computed text size logic
        try:
            bbox = draw.textbbox((0, 0), text, font=font) if hasattr(draw, 'textbbox') else None
            if bbox:
                tw = bbox[2] - bbox[0]
                th = bbox[3] - bbox[1]
            else:
                raise AttributeError
        except Exception:
            try:
                if font:
                    tw, th = font.getsize(text)
                else:
                    tw, th = (10, 10)
            except Exception:
                tw, th = (10, 10)

        tx = int(pad_x + c * cell_w + cell_w / 2 - tw / 2)
        # place the numbers slightly below the board area with a small gap
        ty = int(pad_y + board_h + 6)
        # better place: just below the bottom-most slot so it's clearly visible
        # compute bottom-most slot radius and offset
        radius = int(min(cell_w, cell_h) * 0.38)
        ty = int(pad_y + board_h - (cell_h / 2) + radius + 6)
        # clamp into image bounds
        ty = max(2, min(ty, height - th - 2))
        if font:
            try:
                draw.text((tx, ty), text, fill=num_color, font=font, stroke_width=stroke_w, stroke_fill=stroke_color)
            except TypeError:
                draw.text((tx, ty), text, fill=num_color, font=font)
        else:
            draw.text((tx, ty), text, fill=num_color)

    bio = io.BytesIO()
    img.save(bio, 'PNG')
    bio.seek(0)
    return bio


class ConnectFourButton(discord.ui.Button):
    def __init__(self, col: int, view: 'ConnectFourView'):
        # Place buttons across rows of up to 5 components to satisfy Discord limits
        super().__init__(label=str(col + 1), style=discord.ButtonStyle.secondary, row=(col // 5))
        self.col = col
        self.c4_view = view

    async def callback(self, interaction: discord.Interaction):
        user = interaction.user
        if user.id not in (self.c4_view.player1.id, self.c4_view.player2.id):
            await interaction.response.send_message("<a:warning:1424944783587147868> You're not a participant in this game.", ephemeral=True)
            return

        if user.id != self.c4_view.current_player_id:
            await interaction.response.send_message("<a:warning:1424944783587147868> Not your turn.", ephemeral=True)
            return

        col = self.col
        # find lowest empty slot in column
        row = None
        for r in range(self.c4_view.rows - 1, -1, -1):
            if self.c4_view.board[r][col] is None:
                row = r
                break

        if row is None:
            await interaction.response.send_message("<a:warning:1424944783587147868> This column is full.", ephemeral=True)
            return

        symbol = self.c4_view.current_symbol
        self.c4_view.board[row][col] = symbol

        # Acknowledge quickly and then update the single game message
        await interaction.response.defer()

        # render updated image
        try:
            bio = _generate_empty_board_image()
            img = Image.open(bio).convert('RGBA')
            draw = ImageDraw.Draw(img)

            pad_x = 30
            pad_y = 30
            cols = self.c4_view.cols
            rows = self.c4_view.rows
            w, h = img.size
            board_w = w - pad_x * 2
            board_h = h - pad_y * 2
            cell_w = board_w / cols
            cell_h = board_h / rows

            # colors
            color1 = (220, 20, 60)   # red
            color2 = (50, 205, 50)   # green

            for r in range(rows):
                for c in range(cols):
                    mark = self.c4_view.board[r][c]
                    if mark is None:
                        continue
                    cx = int(pad_x + c * cell_w + cell_w / 2)
                    cy = int(pad_y + r * cell_h + cell_h / 2)
                    radius = int(min(cell_w, cell_h) * 0.38)
                    bbox = [cx - radius, cy - radius, cx + radius, cy + radius]
                    fill = color1 if mark == 'X' else color2
                    draw.ellipse(bbox, fill=fill, outline=(0, 0, 0))

            # highlight winning line if exists
            combo = self.c4_view.get_winning_combo()
            if combo:
                (r1, c1), (r2, c2), (r3, c3), (r4, c4) = combo
                def center(rr, cc):
                    return (int(pad_x + cc * cell_w + cell_w / 2), int(pad_y + rr * cell_h + cell_h / 2))

                p1 = center(r1, c1)
                p4 = center(r4, c4)
                color_line = (255, 215, 0)
                # draw bold line with outline
                draw.line([p1, p4], fill=(0, 0, 0), width=14)
                draw.line([p1, p4], fill=color_line, width=10)

            out = io.BytesIO()
            img.save(out, 'PNG')
            out.seek(0)
        except Exception as e:
            print(f"[connectfour] Failed to render image: {e}")
            out = None

        # check win/draw
        winner = self.c4_view.check_winner()
        is_draw = all(self.c4_view.board[r][c] is not None for r in range(self.c4_view.rows) for c in range(self.c4_view.cols))

        # disable buttons if column full or game over
        if winner or is_draw:
            for item in self.c4_view.children:
                item.disabled = True
        else:
            # optionally disable button if column is full
            col_full = all(self.c4_view.board[r][col] is not None for r in range(self.c4_view.rows))
            if col_full:
                # find corresponding button and disable
                for item in self.c4_view.children:
                    if isinstance(item, ConnectFourButton) and item.col == col:
                        item.disabled = True

        # update single game message
        if out is not None:
            file = discord.File(out, filename='connect4.png')
            # show color words instead of X/O
            new_embed = discord.Embed(title=f"<a:connectfour:1425036938984947712> Connect Four — {self.c4_view.player1.display_name} (🔴) vs {self.c4_view.player2.display_name} (🟢)")
            if winner:
                winner_name = self.c4_view.player1.display_name if winner == 'X' else self.c4_view.player2.display_name
                winner_color = '🔴' if winner == 'X' else '🟢'
                new_embed.description = f"<a:trophy:1424944527315042415> Game over — **{winner_name}** ({winner_color}) wins! <a:trophy:1424944527315042415>"
            elif is_draw:
                new_embed.description = "<a:connectfour:1425036938984947712> Game over — Draw!"
            else:
                next_symbol = 'O' if self.c4_view.current_symbol == 'X' else 'X'
                next_name = self.c4_view.player1.display_name if next_symbol == 'X' else self.c4_view.player2.display_name
                next_color = '🔴' if next_symbol == 'X' else '🟢'
                new_embed.description = f"**{next_name}**'s turn ({next_color})"
            new_embed.set_image(url='attachment://connect4.png')

            try:
                gm = getattr(self.c4_view, 'game_message', None)
                if gm:
                    # Edit the existing message with new attachment, embed and view
                    # Use attachments=[] to clear old attachments and provide new file
                    await gm.edit(attachments=[file], embed=new_embed, view=self.c4_view)
                else:
                    new_msg = await interaction.followup.send(file=file, embed=new_embed, view=self.c4_view)
                    self.c4_view.game_message = new_msg
            except Exception as e:
                # log the exception to help debug
                try:
                    print(f"[connectfour] edit with attachments failed: {e}")
                except Exception:
                    pass
                # If edit fails, try without replacing attachment (just update embed and view)
                try:
                    gm = getattr(self.c4_view, 'game_message', None)
                    if gm:
                        # Keep the existing attachment, just update embed text and view
                        await gm.edit(embed=new_embed, view=self.c4_view)
                    else:
                        new_msg = await interaction.followup.send(file=file, embed=new_embed, view=self.c4_view)
                        self.c4_view.game_message = new_msg
                except Exception as e2:
                    try:
                        print(f"[connectfour] fallback embed-only edit failed: {e2}")
                    except Exception:
                        pass

        # announce results if any
        if winner:
            winner_name = self.c4_view.player1.display_name if winner == 'X' else self.c4_view.player2.display_name
            # record persistent win counter if available on bot
            try:
                bot = interaction.client
                winner_id = self.c4_view.player1.id if winner == 'X' else self.c4_view.player2.id
                inc_fn = getattr(bot, 'increment_win_connectfour', None)
                if inc_fn is not None:
                    try:
                        await inc_fn(winner_id)
                    except Exception as e:
                        print(f"Failed to save connectfour win: {e}")
            except Exception:
                pass

            winner_color = '🔴' if winner == 'X' else '🟢'
            try:
                await interaction.followup.send(f"<a:trophy:1424944527315042415> **{winner_name}** wins! ({winner_color})<a:trophy:1424944527315042415>")
            except Exception:
                pass
            self.c4_view.stop()
            return

        if is_draw and not winner:
            try:
                await interaction.followup.send("<a:connectfour:1425036938984947712> It's a draw!")
            except Exception:
                pass
            self.c4_view.stop()
            return

        # switch turn
        self.c4_view.switch_turn()


class ConnectFourView(discord.ui.View):
    def __init__(self, player1: discord.User, player2: discord.User, timeout: Optional[float] = 3600):
        super().__init__(timeout=timeout)
        self.player1 = player1
        self.player2 = player2
        self.cols = 7
        self.rows = 6
        self.board: List[List[Optional[str]]] = [[None for _ in range(self.cols)] for _ in range(self.rows)]
        self.current_symbol = 'X'
        self.player_map = {'X': player1.id, 'O': player2.id}
        self.game_message = None
        # add column buttons (placed in a single row)
        for c in range(self.cols):
            self.add_item(ConnectFourButton(c, self))

    @property
    def current_player_id(self):
        return self.player_map[self.current_symbol]

    def switch_turn(self):
        self.current_symbol = 'O' if self.current_symbol == 'X' else 'X'

    def check_winner(self) -> Optional[str]:
        # check horizontal, vertical and two diagonal directions for 4 in a row
        board = self.board
        rows = self.rows
        cols = self.cols
        for r in range(rows):
            for c in range(cols):
                mark = board[r][c]
                if not mark:
                    continue
                # horizontal
                if c + 3 < cols and all(board[r][c + i] == mark for i in range(4)):
                    return mark
                # vertical
                if r + 3 < rows and all(board[r + i][c] == mark for i in range(4)):
                    return mark
                # diag down-right
                if r + 3 < rows and c + 3 < cols and all(board[r + i][c + i] == mark for i in range(4)):
                    return mark
                # diag down-left
                if r + 3 < rows and c - 3 >= 0 and all(board[r + i][c - i] == mark for i in range(4)):
                    return mark
        return None

    def get_winning_combo(self):
        board = self.board
        rows = self.rows
        cols = self.cols
        for r in range(rows):
            for c in range(cols):
                mark = board[r][c]
                if not mark:
                    continue
                # horizontal
                if c + 3 < cols and all(board[r][c + i] == mark for i in range(4)):
                    return [(r, c + i) for i in range(4)]
                # vertical
                if r + 3 < rows and all(board[r + i][c] == mark for i in range(4)):
                    return [(r + i, c) for i in range(4)]
                # diag down-right
                if r + 3 < rows and c + 3 < cols and all(board[r + i][c + i] == mark for i in range(4)):
                    return [(r + i, c + i) for i in range(4)]
                # diag down-left
                if r + 3 < rows and c - 3 >= 0 and all(board[r + i][c - i] == mark for i in range(4)):
                    return [(r + i, c - i) for i in range(4)]
        return None


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

        await interaction.response.edit_message(content=f"**{self.opponent.display_name}** accepted the challenge! Starting Connect Four...", view=None)

        try:
            bio = _generate_empty_board_image()
        except Exception:
            await interaction.followup.send("This command requires the Pillow library. Install it in the bot environment.")
            return

        file = discord.File(bio, filename='connect4.png')
        # randomize who is X/O (player1 will be X -> Red, player2 will be O -> Green)
        if random.choice([True, False]):
            p1, p2 = self.challenger, self.opponent
        else:
            p1, p2 = self.opponent, self.challenger

        view = ConnectFourView(p1, p2)

        # show colors (Red/Green) instead of X/O to players
        embed = discord.Embed(title=f"<a:connectfour:1425036938984947712> Connect Four: **{p1.display_name}** (🔴) vs **{p2.display_name}** (🟢)")
        embed.description = f"**{p1.display_name}**'s turn (🔴)"
        embed.set_image(url='attachment://connect4.png')

        game_msg = await interaction.followup.send(file=file, embed=embed, view=view)
        view.game_message = game_msg

    @discord.ui.button(label="Decline", style=discord.ButtonStyle.danger)
    async def decline(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.opponent.id and interaction.user.id != self.challenger.id:
            await interaction.response.send_message("<a:warning:1424944783587147868> Only the challenger or challenged can decline.", ephemeral=True)
            return
        await interaction.response.edit_message(content=f"**{self.opponent.display_name}** declined the challenge.", view=None)


class ConnectFourCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name='connectfour', description='Challenge someone to a Connect Four match')
    @app_commands.describe(opponent='User to challenge')
    async def connectfour(self, interaction: discord.Interaction, opponent: discord.User):
        challenger = interaction.user
        if opponent.id == challenger.id:
            await interaction.response.send_message("<a:warning:1424944783587147868> You can't challenge yourself.", ephemeral=True)
            return

        view = ChallengeView(challenger, opponent)
        # Try to respond to the interaction; if that fails (unknown interaction / already acknowledged),
        # fall back to followup, channel send, or DM to ensure the opponent sees the challenge.
        try:
            # Prefer sending via response if it hasn't been used yet
            if not interaction.response.is_done():
                try:
                    await interaction.response.send_message(f"<a:connectfour:1425036938984947712> {opponent.mention}, you have been challenged to Connect Four by {challenger.display_name}", view=view)
                    return
                except (discord.NotFound, discord.HTTPException):
                    # fall through to followup/channel/DM
                    pass

            # Try followup (works whether response was used or not)
            try:
                await interaction.followup.send(f"<a:connectfour:1425036938984947712> {opponent.mention}, you have been challenged to Connect Four by {challenger.display_name}", view=view)
                return
            except Exception:
                pass

            # Try sending directly to the channel where the command was invoked
            try:
                if interaction.channel:
                    await interaction.channel.send(f"<a:connectfour:1425036938984947712> {opponent.mention}, you have been challenged to Connect Four by {challenger.display_name}")
                    return
            except Exception:
                pass

            # Last resort: DM the opponent
            try:
                await opponent.send(f"<a:connectfour:1425036938984947712> You have been challenged to Connect Four by {challenger.display_name}")
                return
            except Exception:
                pass

            # If all else fails, try to send an ephemeral followup if possible
            try:
                await interaction.followup.send("Failed to send challenge.", ephemeral=True)
            except Exception:
                # give up; avoid raising to the app command handler
                return
        except Exception:
            # Catch-all to avoid the app command bubbling an exception
            try:
                await interaction.followup.send("Failed to send challenge.", ephemeral=True)
            except Exception:
                return


async def setup(bot: commands.Bot):
    await bot.add_cog(ConnectFourCog(bot))
