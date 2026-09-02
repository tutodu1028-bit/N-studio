"""
Bot Discord - point d'entree.
Lance avec :  python bot.py
"""

import asyncio
import logging
import os
from pathlib import Path

import discord
from discord.ext import commands
from dotenv import load_dotenv

# ---------------------------------------------------------------- config
load_dotenv()  # lit le fichier .env

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = os.getenv("GUILD_ID")  # optionnel : sync instantanee des commandes

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("bot")

# ---------------------------------------------------------------- intents
# ATTENTION : "Server Members Intent" et "Message Content Intent" doivent etre
# actives sur https://discord.com/developers/applications > ton app > Bot
intents = discord.Intents.default()
intents.members = True
intents.message_content = True


class MonBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="!",
            intents=intents,
            help_command=None,
            activity=discord.Game(name="fait des script pour vous"),
        )

    async def setup_hook(self):
        # Charge tous les cogs du dossier cogs/
        for fichier in sorted(Path("cogs").glob("*.py")):
            if fichier.stem.startswith("_"):
                continue
            await self.load_extension(f"cogs.{fichier.stem}")
            log.info("Cog charge : %s", fichier.stem)

        # Synchronise les commandes slash
        if GUILD_ID:
            guild = discord.Object(id=int(GUILD_ID))
            self.tree.copy_global_to(guild=guild)
            synced = await self.tree.sync(guild=guild)
            log.info("%d commandes synchronisees sur le serveur %s", len(synced), GUILD_ID)
        else:
            synced = await self.tree.sync()
            log.info("%d commandes globales synchronisees (jusqu'a 1h de delai)", len(synced))

    async def on_ready(self):
        log.info("Connecte en tant que %s (id=%s)", self.user, self.user.id)
        log.info("Present sur %d serveur(s)", len(self.guilds))


async def main():
    if not TOKEN:
        raise SystemExit(
            "DISCORD_TOKEN manquant. Copie .env.example en .env et colle ton token dedans."
        )
    bot = MonBot()
    async with bot:
        await bot.start(TOKEN)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log.info("Arret du bot.")
