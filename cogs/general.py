"""Commandes generales : /ping, /aide, /info, /avatar, /dis."""

import time

import discord
from discord import app_commands
from discord.ext import commands


class General(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="ping", description="Affiche la latence du bot")
    async def ping(self, interaction: discord.Interaction):
        debut = time.perf_counter()
        await interaction.response.send_message("Mesure en cours...")
        aller_retour = (time.perf_counter() - debut) * 1000
        await interaction.edit_original_response(
            content=f"Pong. Websocket : `{self.bot.latency * 1000:.0f} ms` | "
                    f"Aller-retour : `{aller_retour:.0f} ms`"
        )

    @app_commands.command(name="aide", description="Liste les commandes disponibles")
    async def aide(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="Commandes disponibles",
            color=discord.Color.blurple(),
        )
        embed.add_field(
            name="General",
            value="`/ping` `/aide` `/info` `/avatar` `/dis`",
            inline=False,
        )
        embed.add_field(
            name="Moderation",
            value="`/kick` `/ban` `/unban` `/timeout` `/clear` `/slowmode`",
            inline=False,
        )
        embed.add_field(
            name="Configuration",
            value="`/setup-serveur` `/roles-reactions` `/config-accueil`\n"
                  "`/ticket-panel` `/config-ticket`",
            inline=False,
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="info", description="Infos sur le serveur ou un membre")
    @app_commands.describe(membre="Le membre a inspecter (vide = infos du serveur)")
    async def info(self, interaction: discord.Interaction, membre: discord.Member = None):
        if membre is None:
            g = interaction.guild
            embed = discord.Embed(title=g.name, color=discord.Color.blurple())
            if g.icon:
                embed.set_thumbnail(url=g.icon.url)
            embed.add_field(name="Membres", value=str(g.member_count))
            embed.add_field(name="Salons", value=str(len(g.channels)))
            embed.add_field(name="Roles", value=str(len(g.roles)))
            embed.add_field(name="Proprietaire", value=g.owner.mention if g.owner else "?")
            embed.add_field(
                name="Cree le", value=discord.utils.format_dt(g.created_at, "D")
            )
        else:
            embed = discord.Embed(title=str(membre), color=membre.color)
            embed.set_thumbnail(url=membre.display_avatar.url)
            embed.add_field(
                name="A rejoint le", value=discord.utils.format_dt(membre.joined_at, "D")
            )
            embed.add_field(
                name="Compte cree le",
                value=discord.utils.format_dt(membre.created_at, "D"),
            )
            roles = [r.mention for r in reversed(membre.roles) if r.name != "@everyone"]
            embed.add_field(
                name=f"Roles ({len(roles)})",
                value=" ".join(roles)[:1024] or "Aucun",
                inline=False,
            )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="avatar", description="Affiche l'avatar d'un membre")
    async def avatar(self, interaction: discord.Interaction, membre: discord.Member = None):
        membre = membre or interaction.user
        embed = discord.Embed(title=f"Avatar de {membre}", color=membre.color)
        embed.set_image(url=membre.display_avatar.url)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="dis", description="Fait parler le bot")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def dis(self, interaction: discord.Interaction, texte: str):
        await interaction.response.send_message("Envoye.", ephemeral=True)
        await interaction.channel.send(texte)


async def setup(bot: commands.Bot):
    await bot.add_cog(General(bot))
