"""Systeme de tickets : panneau a boutons + salons prives.

Un clic sur un bouton du panneau ouvre un salon prive visible par son auteur
et par le staff. La fermeture supprime le salon : il n'y a pas de transcript,
c'est un choix assume (voir _archiver() si tu changes d'avis un jour).

La config vit dans config.json, sous la cle "tickets" de chaque serveur.
Les vues sont persistantes : les boutons continuent de fonctionner apres un
redemarrage du bot.
"""

import json
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands

CONFIG = Path("config.json")

# Motifs proposes sur le panneau. La cle sert de prefixe au nom du salon.
MOTIFS = {
    "support": {
        "label": "Support",
        "emoji": "\N{BLACK QUESTION MARK ORNAMENT}",
        "style": discord.ButtonStyle.primary,
        "texte": "Une question, un souci, besoin d'un coup de main.",
    },
    "commande": {
        "label": "Commande / Devis",
        "emoji": "\N{SHOPPING TROLLEY}",
        "style": discord.ButtonStyle.success,
        "texte": "Demander un devis ou passer une commande.",
    },
    "partenariat": {
        "label": "Partenariat",
        "emoji": "\N{HANDSHAKE}",
        "style": discord.ButtonStyle.secondary,
        "texte": "Proposer un partenariat avec N-studio.",
    },
}


# ---------------------------------------------------------------- config
def charger() -> dict:
    if CONFIG.exists():
        return json.loads(CONFIG.read_text(encoding="utf-8"))
    return {}


def sauvegarder(data: dict) -> None:
    CONFIG.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def conf_tickets(guild_id: int) -> dict:
    return charger().get(str(guild_id), {}).get("tickets", {})


def maj_tickets(guild_id: int, **champs) -> dict:
    data = charger()
    t = data.setdefault(str(guild_id), {}).setdefault("tickets", {})
    t.update(champs)
    sauvegarder(data)
    return t


# ---------------------------------------------------------------- helpers
def _marqueur(auteur_id: int, cle: str) -> str:
    """Signature ecrite dans le topic du salon.

    On se sert du topic comme source de verite plutot que d'une liste dans
    config.json : si un salon est supprime a la main, rien ne se desynchronise.
    """
    return f"ticket:{cle}:{auteur_id}"


def _ticket_existant(
    categorie: discord.CategoryChannel, auteur_id: int, cle: str
) -> discord.TextChannel | None:
    signature = _marqueur(auteur_id, cle)
    for salon in categorie.text_channels:
        if salon.topic and salon.topic.startswith(signature):
            return salon
    return None


def _auteur_du_ticket(salon: discord.TextChannel) -> int | None:
    """Retrouve l'id de l'auteur depuis le topic, ou None si ce n'est pas un ticket."""
    if not salon.topic or not salon.topic.startswith("ticket:"):
        return None
    morceaux = salon.topic.split(":")
    if len(morceaux) < 3 or not morceaux[2].isdigit():
        return None
    return int(morceaux[2])


def _est_staff(membre: discord.Member, conf: dict) -> bool:
    if membre.guild_permissions.manage_guild:
        return True
    role_id = conf.get("role_staff")
    return bool(role_id) and any(r.id == role_id for r in membre.roles)


async def _archiver(salon: discord.TextChannel) -> None:
    """Point d'accroche si tu veux un jour un transcript avant suppression.

    Il suffirait de lire salon.history() et d'envoyer le resultat dans un salon
    de logs. Volontairement vide : la fermeture supprime, c'est le choix retenu.
    """
    return None


# ---------------------------------------------------------------- ouverture
async def ouvrir_ticket(interaction: discord.Interaction, cle: str) -> None:
    guild = interaction.guild
    conf = conf_tickets(guild.id)

    categorie = guild.get_channel(conf.get("categorie", 0))
    if not isinstance(categorie, discord.CategoryChannel):
        return await interaction.response.send_message(
            "Le systeme de tickets n'est pas encore configure. "
            "Un admin doit lancer `/config-ticket`.",
            ephemeral=True,
        )

    role_staff = guild.get_role(conf.get("role_staff", 0))

    deja = _ticket_existant(categorie, interaction.user.id, cle)
    if deja is not None:
        return await interaction.response.send_message(
            f"Tu as deja un ticket ouvert pour ce motif : {deja.mention}",
            ephemeral=True,
        )

    await interaction.response.defer(ephemeral=True)

    numero = conf.get("compteur", 0) + 1
    maj_tickets(guild.id, compteur=numero)

    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        interaction.user: discord.PermissionOverwrite(
            view_channel=True,
            send_messages=True,
            attach_files=True,
            read_message_history=True,
        ),
        guild.me: discord.PermissionOverwrite(
            view_channel=True,
            send_messages=True,
            manage_channels=True,
            read_message_history=True,
        ),
    }
    if role_staff is not None:
        overwrites[role_staff] = discord.PermissionOverwrite(
            view_channel=True,
            send_messages=True,
            attach_files=True,
            read_message_history=True,
        )

    try:
        salon = await guild.create_text_channel(
            f"{cle}-{numero:04d}",
            category=categorie,
            overwrites=overwrites,
            topic=_marqueur(interaction.user.id, cle),
            reason=f"Ticket ouvert par {interaction.user}",
        )
    except discord.Forbidden:
        return await interaction.followup.send(
            "Il me manque la permission de creer des salons dans cette categorie.",
            ephemeral=True,
        )
    except discord.HTTPException as erreur:
        # Cas classique : la categorie a atteint ses 50 salons.
        return await interaction.followup.send(
            f"Impossible de creer le salon : {erreur}", ephemeral=True
        )

    motif = MOTIFS[cle]
    embed = discord.Embed(
        title=f"Ticket #{numero:04d} - {motif['label']}",
        description=(
            f"{interaction.user.mention} a ouvert ce ticket.\n\n"
            "Decris ta demande le plus precisement possible, le staff repond ici.\n"
            "Le bouton ci-dessous ferme le ticket et **supprime definitivement "
            "ce salon**, conversation comprise."
        ),
        color=discord.Color.blurple(),
    )
    embed.set_footer(text=motif["texte"])

    mentions = interaction.user.mention
    if role_staff is not None:
        mentions += f" {role_staff.mention}"

    await salon.send(content=mentions, embed=embed, view=VueTicket())
    await interaction.followup.send(
        f"Ton ticket est ouvert : {salon.mention}", ephemeral=True
    )


# ---------------------------------------------------------------- vues
class BoutonMotif(discord.ui.Button):
    def __init__(self, cle: str, motif: dict):
        super().__init__(
            label=motif["label"],
            emoji=motif["emoji"],
            style=motif["style"],
            custom_id=f"ticket:ouvrir:{cle}",
        )
        self.cle = cle

    async def callback(self, interaction: discord.Interaction):
        await ouvrir_ticket(interaction, self.cle)


class VuePanneau(discord.ui.View):
    """Panneau public : un bouton par motif. Persistante (timeout=None)."""

    def __init__(self):
        super().__init__(timeout=None)
        for cle, motif in MOTIFS.items():
            self.add_item(BoutonMotif(cle, motif))


class VueConfirmation(discord.ui.View):
    """Deuxieme clic avant suppression. Ephemere, pas besoin d'etre persistante."""

    def __init__(self):
        super().__init__(timeout=60)

    @discord.ui.button(
        label="Oui, supprimer",
        emoji="\N{WASTEBASKET}",
        style=discord.ButtonStyle.danger,
    )
    async def oui(self, interaction: discord.Interaction, bouton: discord.ui.Button):
        salon = interaction.channel
        await interaction.response.edit_message(
            content="Suppression du ticket...", view=None
        )
        await _archiver(salon)
        try:
            await salon.delete(reason=f"Ticket ferme par {interaction.user}")
        except discord.Forbidden:
            await interaction.followup.send(
                "Il me manque la permission de supprimer ce salon.", ephemeral=True
            )

    @discord.ui.button(label="Annuler", style=discord.ButtonStyle.secondary)
    async def non(self, interaction: discord.Interaction, bouton: discord.ui.Button):
        await interaction.response.edit_message(content="Fermeture annulee.", view=None)


class VueTicket(discord.ui.View):
    """Bouton de fermeture, poste dans chaque salon de ticket. Persistante."""

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Fermer le ticket",
        emoji="\N{LOCK}",
        style=discord.ButtonStyle.danger,
        custom_id="ticket:fermer",
    )
    async def fermer(self, interaction: discord.Interaction, bouton: discord.ui.Button):
        conf = conf_tickets(interaction.guild_id)
        auteur_id = _auteur_du_ticket(interaction.channel)

        # Seuls l'auteur du ticket et le staff peuvent fermer.
        if interaction.user.id != auteur_id and not _est_staff(interaction.user, conf):
            return await interaction.response.send_message(
                "Seul l'auteur du ticket ou le staff peut le fermer.", ephemeral=True
            )

        await interaction.response.send_message(
            "Fermer ce ticket ? Le salon et **toute la conversation** seront "
            "supprimes definitivement, sans sauvegarde.",
            view=VueConfirmation(),
            ephemeral=True,
        )


# ---------------------------------------------------------------- cog
class Tickets(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_load(self):
        # Reenregistre les vues pour que les boutons deja postes repondent
        # encore apres un redemarrage du bot.
        self.bot.add_view(VuePanneau())
        self.bot.add_view(VueTicket())

    # ------------------------------------------------------------ config
    @app_commands.command(
        name="config-ticket",
        description="Configure la categorie et le role staff des tickets",
    )
    @app_commands.describe(
        categorie="Categorie ou seront crees les salons de ticket",
        role_staff="Role qui voit et gere tous les tickets",
    )
    @app_commands.checks.has_permissions(manage_guild=True)
    async def config_ticket(
        self,
        interaction: discord.Interaction,
        categorie: discord.CategoryChannel = None,
        role_staff: discord.Role = None,
    ):
        champs = {}
        if categorie is not None:
            champs["categorie"] = categorie.id
        if role_staff is not None:
            champs["role_staff"] = role_staff.id
        if champs:
            maj_tickets(interaction.guild_id, **champs)

        conf = conf_tickets(interaction.guild_id)
        cat = interaction.guild.get_channel(conf.get("categorie", 0))
        rle = interaction.guild.get_role(conf.get("role_staff", 0))

        await interaction.response.send_message(
            "Configuration des tickets :\n"
            f"- Categorie : {cat.mention if cat else '**non definie**'}\n"
            f"- Role staff : {rle.mention if rle else '**non defini**'}\n"
            f"- Tickets ouverts a ce jour : {conf.get('compteur', 0)}",
            ephemeral=True,
        )

    # ------------------------------------------------------------ panneau
    @app_commands.command(
        name="ticket-panel",
        description="Poste le panneau d'ouverture de tickets dans un salon",
    )
    @app_commands.describe(
        salon="Salon ou poster le panneau (vide = salon courant)",
        titre="Titre du panneau",
    )
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.checks.bot_has_permissions(manage_channels=True, manage_roles=True)
    async def ticket_panel(
        self,
        interaction: discord.Interaction,
        salon: discord.TextChannel = None,
        titre: str = "Ouvrir un ticket",
    ):
        conf = conf_tickets(interaction.guild_id)
        categorie = interaction.guild.get_channel(conf.get("categorie", 0))
        if not isinstance(categorie, discord.CategoryChannel):
            return await interaction.response.send_message(
                "Configure d'abord la categorie avec `/config-ticket`, "
                "sinon les boutons ne pourront rien creer.",
                ephemeral=True,
            )

        salon = salon or interaction.channel
        embed = discord.Embed(
            title=titre,
            description=(
                "Choisis le motif qui correspond a ta demande. "
                "Un salon prive sera cree, visible seulement par toi et le staff.\n\n"
                + "\n".join(
                    f"{m['emoji']} **{m['label']}** - {m['texte']}"
                    for m in MOTIFS.values()
                )
            ),
            color=discord.Color.blurple(),
        )
        embed.set_footer(text="Un ticket ouvert a la fois par motif.")

        try:
            await salon.send(embed=embed, view=VuePanneau())
        except discord.Forbidden:
            return await interaction.response.send_message(
                f"Je ne peux pas ecrire dans {salon.mention}.", ephemeral=True
            )

        await interaction.response.send_message(
            f"Panneau poste dans {salon.mention}.", ephemeral=True
        )

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
    await bot.add_cog(Tickets(bot))
