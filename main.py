from quart import Quart, render_template, request, session, redirect, url_for
from quart_discord import DiscordOAuth2Session
from discord.ext import ipc
import json

j_file = open("secret.txt")
vari = json.load(j_file)
j_file.close()
ipcsecret = vari["ipcsecret"]
discordclientsecret = vari["discordclientsecret"]
appsecret = vari["appsecret"]

app = Quart(__name__)
ipc_client = ipc.Client(secret_key=ipcsecret)
app.config["SECRET_KEY"] = appsecret
app.config["DISCORD_CLIENT_ID"] = 743741872039657492
app.config["DISCORD_CLIENT_SECRET"] = discordclientsecret
app.config["DISCORD_REDIRECT_URI"] = "http://127.0.0.1:5000/callback"

discord = DiscordOAuth2Session(app)

@app.route('/')
async def home():
    return await render_template('index.html', authorized = await discord.authorized)

@app.route('/login')
async def login():
    return await discord.create_session()

@app.route('/callback')
async def callback():
    try:
        await discord.callback()
    except:
        pass
    return redirect(url_for("dashboard"))

@app.route('/dashboard')
async def dashboard():
    if not await discord.authorized:
        return redirect(url_for("login"))
    guild_count = await ipc_client.request("get_guild_count")
    guild_ids = await ipc_client.request("get_guild_ids")
    matching_guild = []
    user_guilds = await discord.fetch_guilds()
    for guild in user_guilds:
        if guild.permissions.administrator:
            guild.class_color="green-border" if guild.id in guild_ids else "red-border"
            matching_guild.append(guild)
    matching_guild.sort(key=lambda x:x.class_color=="red-border")
    name = (await discord.fetch_user()).name
    return await render_template('dashboard.html',guild_count = guild_count,matching = matching_guild, username = name)

@app.route("/dashboard/<int:guild_id>")
async def dashboard_server(guild_id):
    if not await discord.authorized:
        return redirect(url_for("login"))
    guild = await ipc_client.request("get_guild", guild_id=guild_id)
    if guild is None:
        return redirect(f"https://discord.com/oauth2/authorize?&client_id={app.config['DISCORD_CLIENT_ID']}&scope=bot&permissions=2130701687&guild_id={guild_id}&response_type=code&redirect_uri={app.config['DISCORD_REDIRECT_URI']}")
    return guild["name"]

if __name__ == '__main__':
    app.run(debug=True)