# 🌸 IrisBot

A multipurpose Discord bot built with Python, `discord.py`, MongoDB, Wavelink and Lavalink.

Iris includes moderation, tickets, logging, welcome/leave systems, utilities and music playback.

> ⚠️ **Iris is still in development.** Music currently has some known Lavalink/YouTube compatibility bugs, so playback may not work for every YouTube video.

## ✨ Features

### 🛡️ Moderation
- Permission-based moderation
- Member management
- Moderation utilities

### 🎫 Tickets
- Private support tickets
- Custom ticket category
- Support role configuration
- Ticket logs
- Claim, close, reopen and delete tickets
- Transcripts

### 📜 Logging
- Server event logging
- Moderation logging
- Message/member/role/channel/voice/server/thread/emoji logs

### 👋 Welcome & Leave
- Welcome messages
- Goodbye/leave messages
- Customizable server-specific configuration

### 🎵 Music
Iris uses **Wavelink + Lavalink**.

Current music slash commands:
- `/play`
- `/pause`
- `/resume`
- `/skip`
- `/queue`
- `/nowplaying`
- `/volume`
- `/shuffle`
- `/clear`
- `/stop`
- `/leave`

Music can search for songs and resolve supported URLs through Lavalink.

### ⚙️ Help & Prefix
- `!help` shows the help menu by default
- `!help music` shows music commands
- `!prefix ?` changes the prefix for the current server
- Prefixes are stored per-server in MongoDB
- Slash commands continue to work normally

> The current prefix commands are for Help/Prefix. The existing moderation, ticket, logging, welcome and music commands are slash commands.

### 🗄️ MongoDB
MongoDB stores persistent server configuration and bot data, including ticket, logging, welcome/leave and prefix settings.

---

# 🚀 Setup

## 1. Requirements

Install:

- Python 3.10+
- Git
- MongoDB / MongoDB Atlas
- Java 21+
- Lavalink
- A Discord Bot Application

## 2. Clone

```bash
git clone YOUR_REPOSITORY_URL
cd IrisBot
```

## 3. Create a virtual environment

Windows PowerShell:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

## 4. Install dependencies

```powershell
pip install -r requirements.txt
```

## 5. Configure `.env`

Copy `.env.example` to `.env`:

```powershell
copy .env.example .env
```

Then fill in:

```env
DISCORD_TOKEN=your_discord_bot_token
MONGO_URI=your_mongodb_connection_string
SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret

LAVALINK_HOST=127.0.0.1
LAVALINK_PORT=2333
LAVALINK_PASSWORD=iris
```

**Never upload `.env` to GitHub.** It contains private credentials.

## 6. Discord bot setup

In the Discord Developer Portal:

1. Create an application.
2. Create a bot.
3. Copy the bot token into `.env`.
4. Enable the required intents, especially **Message Content Intent** if you want prefix commands.
5. Invite the bot with the required bot and application-command scopes.

## 7. MongoDB setup

Create a MongoDB database and put its connection string in:

```env
MONGO_URI=...
```

Iris uses the `iris` database and stores settings/data in its collections.

When Iris starts successfully, you should see:

```text
✅ Connected to MongoDB!
```

## 8. Lavalink setup

Iris connects to a local Lavalink server using:

```text
Host: 127.0.0.1
Port: 2333
Password: iris
```

Start Lavalink **before** starting Iris.

Your Lavalink `application.yml` should have the same password and port. You also need the required Lavalink plugins for YouTube and Spotify/source resolution.

When the connection succeeds, Iris should print:

```text
🎵 Connected to Lavalink
```

and then:

```text
🎵 Lavalink node ready
```

### Spotify

Spotify links are resolved through Lavalink/LavaSrc. Spotify credentials belong in the Lavalink configuration (or the setup you choose for LavaSrc), not in Discord commands.

Spotify normally provides metadata; the actual playable audio is resolved through an enabled audio source such as YouTube. This means a Spotify track can resolve successfully while playback can still fail if the selected YouTube source cannot provide an audio stream.

> ⚠️ **YouTube note:** YouTube frequently changes playback/authentication behavior. If Lavalink reports errors such as `This video requires login`, `No supported audio streams available`, or `Video player configuration error`, the problem is on the Lavalink/YouTube source side rather than Discord voice connection itself.

---

# ▶️ Running Iris

Start Lavalink in its own terminal first.

Then open another PowerShell window in the IrisBot folder:

```powershell
.\venv\Scripts\python.exe main.py
```

Or use:

```powershell
.\start.bat
```

A healthy startup should show the bot logging in, MongoDB connecting, cogs loading and Lavalink connecting.

---

# 🔧 Prefix commands

Default prefix:

```text
!help
```

Change it:

```text
!prefix ?
```

Now use:

```text
?help
```

Only administrators can change the server prefix.

---

# 🐛 Known Issues

- Some YouTube tracks may fail to play through Lavalink.
- Some YouTube videos may require authentication or may not expose a supported audio stream.
- Music is still being improved.
- AutoMod is planned for a future update.

If you find a bug, please include the console error and the command/query that caused it.

---

# 📌 Customization

Some server systems can be customized through the bot's configuration commands, including:

- Welcome channel/message configuration
- Goodbye/exit configuration
- Ticket category configuration
- Ticket support configuration
- Logging channels
- Per-server command prefix

---

# 🤝 Assistance

If you need help setting Iris up or modifying the bot, DM me on Discord:

**immense_sloth**

---

# 🛣️ Roadmap

- [ ] Improve YouTube music reliability
- [ ] Improve music error handling
- [ ] Add AutoMod
- [ ] More utility features
- [ ] More server customization

---

# 📄 License

Add your preferred license here before publishing the project publicly.
