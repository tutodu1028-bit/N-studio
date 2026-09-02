"""Commandes de moderation : /kick, /ban, /unban, /timeout, /clear, /slowmode."""

import datetime

import discord
from discord import app_commands
from discord.ext import commands


class Moderation(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ------------------------------------------------------------ helpers
    @staticmethod
    def _peut_agir(auteur: discord.Member, cible: discord.Member) -> str | None:
        """Retourne un message d'erreur si l'action est interdite, sinon None."""
        if cible == auteur:
            return "Tu ne peux pas faire ca sur toi-meme."
        if cible == auteur.guild.owner:
            return "Impossible : c'est le proprietaire du serveur."
        if auteur.top_role <= cible.top_role and auteur != auteur.guild.owner:
            return "Cette personne a un role egal ou superieur au tien."
        if cible.top_role >= cible.guild.me.top_role:
            return "Mon role est trop bas pour agir sur cette personne."
        return None

    # ------------------------------------------------------------ kick
    @app_commands.command(name="kick", description="Expulse un membre")
    @app_commands.describe(membre="Membre a expulser", raison="Raison de l'expulsion")
    @app_commands.checks.has_permissions(kick_members=True)
    @app_commands.checks.bot_has_permissions(kick_members=True)
    async def kick(
        self,
        interaction: discord.Interaction,
        membre: discord.Member,
        raison: str = "Aucune raison fournie",
    ):
        erreur = self._peut_agir(interaction.user, membre)
        if erreur:
            return await interaction.response.send_message(erreur, ephemeral=True)
        await membre.kick(reason=f"{interaction.user} : {raison}")
        await interaction.response.send_message(
            f"**{membre}** a ete expulse. Raison : {raison}"
        )

    # ------------------------------------------------------------ ban
    @app_commands.command(name="ban", description="Bannit un membre")
    @app_commands.describe(
        membre="Membre a bannir",
        raison="Raison du bannissement",
        jours_messages="Supprimer les messages des N derniers jours (0-7)",
    )
    @app_commands.checks.has_permissions(ban_members=True)
    @app_commands.checks.bot_has_permissions(ban_members=True)
    async def ban(
        self,
        interaction: discord.Interaction,
        membre: discord.Member,
        raison: str = "Aucune raison fournie",
        jours_messages: app_commands.Range[int, 0, 7] = 0,
    ):
        erreur = self._peut_agir(interaction.user, membre)
        if erreur:
            return await interaction.response.send_message(erreur, ephemeral=True)
        await membre.ban(
            reason=f"{interaction.user} : {raison}",
            delete_message_seconds=jours_messages * 86400,
        )
        await interaction.response.send_message(
            f"**{membre}** a ete banni. Raison : {raison}"
        )

    # ------------------------------------------------------------ unban
    @app_commands.command(name="unban", description="Debannit un utilisateur par son ID")
    @app_commands.checks.has_permissions(ban_members=True)
    async def unban(self, interaction: discord.Interaction, user_id: str):
        try:
            user = await self.bot.fetch_user(int(user_id))
            await interaction.guild.unban(user)
        except (ValueError, discord.NotFound):
            return await interaction.response.send_message(
                "ID invalide ou utilisateur non banni.", ephemeral=True
            )
        await interaction.response.send_message(f"**{user}** a ete debanni.")

    # ------------------------------------------------------------ timeout
    @app_commands.command(name="timeout", description="Rend un membre muet temporairement")
    @app_commands.describe(minutes="Duree en minutes (max 40320 = 28 jours)")
    @app_commands.checks.has_permissions(moderate_members=True)
    @app_commands.checks.bot_has_permissions(moderate_members=True)
    async def timeout(
        self,
        interaction: discord.Interaction,
        membre: discord.Member,
        minutes: app_commands.Range[int, 1, 40320],
        raison: str = "Aucune raison fournie",
    ):
        erreur = self._peut_agir(interaction.user, membre)
        if erreur:
            return await interaction.response.send_message(erreur, ephemeral=True)
        duree = datetime.timedelta(minutes=minutes)
        await membre.timeout(duree, reason=f"{interaction.user} : {raison}")
        fin = discord.utils.utcnow() + duree
        await interaction.response.send_message(
            f"**{membre}** est muet jusqu'a {discord.utils.format_dt(fin, 'R')}. "
            f"Raison : {raison}"
        )

    # ------------------------------------------------------------ clear
    @app_commands.command(name="clear", description="Supprime des messages du salon")
    @app_commands.describe(
        nombre="Nombre de messages a supprimer (1-100)",
        membre="Ne supprimer que les messages de ce membre",
    )
    @app_commands.checks.has_permissions(manage_messages=True)
    @app_commands.checks.bot_has_permissions(manage_messages=True)
    async def clear(
        self,
        interaction: discord.Interaction,
        nombre: app_commands.Range[int, 1, 100],
        membre: discord.Member = None,
    ):
        await interaction.response.defer(ephemeral=True)
        verif = (lambda m: m.author == membre) if membre else None
        supprimes = await interaction.channel.purge(limit=nombre, check=verif)
        await interaction.followup.send(
            f"{len(supprimes)} message(s) supprime(s).", ephemeral=True
        )

    # ------------------------------------------------------------ slowmode
    @app_commands.command(name="slowmode", description="Definit le mode lent du salon")
    @app_commands.describe(secondes="Delai entre messages (0 = desactive, max 21600)")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def slowmode(
        self, interaction: discord.Interaction, secondes: app_commands.Range[int, 0, 21600]
    ):
        await interaction.channel.edit(slowmode_delay=secondes)
        if secondes:
            await interaction.response.send_message(f"Mode lent : {secondes}s.")
        else:
            await interaction.response.send_message("Mode lent desactive.")

    # ------------------------------------------------------------ erreurs
    async def cog_app_command_error(
        self, interaction: discord.Interaction, error: app_commands.AppCommandError
    ):
        if isinstance(error, app_commands.MissingPermissions):
            msg = "Tu n'as pas la permission d'utiliser cette commande."
        elif isinstance(error, app_commands.BotMissingPermissions):
            msg = "Il me manque une permission pour faire ca."
        else:
            msg = f"Erreur : {error}"
        if interaction.response.is_done():
            await interaction.followup.send(msg, ephemeral=True)
        else:
            await interaction.response.send_message(msg, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Moderation(bot))
