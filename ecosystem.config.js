// PM2 - bot Discord N-studio
//
//   pm2 start ecosystem.config.js     lancer
//   pm2 logs n-studio                 voir les logs en direct
//   pm2 restart n-studio              redemarrer
//   pm2 save && pm2 startup           relancer tout seul au reboot du VPS
//
// Prerequis sur le VPS : Node.js + `npm i -g pm2`, le venv cree
// (`python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`)
// et un fichier .env rempli a la racine du projet.

module.exports = {
  apps: [
    {
      name: "n-studio",
      script: "bot.py",

      // Interpreteur du venv, pas le python systeme.
      // Sous Windows, remplacer par ".venv/Scripts/python.exe".
      interpreter: "./.venv/bin/python",
      // -u : sortie non bufferisee, sinon les logs n'arrivent que par blocs.
      interpreter_args: "-u",

      // bot.py charge les cogs via un chemin relatif (Path("cogs")) :
      // sans ce cwd, demarrage impossible.
      cwd: __dirname,

      autorestart: true,
      restart_delay: 5000, // laisse passer les coupures reseau courtes
      max_restarts: 10,
      min_uptime: "30s", // en dessous, PM2 considere que ca crashloop

      // Surtout pas de watch : le bot ecrit lui-meme config.json
      // (accueil + roles a reaction), ce qui le ferait redemarrer en boucle.
      watch: false,

      max_memory_restart: "300M",

      env: {
        PYTHONUNBUFFERED: "1",
      },

      error_file: "logs/erreur.log",
      out_file: "logs/sortie.log",
      merge_logs: true,
      time: true, // horodate chaque ligne
    },
  ],
};
