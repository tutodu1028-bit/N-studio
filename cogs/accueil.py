"""Message de bienvenue + role automatique a l'arrivee.

La config est stockee dans config.json (cree automatiquement).
"""

import json
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


class Accueil(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ------------------------------------------------------------ evenements
    @commands.Cog.listener()
    async def on_member_join(self, membre: discord.Member):
        conf = charger().get(str(membre.guild.id), {})

        # Role automatique
        role_id = conf.get("role_auto")
        if role_id:
            role = membre.guild.get_role(role_id)
            if role and role < membre.guild.me.top_role:
                try:
                    await membre.add_roles(role, reason="Role automatique a l'arrivee")
                except discord.Forbidden:
                    pass

        # Message de bienvenue
        salon_id = conf.get("salon_bienvenue")
        if salon_id:
            salon = membre.guild.get_channel(salon_id)
            if salon:
                embed = discord.Embed(
                    title="Bienvenue !",
                    description=conf.get(
                        "message_bienvenue", "Bienvenue {membre} sur **{serveur}** !"
                    ).format(membre=membre.mention, serveur=membre.guild.name),
                    color=discord.Color.green(),
                )
                embed.set_thumbnail(url=membre.display_avatar.url)
                embed.set_footer(text=f"Membre n°{membre.guild.member_count}")
                try:
                    await salon.send(embed=embed)
                except discord.Forbidden:
                    pass

    @commands.Cog.listener()
    async def on_member_remove(self, membre: discord.Member):
        conf = charger().get(str(membre.guild.id), {})
        salon_id = conf.get("salon_bienvenue")
        if salon_id:
            salon = membre.guild.get_channel(salon_id)
            if salon:
                try:
                    await salon.send(f"**{membre}** a quitte le serveur.")
                except discord.Forbidden:
                    pass

    # ------------------------------------------------------------ config
    @app_commands.command(
        name="config-accueil", description="Configure le salon et le role d'accueil"
    )
    @app_commands.describe(
        salon="Salon ou envoyer les messages de bienvenue",
        role="Role donne automatiquement aux nouveaux membres",
        message="Message perso. Variables : {membre} et {serveur}",
    )
    @app_commands.checks.has_permissions(manage_guild=True)
    async def config_accueil(
        self,
        interaction: discord.Interaction,
        salon: discord.TextChannel = None,
        role: discord.Role = None,
        message: str = None,
    ):
        data = charger()
        gid = str(interaction.guild_id)
        conf = data.setdefault(gid, {})

        if salon:
            conf["salon_bienvenue"] = salon.id
        if role:
            conf["role_auto"] = role.id
        if message:
            conf["message_bienvenue"] = message
        sauvegarder(data)

        await interaction.response.send_message(
            "Configuration enregistree :\n"
            f"- Salon : {salon.mention if salon else 'inchange'}\n"
            f"- Role auto : {role.mention if role else 'inchange'}\n"
            f"- Message : {message or 'inchange'}",
            ephemeral=True,
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(Accueil(bot))
