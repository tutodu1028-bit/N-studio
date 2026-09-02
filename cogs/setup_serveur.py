"""/setup-serveur : construit automatiquement la structure d'un serveur.

Cree les roles, les categories et les salons, avec les permissions qui vont bien.
Ne supprime jamais rien : ce qui existe deja est reutilise.
"""

import discord
from discord import app_commands
from discord.ext import commands

# ------------------------------------------------------------------ modele
ROLES = [
    # (nom, couleur, permissions supplementaires, affiche separement)
    # L'ordre de cette liste = l'ordre de la hierarchie, du plus haut au plus bas.
    ("Owner", discord.Color.from_str("#E74C3C"), discord.Permissions(administrator=True), True),
    ("Bot", discord.Color.from_str("#5865F2"), discord.Permissions.none(), True),
    (
        "Staff",
        discord.Color.from_str("#E67E22"),
        discord.Permissions(
            kick_members=True,
            ban_members=True,
            manage_messages=True,
            moderate_members=True,
            manage_channels=True,
        ),
        True,
    ),
    ("Client", discord.Color.from_str("#1ABC9C"), discord.Permissions.none(), True),
    ("Partenaires", discord.Color.from_str("#F1C40F"), discord.Permissions.none(), True),
    ("Membre", discord.Color.from_str("#95A5A6"), discord.Permissions.none(), False),
]

STRUCTURE = [
    {
        "categorie": "📌 INFORMATIONS",
        "lecture_seule": True,
        "salons": [
            ("📜・reglement", "text", "Les regles du serveur."),
            ("📢・annonces", "text", "Les annonces importantes."),
            ("🎭・roles", "text", "Choisis tes roles ici."),
        ],
    },
    {
        "categorie": "💬 GENERAL",
        "lecture_seule": False,
        "salons": [
            ("💬・general", "text", "Discussion generale."),
            ("😂・memes", "text", "Images et memes."),
            ("🎁・free-script", "text", "Scripts gratuits a telecharger."),
        ],
    },
    {
        "categorie": "🔉 VOCAL",
        "lecture_seule": False,
        "salons": [
            ("🔈 Salon vocal 1", "voice", None),
            ("🎮 Salon vocal 2", "voice", None),
        ],
    },
    {
        "categorie": "💼 ESPACE CLIENT",
        "lecture_seule": False,
        "prive": True,
        "acces": ["Client"],  # en plus de Owner et Staff, toujours inclus
        "salons": [
            ("🛒・commandes", "text", "Passe et suis tes commandes."),
            ("📈・suivi-projet", "text", "Avancement des projets en cours."),
            ("📦・livraisons", "text", "Reception des fichiers finaux."),
            ("🎧 Point client", "voice", None),
        ],
    },
    {
        "categorie": "🤝 PARTENAIRES",
        "lecture_seule": False,
        "prive": True,
        "acces": ["Partenaires"],
        "salons": [
            ("🤝・partenariats", "text", "Discussions entre partenaires."),
            ("🚀・collaborations", "text", "Projets menes ensemble."),
        ],
    },
    {
        "categorie": "🔒 STAFF",
        "lecture_seule": False,
        "prive": True,
        "salons": [
            ("🛠️・staff-discussion", "text", "Salon prive du staff."),
            ("📋・logs", "text", "Journal des actions de moderation."),
        ],
    },
]

# Anciens noms -> nouveaux noms. Evite de creer des doublons quand on relance
# la commande apres avoir change les libelles.
RENOMMAGES = {
    "INFORMATIONS": "📌 INFORMATIONS",
    "GENERAL": "💬 GENERAL",
    "VOCAL": "🔉 VOCAL",
    "ESPACE CLIENT": "💼 ESPACE CLIENT",
    "PARTENAIRES": "🤝 PARTENAIRES",
    "STAFF": "🔒 STAFF",
    "reglement": "📜・reglement",
    "annonces": "📢・annonces",
    "roles": "🎭・roles",
    "general": "💬・general",
    "memes": "😂・memes",
    "Salon vocal 1": "🔈 Salon vocal 1",
    "Salon vocal 2": "🎮 Salon vocal 2",
    "commandes": "🛒・commandes",
    "suivi-projet": "📈・suivi-projet",
    "livraisons": "📦・livraisons",
    "Point client": "🎧 Point client",
    "partenariats": "🤝・partenariats",
    "collaborations": "🚀・collaborations",
    "staff-discussion": "🛠️・staff-discussion",
    "logs": "📋・logs",
}

# Salons retires de la structure : supprimes s'ils existent encore.
SUPPRIMER = ["bot-commandes"]


class SetupServeur(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="setup-serveur",
        description="Cree automatiquement roles, categories et salons",
    )
    @app_commands.describe(
        confirmer="Coche pour lancer reellement la creation",
    )
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.checks.bot_has_permissions(manage_channels=True, manage_roles=True)
    async def setup_serveur(self, interaction: discord.Interaction, confirmer: bool = False):
        if not confirmer:
            apercu = "\n".join(
                f"**{bloc['categorie']}** : "
                + ", ".join(f"`{n}`" for n, _, _ in bloc["salons"])
                for bloc in STRUCTURE
            )
            avertissement = ""
            presents = [
                n for n in SUPPRIMER
                if discord.utils.get(interaction.guild.channels, name=n)
            ]
            if presents:
                avertissement = (
                    "\n\n**Sera supprime** : "
                    + ", ".join(f"`{n}`" for n in presents)
                    + " (avec son historique de messages)"
                )
            return await interaction.response.send_message(
                "Voici la structure cible. L'existant est renomme, jamais duplique :\n\n"
                f"Roles : {', '.join(f'`{r[0]}`' for r in ROLES)}\n\n{apercu}"
                f"{avertissement}\n\n"
                "Relance la commande avec `confirmer: True` pour lancer.",
                ephemeral=True,
            )

        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild
        journal = []

        # ------------------------------------------------------- migration
        # Renomme l'existant vers les nouveaux libelles avant toute creation,
        # sinon on se retrouverait avec deux fois chaque salon.
        for ancien, nouveau in RENOMMAGES.items():
            if discord.utils.get(guild.channels, name=nouveau):
                continue  # deja au bon nom
            salon = discord.utils.get(guild.channels, name=ancien)
            if salon:
                await salon.edit(name=nouveau, reason="setup-serveur : renommage")
                journal.append(f"Renomme : {ancien} -> {nouveau}")

        # Supprime les salons retires de la structure.
        for nom in SUPPRIMER:
            salon = discord.utils.get(guild.channels, name=nom)
            if salon:
                await salon.delete(reason="setup-serveur : retire de la structure")
                journal.append(f"Salon supprime : {nom}")

        # --------------------------------------------------------- roles
        roles_crees: dict[str, discord.Role] = {}
        for nom, couleur, perms, hoist in ROLES:
            role = discord.utils.get(guild.roles, name=nom)
            if role is None:
                role = await guild.create_role(
                    name=nom, colour=couleur, permissions=perms, hoist=hoist,
                    reason="setup-serveur",
                )
                journal.append(f"Role cree : {nom}")
            else:
                journal.append(f"Role deja present : {nom}")
            roles_crees[nom] = role

        # Remet la hierarchie dans l'ordre de la liste ROLES (le plus haut d'abord).
        # Discord interdit de deplacer un role au-dessus du role du bot : dans ce
        # cas on prévient au lieu de planter.
        try:
            sous_le_bot = guild.me.top_role.position
            positions = {
                roles_crees[nom]: max(1, sous_le_bot - 1 - i)
                for i, (nom, *_) in enumerate(ROLES)
            }
            await guild.edit_role_positions(positions=positions, reason="setup-serveur")
            journal.append("Hierarchie des roles reordonnee")
        except discord.Forbidden:
            journal.append(
                "Hierarchie non modifiee (role du bot trop bas) - a ranger a la main"
            )

        everyone = guild.default_role
        staff = [roles_crees["Owner"], roles_crees["Staff"]]

        # --------------------------------------------------------- salons
        for bloc in STRUCTURE:
            nom_cat = bloc["categorie"]
            categorie = discord.utils.get(guild.categories, name=nom_cat)

            overwrites = {}
            if bloc.get("prive"):
                overwrites[everyone] = discord.PermissionOverwrite(view_channel=False)
                autorises = list(staff) + [
                    roles_crees[nom] for nom in bloc.get("acces", [])
                ]
                for r in autorises:
                    overwrites[r] = discord.PermissionOverwrite(view_channel=True)
            elif bloc.get("lecture_seule"):
                overwrites[everyone] = discord.PermissionOverwrite(
                    send_messages=False, add_reactions=False
                )
                for r in staff:
                    overwrites[r] = discord.PermissionOverwrite(send_messages=True)

            if categorie is None:
                categorie = await guild.create_category(
                    nom_cat, overwrites=overwrites, reason="setup-serveur"
                )
                journal.append(f"Categorie creee : {nom_cat}")

            for nom_salon, type_salon, sujet in bloc["salons"]:
                existant = discord.utils.get(guild.channels, name=nom_salon)
                if existant:
                    continue
                if type_salon == "voice":
                    await guild.create_voice_channel(
                        nom_salon, category=categorie, reason="setup-serveur"
                    )
                else:
                    await guild.create_text_channel(
                        nom_salon, category=categorie, topic=sujet,
                        reason="setup-serveur",
                    )
                journal.append(f"Salon cree : {nom_salon}")

        resume = "\n".join(journal) or "Rien a faire, tout existait deja."
        await interaction.followup.send(f"**Terminé.**\n```\n{resume[:1800]}\n```", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(SetupServeur(bot))
