# Bot Discord — guide de démarrage

Bot en Python (discord.py) avec commandes slash, modération, accueil automatique,
rôles par réaction et une commande qui construit la structure du serveur.

---

## 1. Créer le bot et récupérer le token

1. Va sur https://discord.com/developers/applications → **New Application**.
2. Onglet **Bot** → **Reset Token** → **Copy**. C'est ton token.
   ⚠️ Ce token est un mot de passe : ne le poste jamais nulle part.
   Si tu l'as déjà partagé, clique sur **Reset Token** pour l'invalider.
3. Toujours dans l'onglet **Bot**, active les deux interrupteurs :
   - **SERVER MEMBERS INTENT**
   - **MESSAGE CONTENT INTENT**

## 2. Inviter le bot sur ton serveur

Onglet **OAuth2 → URL Generator** :

- Scopes : `bot` + `applications.commands`
- Bot Permissions : `Administrator` (le plus simple pour commencer)

Copie l'URL générée en bas, ouvre-la, choisis ton serveur.

> Dans **Paramètres du serveur → Rôles**, remonte le rôle du bot au-dessus des
> rôles qu'il doit gérer, sinon il ne pourra pas les attribuer.

## 3. Installer et lancer

```bash
cd discord-bot
python -m venv .venv
source .venv/bin/activate        # Windows : .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env             # Windows : copy .env.example .env
# ouvre .env et colle ton token

python bot.py
```

Tu dois voir `Connecte en tant que MonBot#1234`. C'est bon.

Pour récupérer ton `GUILD_ID` : active le **Mode développeur** dans les
paramètres Discord (Avancés), puis clic droit sur ton serveur → *Copier l'ID*.

---

## 4. Commandes

| Commande | Rôle requis | Description |
|---|---|---|
| `/ping` | — | Latence du bot |
| `/aide` | — | Liste des commandes |
| `/info [membre]` | — | Infos serveur ou membre |
| `/avatar [membre]` | — | Affiche un avatar |
| `/dis <texte>` | Gérer les messages | Fait parler le bot |
| `/kick <membre>` | Expulser | Expulse un membre |
| `/ban <membre>` | Bannir | Bannit un membre |
| `/unban <user_id>` | Bannir | Débannit par ID |
| `/timeout <membre> <minutes>` | Modérer | Rend muet temporairement |
| `/clear <nombre>` | Gérer les messages | Supprime des messages |
| `/slowmode <secondes>` | Gérer les salons | Mode lent du salon |
| `/config-accueil` | Gérer le serveur | Salon + rôle + message d'accueil |
| `/roles-reactions` | Gérer les rôles | Crée un message de rôles à réaction |
| `/setup-serveur` | Administrateur | Crée rôles, catégories et salons |

### Exemples

```
/config-accueil salon:#general role:@Membre message:Salut {membre}, bienvenue sur {serveur} !
/roles-reactions titre:Choisis tes rôles paires:🎮=@Gamer, 🎵=@Musique
/setup-serveur confirmer:True
```

`/setup-serveur` sans `confirmer` affiche un aperçu. Il ne supprime jamais rien :
ce qui existe déjà est conservé.

---

## 5. Le faire tourner 24/7

### Sur un VPS Linux (systemd)

Crée `/etc/systemd/system/discordbot.service` :

```ini
[Unit]
Description=Bot Discord
After=network-online.target

[Service]
Type=simple
User=TON_UTILISATEUR
WorkingDirectory=/chemin/vers/discord-bot
ExecStart=/chemin/vers/discord-bot/.venv/bin/python bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now discordbot
sudo journalctl -u discordbot -f    # voir les logs
```

### Sur Railway / Render / Fly.io

Mets le code sur GitHub (avec le `.gitignore` fourni, qui exclut `.env`),
connecte le dépôt, définis `DISCORD_TOKEN` en variable d'environnement,
et commande de démarrage : `python bot.py`.

---

## 6. Ajouter une commande

Crée un fichier dans `cogs/`, il sera chargé automatiquement au démarrage :

```python
import discord
from discord import app_commands
from discord.ext import commands

class MonCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="hello", description="Dit bonjour")
    async def hello(self, interaction: discord.Interaction):
        await interaction.response.send_message("Salut !")

async def setup(bot):
    await bot.add_cog(MonCog(bot))
```

Redémarre le bot : la commande apparaît.

---

## Problèmes courants

- **Les commandes slash n'apparaissent pas** → mets `GUILD_ID` dans `.env`
  (sync instantanée), et vérifie que le bot a bien le scope `applications.commands`.
- **`PrivilegedIntentsRequired`** → tu as oublié d'activer les intents à l'étape 1.3.
- **« Mon rôle est trop bas »** → remonte le rôle du bot dans la hiérarchie.
- **`ModuleNotFoundError`** → le venv n'est pas activé, ou `pip install` non fait.
