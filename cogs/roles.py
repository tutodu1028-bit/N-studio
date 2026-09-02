"""Roles par reaction : /roles-reactions.

Cree un message ou chaque emoji donne un role. Fonctionne apres un redemarrage
du bot (la config est relue depuis config.json a chaque reaction).
"""

import json
import re
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands

CONFIG = Path("config.json")


def charger() -> dict:
    if CONFIG.exists():
        return json.loads(CONFIG.read_text(encoding="utf-8"))
    return {}


def sauvegarder(data: dict) -> None:
    CONFIG.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


class Roles(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="roles-reactions",
        description="Cree un message de roles a reaction",
    )
    @app_commands.describe(
        titre="Titre du message",
        paires="Format : emoji=@role, emoji=@role  (ex: 🎮=@Gamer, 🎵=@Musique)",
    )
    @app_commands.checks.has_permissions(manage_roles=True)
    @app_commands.checks.bot_has_permissions(manage_roles=True, add_reactions=True)
    async def roles_reactions(
        self, interaction: discord.Interaction, titre: str, paires: str
    ):
        entrees = []
        for morceau in paires.split(","):
            if "=" not in morceau:
                continue
            emoji, brut = (p.strip() for p in morceau.split("=", 1))
            match = re.search(r"\d{15,20}", brut)
            role = None
            if match:
                role = interaction.guild.get_role(int(match.group()))
            if role is None:
                role = discord.utils.get(
                    interaction.guild.roles, name=brut.lstrip("@").strip()
                )
            if role is None:
                return await interaction.response.send_message(
                    f"Role introuvable : `{brut}`", ephemeral=True
                )
            if role >= interaction.guild.me.top_role:
                return await interaction.response.send_message(
                    f"Mon role doit etre au-dessus de {role.mention}.", ephemeral=True
                )
            entrees.append((emoji, role))

        if not entrees:
            return await interaction.response.send_message(
                "Format invalide. Exemple : `🎮=@Gamer, 🎵=@Musique`", ephemeral=True
            )

        embed = discord.Embed(
            title=titre,
            description="\n".join(f"{e} → {r.mention}" for e, r in entrees),
            color=discord.Color.blurple(),
        )
        embed.set_footer(text="Ajoute une reaction pour obtenir le role, retire-la pour l'enlever.")

        await interaction.response.send_message("Message cree.", ephemeral=True)
        message = await interaction.channel.send(embed=embed)
        for emoji, _ in entrees:
            try:
                await message.add_reaction(emoji)
            except discord.HTTPException:
                pass

        data = charger()
        conf = data.setdefault(str(interaction.guild_id), {})
        conf.setdefault("roles_reactions", {})[str(message.id)] = {
            e: r.id for e, r in entrees
        }
        sauvegarder(data)

    # ------------------------------------------------------------ reactions
    async def _gerer(self, payload: discord.RawReactionActionEvent, ajouter: bool):
        if payload.guild_id is None:
            return
        conf = charger().get(str(payload.guild_id), {}).get("roles_reactions", {})
        mapping = conf.get(str(payload.message_id))
        if not mapping:
            return

        role_id = mapping.get(str(payload.emoji))
        if role_id is None:
            return

        guild = self.bot.get_guild(payload.guild_id)
        role = guild.get_role(role_id)
        membre = guild.get_member(payload.user_id)
        if role is None or membre is None or membre.bot:
            return

        try:
            if ajouter:
                await membre.add_roles(role, reason="Role par reaction")
            else:
                await membre.remove_roles(role, reason="Role par reaction")
        except discord.Forbidden:
            pass

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        await self._gerer(payload, ajouter=True)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        await self._gerer(payload, ajouter=False)


async def setup(bot: commands.Bot):
    await bot.add_cog(Roles(bot))
