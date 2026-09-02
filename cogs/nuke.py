"""/nuke : supprime tous les salons et tous les roles du serveur.

Commande volontairement bardee de garde-fous : reservee au proprietaire du
serveur, elle exige de retaper le nom exact du serveur pour s'executer.
Aucune de ces suppressions n'est reversible cote Discord.
"""

import discord
from discord import app_commands
from discord.ext import commands


class Nuke(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ------------------------------------------------------------ helpers
    @staticmethod
    def _roles_supprimables(guild: discord.Guild) -> list[discord.Role]:
        """Roles que le bot peut reellement supprimer.

        Sont exclus : @everyone (indestructible), les roles geres par une
        integration (bots, boost Nitro) que Discord refuse de supprimer, et
        tout ce qui est au niveau du role du bot ou au-dessus.
        """
        plafond = guild.me.top_role
        return [
            r
            for r in guild.roles
            if not r.is_default() and not r.managed and r < plafond
        ]

    # ------------------------------------------------------------ nuke
    @app_commands.command(
        name="nuke",
        description="DANGER : supprime TOUS les salons et TOUS les roles du serveur",
    )
    @app_commands.describe(
        confirmation="Retape le nom EXACT du serveur pour lancer (vide = apercu)",
    )
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.checks.bot_has_permissions(manage_channels=True, manage_roles=True)
    async def nuke(
        self, interaction: discord.Interaction, confirmation: str = None
    ):
        guild = interaction.guild

        # Garde-fou 1 : le proprietaire du serveur, et personne d'autre.
        if interaction.user.id != guild.owner_id:
            return await interaction.response.send_message(
                "Commande reservee au proprietaire du serveur.", ephemeral=True
            )

        salons = list(guild.channels)
        roles = self._roles_supprimables(guild)
        intouchables = [
            r for r in guild.roles if not r.is_default() and r not in roles
        ]

        # Garde-fou 2 : sans le nom exact du serveur, on ne fait qu'afficher
        # l'ampleur des degats.
        if confirmation != guild.name:
            apercu = (
                f"**Cette commande est irreversible.**\n\n"
                f"Elle supprimerait maintenant :\n"
                f"- **{len(salons)}** salon(s) et categorie(s), avec tout "
                f"l'historique des messages\n"
                f"- **{len(roles)}** role(s)\n"
            )
            if intouchables:
                apercu += (
                    f"\nResteront en place (Discord l'impose) : "
                    + ", ".join(r.mention for r in intouchables[:10])
                    + ("..." if len(intouchables) > 10 else "")
                    + "\n"
                )
            apercu += (
                f"\nAucune de ces suppressions ne peut etre annulee. Il n'existe "
                f"pas de sauvegarde cote Discord.\n\n"
                f"Pour lancer pour de vrai, relance la commande avec "
                f"`confirmation:` suivi du nom exact du serveur :\n"
                f"```\n{guild.name}\n```"
            )
            return await interaction.response.send_message(apercu, ephemeral=True)

        await interaction.response.defer(ephemeral=True)

        # Le salon d'ou vient la commande va disparaitre aussi : on ouvre un DM
        # pour pouvoir rendre compte. Si les MP sont fermes, on epargne ce salon.
        try:
            dm = await interaction.user.create_dm()
            await dm.send(f"Nuke en cours sur **{guild.name}**...")
        except discord.HTTPException:
            dm = None

        courant = interaction.channel
        cibles = [c for c in salons if dm is not None or c != courant]

        salons_ok = salons_ko = 0
        for salon in cibles:
            try:
                await salon.delete(reason=f"/nuke par {interaction.user}")
                salons_ok += 1
            except discord.HTTPException:
                salons_ko += 1

        # Du plus bas au plus haut : evite de se retrouver bloque en cours de route.
        roles_ok = roles_ko = 0
        for role in sorted(roles, key=lambda r: r.position):
            try:
                await role.delete(reason=f"/nuke par {interaction.user}")
                roles_ok += 1
            except discord.HTTPException:
                roles_ko += 1

        rapport = (
            f"**Nuke termine sur {guild.name}.**\n"
            f"- Salons supprimes : {salons_ok}"
            + (f" ({salons_ko} echec(s))" if salons_ko else "")
            + "\n"
            f"- Roles supprimes : {roles_ok}"
            + (f" ({roles_ko} echec(s))" if roles_ko else "")
            + "\n"
        )
        if dm is None:
            rapport += f"\nLe salon {courant.mention} a ete epargne (MP fermes)."
        if intouchables:
            rapport += (
                "\nRoles conserves car geres par Discord ou trop hauts : "
                + ", ".join(r.name for r in intouchables)
            )

        if dm is not None:
            await dm.send(rapport)
        else:
            await interaction.followup.send(rapport, ephemeral=True)

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
    await bot.add_cog(Nuke(bot))
