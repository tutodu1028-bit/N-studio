# Mettre le bot en ligne (le faire passer au vert)

Le point gris à côté de ton bot = le programme ne tourne nulle part.
Discord n'héberge pas les bots : il faut une machine qui exécute `python bot.py`
en permanence. Voici les options, de la plus simple à la plus solide.

---

## Option A — Railway (le plus simple depuis un téléphone)

1. Mets le code sur GitHub (le `.gitignore` fourni exclut déjà `.env`).
   Depuis un mobile : app **GitHub** → *New repository* → uploade les fichiers.
2. Va sur https://railway.app → *Login with GitHub*.
3. *New Project* → *Deploy from GitHub repo* → choisis ton dépôt.
4. Onglet **Variables** → ajoute :
   - `DISCORD_TOKEN` = ton nouveau token
   - `GUILD_ID` = 1544297452377612288
5. Onglet **Settings** → *Start Command* : `python bot.py`
6. Deploy. Regarde les logs : tu dois voir `Connecte en tant que N-studio#8836`.

Le plan gratuit offre un crédit mensuel limité — largement suffisant pour un
petit bot, mais surveille la consommation.

⚠️ Le fichier `config.json` (config d'accueil, rôles à réaction) est perdu à
chaque redéploiement sur ce type d'hébergeur. Pour le rendre permanent, ajoute
un **Volume** dans Railway monté sur `/app`, ou passe sur une base de données.

---

## Option B — Un VPS Linux (le plus fiable, ~3-5 €/mois)

Chez Hetzner, OVH, Contabo, etc. Une fois connecté en SSH :

```bash
sudo apt update && sudo apt install -y python3-venv git
git clone <ton-depot> discord-bot && cd discord-bot
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
nano .env          # colle DISCORD_TOKEN et GUILD_ID
```

Puis le service systemd (voir README.md, section 5) pour qu'il redémarre
tout seul au reboot et en cas de crash.

---

## Option C — Ton PC

Le bot est en ligne uniquement quand ton PC est allumé et le script lancé.
Parfait pour tester, pas pour un vrai serveur.

```bash
python bot.py
```

---

## Option D — Ton téléphone Android (Termux)

Utile pour tester sans PC. Installe **Termux** depuis F-Droid (pas le Play Store,
la version y est obsolète) :

```bash
pkg update && pkg install python git
git clone <ton-depot> && cd discord-bot
pip install -r requirements.txt
nano .env
python bot.py
```

Le bot s'arrête si Android tue l'appli — lance `termux-wake-lock` avant.
Impossible sur iPhone.

---

## Vérifier que ça marche

Dans les logs tu dois voir :

```
Cog charge : accueil ... setup_serveur
14 commandes synchronisees sur le serveur 1544297452377612288
Connecte en tant que N-studio#8836 (id=...)
Present sur 1 serveur(s)
```

Puis dans Discord : le point devient vert, et `/ping` répond.

| Ce que tu vois | Ce que ça veut dire |
|---|---|
| `PrivilegedIntentsRequired` | Active *Server Members* et *Message Content* dans le portail |
| `Improper token has been passed` | Token invalide ou mal copié (attention aux espaces) |
| `Present sur 0 serveur(s)` | Le bot n'est pas invité — repasse par l'URL OAuth2 |
| Rien, le process s'arrête direct | `.env` absent ou vide |
| En ligne mais `/ping` invisible | Attends, ou vérifie `GUILD_ID` et le scope `applications.commands` |
