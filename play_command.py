import discord
from discord.ext import commands
from discord import app_commands
import discord.utils
import pathlib
import asyncio
from typing import Optional

import discord.ui


class PauseResumeView(discord.ui.View):
    def __init__(self, voice_client: discord.VoiceClient, *, timeout: Optional[float] = None):
        super().__init__(timeout=timeout)
        self.voice_client = voice_client

    @discord.ui.button(label="Pause", style=discord.ButtonStyle.primary)
    async def toggle(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Only allow control if bot has a voice client and is in the same guild
        try:
            vc = self.voice_client
            if not vc:
                await interaction.response.send_message('<a:warning:1424944783587147868> No active voice client.', ephemeral=True)
                return

            if vc.is_playing() and not vc.is_paused():
                try:
                    vc.pause()
                    button.label = "Resume"
                    button.style = discord.ButtonStyle.success
                    await interaction.response.edit_message(view=self)
                except Exception as e:
                    await interaction.response.send_message(f'<a:warning:1424944783587147868> Failed to pause: {e}', ephemeral=True)
            elif vc.is_paused():
                try:
                    vc.resume()
                    button.label = "Pause"
                    button.style = discord.ButtonStyle.primary
                    await interaction.response.edit_message(view=self)
                except Exception as e:
                    await interaction.response.send_message(f'<a:warning:1424944783587147868>Failed to resume: {e}', ephemeral=True)
            else:
                # Nothing is playing
                await interaction.response.send_message('<a:warning:1424944783587147868> Nothing is currently playing.', ephemeral=True)
        except Exception:
            try:
                await interaction.response.send_message('<a:warning:1424944783587147868>Failed to control playback.', ephemeral=True)
            except Exception:
                pass

    @discord.ui.button(label="Skip", style=discord.ButtonStyle.danger)
    async def skip(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            vc = self.voice_client
            if not vc:
                await interaction.response.send_message('<a:warning:1424944783587147868>No active voice client.', ephemeral=True)
                return

            # Check if there's anything in the queue to skip to
            queue = getattr(vc, 'queue', None)
            if not queue:
                await interaction.response.send_message('<a:warning:1424944783587147868> Nothing queued to skip to.', ephemeral=True)
                return

            # Stop the current player — the existing after callback will schedule the next track
            try:
                vc.stop()
                await interaction.response.send_message('⏩ Skipped to next track.', ephemeral=True)
            except Exception as e:
                await interaction.response.send_message(f'<a:warning:1424944783587147868> Failed to skip: {e}', ephemeral=True)
        except Exception:
            try:
                await interaction.response.send_message('<a:warning:1424944783587147868> Failed to skip track.', ephemeral=True)
            except Exception:
                pass

# Plays a local file by name (or streams from YouTube if yt_dlp is installed).
# Usage: /play query: str
# Requirements for streaming: ffmpeg installed and yt_dlp available in the environment.

FFMPEG_OPTIONS = {
    # before_options enables ffmpeg to attempt reconnects for unstable streams
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

class PlayCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def _fetch_metadata_in_background(self, query: str):
        """Run yt_dlp extraction in a background thread to avoid blocking the event loop."""
        def _extract():
            try:
                import importlib
                yt_dlp = importlib.import_module('yt_dlp')
                ytdl_opts = {
                    'format': 'bestaudio/best',
                    'noplaylist': True,
                    'quiet': True,
                    'ignoreerrors': True,
                }
                with yt_dlp.YoutubeDL(ytdl_opts) as ydl:
                    info = ydl.extract_info(f"ytsearch1:{query}", download=False)
                    if not info:
                        return {}
                    entry = None
                    if 'entries' in info and info['entries']:
                        entry = info['entries'][0]
                    else:
                        entry = info
                    if not entry:
                        return {}

                    stream_url = None
                    fmts = entry.get('formats') or []
                    if fmts:
                        audio_fmts = [f for f in fmts if f.get('acodec') and f.get('acodec') != 'none']
                        if audio_fmts:
                            audio_only = [f for f in audio_fmts if not f.get('vcodec') or f.get('vcodec') == 'none']
                            candidates = audio_only or audio_fmts
                            def _fmt_score(f):
                                return (f.get('abr') or f.get('tbr') or f.get('filesize') or 0)
                            candidates.sort(key=_fmt_score, reverse=True)
                            stream_url = candidates[0].get('url')
                    if not stream_url:
                        stream_url = entry.get('url') or entry.get('webpage_url')

                    return {
                        'stream_url': stream_url,
                        'title': entry.get('title'),
                        'webpage': entry.get('webpage_url') or entry.get('url'),
                        'thumbnail': entry.get('thumbnail'),
                    }
            except Exception:
                return {}

        # Run blocking yt_dlp in a thread
        return await asyncio.to_thread(_extract)

    async def _play_next(self, voice_client: discord.VoiceClient):
        """
        Play the next item from the voice_client.queue if present.
        This runs in the bot event loop.
        """
        try:
            if not hasattr(voice_client, 'queue') or not voice_client.queue:
                return

            item = voice_client.queue.pop(0)
            local_path = item.get('local_path')
            stream_url = item.get('stream_url')
            title = item.get('title') or item.get('webpage') or 'Unknown'
            thumbnail = item.get('thumbnail')
            requester = item.get('requester')

            # If stream_url is still None and we have a query, try to fetch metadata (wait up to 3 seconds)
            if local_path is None and not stream_url and item.get('query'):
                try:
                    metadata = await asyncio.wait_for(
                        self._fetch_metadata_in_background(item['query']),
                        timeout=3.0
                    )
                    if metadata:
                        stream_url = metadata.get('stream_url') or stream_url
                        title = metadata.get('title') or title
                        thumbnail = metadata.get('thumbnail') or thumbnail
                        item['stream_url'] = stream_url
                        item['title'] = title
                        item['webpage'] = metadata.get('webpage') or item.get('webpage')
                        item['thumbnail'] = thumbnail
                except asyncio.TimeoutError:
                    pass  # Continue with whatever we have
                except Exception:
                    pass

            try:
                if local_path is not None:
                    source = discord.FFmpegPCMAudio(local_path, **FFMPEG_OPTIONS)
                else:
                    source = discord.FFmpegPCMAudio(stream_url, **FFMPEG_OPTIONS)
            except discord.errors.ClientException:
                # Can't prepare this source; skip to next
                await self._play_next(voice_client)
                return

            # after callback schedules next track when this one finishes
            def _after(err):
                try:
                    asyncio.run_coroutine_threadsafe(self._play_next(voice_client), self.bot.loop)
                except Exception:
                    pass

            voice_client.play(source, after=_after)

            # Send a now-playing embed. Prefer the original request channel stored with the queued item,
            # otherwise fall back to the guild system channel when available.
            try:
                guild = getattr(voice_client, 'guild', None)
                if guild:
                    channel = None
                    try:
                        chan_id = item.get('channel_id')
                        if chan_id:
                            channel = guild.get_channel(chan_id)
                    except Exception:
                        channel = None

                    if channel is None:
                        channel = guild.system_channel

                    if channel is not None and channel.permissions_for(guild.me).send_messages:
                        embed = discord.Embed(title="<a:music:1425403164688908299> Now playing", description=f"{title}", color=discord.Color.blurple())
                        if item.get('webpage'):
                            embed.add_field(name="Source", value=f"[Link]({item.get('webpage')})", inline=False)
                        try:
                            if requester:
                                embed.set_footer(text=f"Requested by {getattr(requester,'display_name', str(requester))}")
                        except Exception:
                            pass
                        if thumbnail:
                            try:
                                embed.set_thumbnail(url=thumbnail)
                            except Exception:
                                pass
                        # fire-and-forget send with Pause/Resume/Skip controls
                        try:
                            view = PauseResumeView(voice_client)
                            asyncio.create_task(channel.send(embed=embed, view=view))
                        except Exception:
                            try:
                                asyncio.create_task(channel.send(embed=embed))
                            except Exception:
                                pass
            except Exception:
                pass
        except Exception:
            return

    @app_commands.command(name='play', description='Join your voice channel and play an audio by name or search term')
    @app_commands.describe(query='Filename (in bot folder) or search term to play')
    async def play(self, interaction: discord.Interaction, query: str):
        # Ensure the user is in a voice channel
        user_voice = getattr(interaction.user, 'voice', None)
        if not user_voice or not getattr(user_voice, 'channel', None):
            await interaction.response.send_message('<a:warning:1424944783587147868> You need to be in a voice channel for me to join and play audio.', ephemeral=True)
            return

        voice_channel: discord.VoiceChannel = user_voice.channel

        # Connect or move the bot to the user's voice channel
        voice_client = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)
        # Defer the interaction early to avoid 'This interaction failed.' if processing takes >3s
        try:
            if not interaction.response.is_done():
                await interaction.response.defer(ephemeral=False)
        except Exception:
            pass
        try:
            if voice_client is None:
                # Try to connect with a longer timeout (60 seconds instead of default 30)
                voice_client = await voice_channel.connect(timeout=60.0)
            else:
                if voice_client.channel.id != voice_channel.id:
                    await voice_client.move_to(voice_channel)
        except asyncio.TimeoutError:
            # Voice connection timed out - likely network/firewall issue
            await interaction.followup.send(
                '❌ Failed to connect to voice: Connection timed out.\n'
                'This usually means UDP traffic is blocked by the hosting provider.\n'
                'Voice connections require UDP ports to be open.',
                ephemeral=True
            )
            return
        except Exception as e:
            # Detect common missing dependency error (PyNaCl) and provide actionable advice
            err_text = str(e)
            if 'PyNaCl' in err_text or 'pynacl' in err_text.lower():
                await interaction.followup.send(
                    'Failed to connect to voice channel: PyNaCl is required for voice support.\n'
                    'Install it with `pip install pynacl` (on Windows: `python -m pip install pynacl`).\n'
                    'Also ensure ffmpeg is installed and available on PATH for audio playback.',
                    ephemeral=True,
                )
            else:
                await interaction.followup.send(f'❌ Failed to connect to voice channel: {e}', ephemeral=True)
            return

        # Try to find a local file matching the query
        local_path = None
        search_names = [query]
        # Also try common extensions
        exts = ['.mp3', '.wav', '.m4a', '.ogg']
        for ext in exts:
            search_names.append(query + ext)

        base = pathlib.Path('.')
        for name in search_names:
            p = base / name
            if p.exists() and p.is_file():
                local_path = str(p.resolve())
                break

        # If no local file found, and yt_dlp is available, try streaming from YouTube search
        stream_url = None
        track_title = None
        track_webpage = None
        track_thumbnail = None
        if local_path is None:
            # Always use background fetch to avoid blocking the event loop (keeps bot responsive)
            # Fetch metadata in background thread
            try:
                metadata = await self._fetch_metadata_in_background(query)
                if metadata:
                    stream_url = metadata.get('stream_url')
                    track_title = metadata.get('title')
                    track_webpage = metadata.get('webpage')
                    track_thumbnail = metadata.get('thumbnail')
                else:
                    # Fetch returned empty - set placeholder
                    track_title = query
            except Exception:
                # Fetch failed - set placeholder
                track_title = query
                stream_url = None

        # Helper to send a message or embed, using followup if the initial response was already used
        async def _safe_reply(content: str | None = None, *, embed: discord.Embed | None = None, ephemeral: bool = True, view: discord.ui.View | None = None):
            try:
                if not interaction.response.is_done():
                    await interaction.response.send_message(content, embed=embed, ephemeral=ephemeral, view=view)
                else:
                    await interaction.followup.send(content, embed=embed, ephemeral=ephemeral, view=view)
            except Exception:
                # If this fails, there's not much we can do; swallow to avoid crash
                pass

        # Prepare source / handle queueing when already playing
        try:
            # Prepare friendly metadata for either playing now or queueing
            if local_path is not None:
                display_title = pathlib.Path(local_path).name
                source_url = None
                thumbnail = None
            else:
                display_title = track_title or query
                source_url = track_webpage
                thumbnail = track_thumbnail

            # If something is already playing, save this request to a simple queue on the voice client
            if voice_client.is_playing():
                # attach a queue list to the voice client if missing
                if not hasattr(voice_client, 'queue') or voice_client.queue is None:
                    voice_client.queue = []

                # store minimal info needed for later playback or display
                item = {
                    'local_path': local_path,
                    'stream_url': stream_url,
                    'title': display_title,
                    'webpage': track_webpage,
                    'thumbnail': track_thumbnail,
                    'requester': getattr(interaction, 'user', None),
                    # channel id where the play command was invoked; used to send now-playing embeds for queued tracks
                    'channel_id': getattr(interaction.channel, 'id', None),
                    'query': query,  # Store original query for background fetch
                }
                voice_client.queue.append(item)

                # If metadata wasn't fetched yet (stream_url is None), schedule background fetch
                if local_path is None and stream_url is None:
                    async def _fetch_and_update():
                        try:
                            metadata = await self._fetch_metadata_in_background(query)
                            if metadata:
                                # Update the queued item in-place
                                item['stream_url'] = metadata.get('stream_url') or item.get('stream_url')
                                item['title'] = metadata.get('title') or item.get('title')
                                item['webpage'] = metadata.get('webpage') or item.get('webpage')
                                item['thumbnail'] = metadata.get('thumbnail') or item.get('thumbnail')
                        except Exception:
                            pass  # Silently ignore fetch errors
                    
                    # Schedule background fetch (fire-and-forget)
                    asyncio.create_task(_fetch_and_update())

                # send an embed confirming item was added to queue
                q_embed = discord.Embed(title="<a:music:1425403164688908299> Added to queue", description=f"{display_title}", color=discord.Color.blurple())
                if source_url:
                    q_embed.add_field(name="Source", value=f"[Link]({source_url})", inline=False)
                try:
                    requester = interaction.user
                    q_embed.set_footer(text=f"Queued by {requester.display_name}")
                except Exception:
                    pass
                if thumbnail:
                    try:
                        q_embed.set_thumbnail(url=thumbnail)
                    except Exception:
                        pass

                # Try to respond to the interaction or followup. If that fails, fall back to sending
                # directly in the invocation channel or system channel so the user sees confirmation.
                try:
                    if not interaction.response.is_done():
                        await interaction.response.send_message(None, embed=q_embed, ephemeral=False)
                    else:
                        try:
                            await interaction.followup.send(embed=q_embed, ephemeral=False)
                        except Exception:
                            # fallback: try sending to the original channel
                            try:
                                chan = getattr(interaction, 'channel', None)
                                if chan is not None and chan.permissions_for(interaction.guild.me).send_messages:
                                    await chan.send(embed=q_embed)
                                else:
                                    g = getattr(interaction, 'guild', None)
                                    if g and g.system_channel and g.system_channel.permissions_for(g.me).send_messages:
                                        await g.system_channel.send(embed=q_embed)
                            except Exception:
                                # final fallback: attempt a short text followup
                                try:
                                    await interaction.followup.send(f'<a:music:1425403164688908299> Added to queue: {display_title}', ephemeral=False)
                                except Exception:
                                    pass
                except Exception:
                    # If all else fails, try a minimal text-only response so the client doesn't stay thinking
                    try:
                        if not interaction.response.is_done():
                            await interaction.response.send_message(f'<a:music:1425403164688908299> Added to queue: {display_title}', ephemeral=False)
                        else:
                            await interaction.followup.send(f'<a:music:1425403164688908299> Added to queue: {display_title}', ephemeral=False)
                    except Exception:
                        # Give up silently; we don't want to raise here
                        pass
                return

            # Not playing: prepare ffmpeg source and start playback (unchanged behaviour)
            # Check that we have something to play
            if local_path is None and stream_url is None:
                msg = '<a:warning:1424944783587147868> No local audio file found and streaming dependencies are not available or the query returned nothing. Place a file in the bot folder or install `yt_dlp`+`ffmpeg` for streaming.'
                try:
                    if not interaction.response.is_done():
                        await interaction.response.send_message(msg, ephemeral=True)
                    else:
                        await interaction.followup.send(msg, ephemeral=True)
                except Exception:
                    pass
                return

            try:
                if local_path is not None:
                    source = discord.FFmpegPCMAudio(local_path, **FFMPEG_OPTIONS)
                else:
                    # stream_url may be a webpage URL; FFmpeg can accept it via yt-dlp's output if direct stream is not provided
                    source = discord.FFmpegPCMAudio(stream_url, **FFMPEG_OPTIONS)
            except discord.errors.ClientException as ce:
                # Typical message: 'ffmpeg was not found.' — give the user instructions
                msg = (
                    "Failed to prepare audio: ffmpeg was not found on the system.\n"
                    "Install ffmpeg and ensure `ffmpeg` is available on your PATH.\n"
                    "On Windows, download from https://www.gyan.dev/ffmpeg/builds/ and add the `bin` folder to PATH."
                )
                await _safe_reply(msg, ephemeral=True)
                return

            # after callback schedules next queued track when this one finishes
            def _after(err):
                try:
                    asyncio.run_coroutine_threadsafe(self._play_next(voice_client), self.bot.loop)
                except Exception:
                    pass

            voice_client.play(source, after=_after)

            embed = discord.Embed(title="<a:music:1425403164688908299> Now playing", description=f"{display_title}", color=discord.Color.blurple())
            if source_url:
                embed.add_field(name="Source", value=f"[Link]({source_url})", inline=False)
            try:
                requester = interaction.user
                embed.set_footer(text=f"Requested by {requester.display_name}")
            except Exception:
                pass
            if thumbnail:
                try:
                    embed.set_thumbnail(url=thumbnail)
                except Exception:
                    pass

            try:
                view = PauseResumeView(voice_client)
                await _safe_reply(None, embed=embed, ephemeral=False, view=view)
            except Exception:
                # Fallback: send text-only reply
                await _safe_reply(f'<a:music:1425403164688908299> Now playing: {display_title}', ephemeral=False)
        except Exception as e:
            await _safe_reply(f'<a:warning:1424944783587147868> Failed to play audio: {e}', ephemeral=True)
            return


async def setup(bot: commands.Bot):
    await bot.add_cog(PlayCog(bot))