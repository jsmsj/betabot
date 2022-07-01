from dotenv import load_dotenv
from discord.ext import commands,tasks,pages
from discord.ui import Modal,InputText
import discord
import os
load_dotenv()
import helpers as hp
import datetime
import databsefuncs as dbf
import secrets

def make_timestamp():
    tz = datetime.timezone(datetime.timedelta(hours=5.5))
    dtobj = datetime.datetime.now().replace(tzinfo=tz)
    return round(dtobj.timestamp())

def make_em_timestamp():
    tz = datetime.timezone(datetime.timedelta(hours=5.5))
    return datetime.datetime.now().replace(tzinfo=tz)

intents = discord.Intents.all()

bot = commands.Bot(command_prefix=os.environ.get("PREFIX"),intents=intents, case_insensitive=True,help_command=None)

class MyModal(Modal):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.add_item(InputText(label="Fake Name: [max 12 characters]", placeholder="Enter your fakename here, to appear on the leaderboard"))
        self.add_item(InputText(label="Real Name:",placeholder="Enter your real name here."))

    async def callback(self, interaction: discord.Interaction):
        if len(self.children[0].value) > 12:
            await interaction.response.send_message("Error: length of fakename is more than 12, kindly re-register.",ephemeral=True)
        else:
            if await dbf.is_fakename_unique(self.children[0].value):
                await dbf.insert_registered_user(interaction.user.id,self.children[0].value,self.children[1].value)
                await dbf.insert_userdatatime(interaction.user.id,"REGISTRATION","User has registered for event",make_timestamp())
                await interaction.response.send_message("You have successfully registered for the event.", ephemeral=True)
            else:
                await interaction.response.send_message("Error: fakename used by some other user, kindly re-register.",ephemeral=True)

class PersistentView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Register",
        style=discord.ButtonStyle.green,
        custom_id="persistent_view:green",
    )
    async def green(self, button: discord.ui.Button, interaction: discord.Interaction):
        # interaction.response.send_message or interaction.followup.send
        if not await dbf.is_registered(interaction.user.id):
            modal = MyModal(title="Register for the event")
            await interaction.response.send_modal(modal)
        else:
            await interaction.response.send_message("You have already registered for this event.", ephemeral=True)

@bot.event
async def on_ready():
    setattr(bot,"leaderboard_msg_id",None)
    persistent_views_added = False
    if not persistent_views_added:
        bot.add_view(PersistentView())
        persistent_views_added = True

    commands_list = [bot.get_command("submit")]
    for comm in commands_list:
        comm.enabled = False
    await dbf.insert_mod_logs(bot.user.id,"STOP_EVENT","Bot has (re)started and stopped the event.",make_timestamp())
    print("Bot is ready!")

# @bot.event
# async def on_message(message):
#     if message.author.bot:return
#     eveguild = await bot.fetch_guild(int(os.getenv('event_guild_id')))
#     try:
#         await eveguild.fetch_member(message.author.id)
#     except:
#         return

#     await bot.process_commands(message)

@bot.event
async def on_command_error(ctx,error):
    if hasattr(ctx.command, 'on_error'):
        return
    if isinstance(error,commands.CommandNotFound):
        return
    if isinstance(error,commands.DisabledCommand):
        await ctx.send("The command is disabled, either you do not have permissions to run this command or the event has not started yet.")
    elif isinstance(error,commands.CheckFailure):
        await ctx.send("You do not have permission to run this command.")
    else:
        await ctx.send(f"Error: the correct usage is : {ctx.command.description}")
        chan = await bot.fetch_channel(int(os.getenv('error_channel')))
        await chan.send(embed=hp.errorembed(ctx,error))

@bot.command(description="Shows the bot's latency")
async def ping(ctx):
    await ctx.send(f"🏓 {round(bot.latency*1000)}ms")

@bot.command(description=f"Submits the answer provided by participant `{os.getenv('PREFIX')}submit answer_text`")
async def submit(ctx:commands.Context,*,response=None):
    if not response : return await ctx.send(f"No answer provided, correct usage: `{os.getenv('PREFIX')}submit answer_text`")
    if await dbf.is_registered(ctx.author.id):
        resp = hp.format_response(response)
        user_level = await dbf.get_level(ctx.author.id)
        correct_answer = await dbf.get_ansforlev(user_level)
        ques_channel_id = await dbf.get_channelforlev(user_level)
        ques_channel = await bot.fetch_channel(ques_channel_id)
        info = False
        lb_chan = await bot.fetch_channel(secrets.leaderboard_chan_id)
        if not await dbf.is_completed(ctx.author.id):
            if resp == correct_answer:
                em = hp.give_correct_ans_em(resp,ques_channel)
                em.timestamp = make_em_timestamp()
                await ctx.send(embed=em)
                emb = discord.Embed(title="🎉 Congratulations 🎉",color=discord.Color.green(),timestamp=make_em_timestamp())
                if user_level == int(os.getenv("max_level")):
                    emb.description = f"Congratulations {ctx.author.display_name} you have solved all the questions reached the maximum level.\nYou currently have {(user_level+1)*500} points.\nLeaderboard : {lb_chan.mention}" 
                    await ctx.send(embed=emb)
                    await dbf.update_completion_status(ctx.author.id,"True")
                    info = "Completed the Event"
                else:
                    nxt_q_c_id = await dbf.get_channelforlev(user_level+1)
                    next_ques_channel = await bot.fetch_channel(nxt_q_c_id)
                    emb.description = f"Congratulations {ctx.author.display_name} you have solved the question of level {user_level}, now you are at level {user_level+1}.\nNext Question : {next_ques_channel.mention}.\nYou currently have {(user_level+1)*500} points.\nLeaderboard : {lb_chan.mention}" 
                    await ctx.send(embed=emb)
                    await dbf.update_level(ctx.author.id,user_level+1)
                    info = f"Levelled up to {user_level+1}"
                    eve_guild = await bot.fetch_guild(int(os.getenv('event_guild_id')))
                    role = eve_guild.get_role(int(os.getenv(f'level_{user_level+1}')))
                    author = await eve_guild.fetch_member(ctx.author.id)
                    if role not in author.roles:
                        await author.add_roles(role)
            else:
                em = hp.give_incorrect_ans_em(resp,ques_channel)
                em.timestamp = make_em_timestamp()
                await ctx.send(embed=em)
        else:
            em = discord.Embed(title="Already Completed",description=f"You have already solved all the questions. Now sit back and relax or see the leaderboard : {lb_chan.mention}",color=discord.Color.green())
            await ctx.send(embed=em)
        if info:
            await dbf.insert_userdatatime(ctx.author.id,"SUBMISSION",f"submitted answer---> {resp} for level---> {user_level} | {info}",make_timestamp(),user_level+1)
        else:
            await dbf.insert_userdatatime(ctx.author.id,"SUBMISSION",f"submitted answer---> {resp} for level---> {user_level}",make_timestamp(),user_level)
    else:
        await ctx.send("You have not registered for the event, hence you can not use this command.")

@bot.command(description=f"Sends the registration message to desired channel `{os.getenv('PREFIX')}sendRegisMsg #channel`")
@hp.is_allowed()
async def sendRegisMsg(ctx,channel:discord.TextChannel=None):
    if not channel: return await ctx.send(f"No channel provided to send the message, correct usage: `{os.getenv('PREFIX')}sendRegisMsg #channel`")
    em = hp.get_registration_embed()
    msg = await channel.send(embed=em,view=PersistentView())
    await ctx.send(f"Successfully sent registration message -> {msg.jump_url}")
    await dbf.insert_mod_logs(ctx.author.id,"REGISTRATION_MESSAGE",f"Registration message sent to channel_id = {channel.id}",make_timestamp())


@bot.command(description=f"Enables the `submit` command as well as starts the ongoing event. Also it may send all registered users a dm to start answering.\n`{os.getenv('PREFIX')}startEvent` or `{os.getenv('PREFIX')}startEvent true`\n use the second option to dm all users as well.")
@hp.is_allowed()
async def startEvent(ctx,sendMsg:bool=False):
    commands_list = [bot.get_command("submit")]
    for comm in commands_list:
        comm.enabled = True
    chan = await bot.fetch_channel(secrets.announcement_chan_id)
    em = discord.Embed(title="The Event has started !",description=f"All registered users should dm the bot : {bot.user.mention} with their chosen answer in the format `pb submit your_answer`\nFor example,\n`pb submit exmagician`\n`pb submit elonmusk`",color=discord.Color.green())
    msg = await chan.send(embed=em)
    all_registered_users = await dbf.get_all_registered_users()
    if sendMsg:
        for i in all_registered_users:
            try:
                temp_user = await bot.fetch_user(i['userid'])
                await temp_user.send("The event has started, DM me with your answer in the format, `pb submit your_answer`\nFor Example: \n`pb submit exmagician`\n`pb submit avadakedavra`")
            except:
                pass
        await ctx.send(f"Successfully started the event and sent all registered users the dm -> {msg.jump_url}")
    await dbf.insert_mod_logs(ctx.author.id,"START_EVENT",f"Event has been started by a mod",make_timestamp())

@bot.command(description="Disables the `submit` command as well as ends the ongoing event")
@hp.is_allowed()
async def endEvent(ctx):
    commands_list = [bot.get_command("submit")]
    for comm in commands_list:
        comm.enabled = False
    chan = await bot.fetch_channel(secrets.announcement_chan_id)
    lb_chan = await bot.fetch_channel(secrets.leaderboard_chan_id)
    em = discord.Embed(title="The Event has ended !",description=f"Thankyou to all the participants for participating in this event. You may see the leaderboard here : {lb_chan.mention}",color=discord.Color.green())
    msg = await chan.send(embed=em)
    await ctx.send(f"Successfully ended the event -> {msg.jump_url}")
    await dbf.insert_mod_logs(ctx.author.id,"STOP_EVENT",f"Event has been stopped by a mod",make_timestamp())

@bot.command(description=f"Insert answer statement for a given level\n`{os.getenv('PREFIX')}insertLevAns level_int answer_text #lvl_ques_channel`") 
@hp.is_allowed()
async def insertLevAns(ctx,level:int,ans,channel:discord.TextChannel):
    await dbf.insert_levans(level,ans,channel.id)
    await ctx.send("done")

@insertLevAns.error
async def error_insertLevAns(ctx,error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"Missing required arguments, correct usage : `{os.getenv('PREFIX')}insertLevAns level_int answer_text #lvl_ques_channel`")

@bot.command(description="Shows the leaderboard in your current channel")
@hp.is_allowed()
async def showLeaderboard(ctx):
    chan = await bot.fetch_channel(secrets.leaderboard_chan_id)
    ls_of_data = await dbf.give_level_descending()
    em = hp.give_leaderboard(ls_of_data)
    msg = await chan.send(embed=em)
    if not bot.leaderboard_msg_id:
        bot.leaderboard_msg_id = msg.id
    await ctx.send(f"Successfully sent the leaderboard -> {msg.jump_url}")

@bot.command(description=f"Starts updating the leaderboard, updation occours every {os.getenv('lb_update_interval_secs')} seconds")
@hp.is_allowed()
async def startLbUpdate(ctx):
    update_leaderboard.start()
    await ctx.send("Successfully started leaderboard auto-update")

@bot.command(description="Stops updating the leaderboard")
@hp.is_allowed()
async def stopLbUpdate(ctx):
    update_leaderboard.stop()
    await ctx.send("Successfully stopped leaderboard auto-update")


@tasks.loop(seconds=int(os.getenv('lb_update_interval_secs')))
async def update_leaderboard():
    chan = await bot.fetch_channel(secrets.leaderboard_chan_id)
    ls_of_data = await dbf.give_level_descending()
    em = hp.give_leaderboard(ls_of_data)
    if not bot.leaderboard_msg_id:
        msg = await chan.send(embed=em)
        bot.leaderboard_msg_id = msg.id
    else:
        msg = await chan.fetch_message(bot.leaderboard_msg_id)
        await msg.edit(embed=em)

@bot.command(description=f"Shows logs for a moderator [`{os.getenv('PREFIX')}showModLogs @Member`] or all logs [`{os.getenv('PREFIX')}showModLogs`]")
@hp.is_allowed()
async def showModLogs(ctx,user:discord.User=None):
    ls_md_log = await dbf.get_mod_logs(user)
    if ls_md_log == []:
        return await ctx.send("No logs found for the given user")
    ls_of_embs = hp.giveLogEmbed(ls_md_log)
    paginator = pages.Paginator(pages=ls_of_embs)
    await paginator.send(ctx)

# @bot.command(description=)
# async def tempo(ctx,x:int):
#     pag = pages.Paginator(pages=hp.temp(x))
#     await pag.send(ctx)

@bot.command(description=f"Shows submissions and logs for a participant [`{os.getenv('PREFIX')}showSubmissions @Member`] or all submissions [`{os.getenv('PREFIX')}showSubmissions`]")
@hp.is_allowed()
async def showSubmissions(ctx,user:discord.User=None):
    ls_user_time_log = await dbf.find_userdatatime(user)
    if ls_user_time_log == []:
        return await ctx.send("No logs found for the given user")
    ls_of_embs = hp.giveLogEmbed(ls_user_time_log)
    paginator = pages.Paginator(pages=ls_of_embs)
    await paginator.send(ctx)

@bot.command(description="Gives the help for various commands avaialable")
@hp.is_allowed()
async def help(ctx):
    ls_of_em = []
    com_except_jishaku = [i for i in list(bot.commands) if i.name!= "jishaku"]
    com_list = [com_except_jishaku[i:i + 6] for i in range(0, len(com_except_jishaku), 6)]
    for idx,val in enumerate(com_list):
        em = discord.Embed(title=f"Help -- Page: {idx+1}",color=discord.Color.green())
        for j in val:
            em.add_field(name=f"{os.getenv('PREFIX')}{j.name}",value=j.description if j.description else "None",inline=False)
        ls_of_em.append(em)
    paginator = pages.Paginator(pages=ls_of_em)
    await paginator.send(ctx)


if __name__ == '__main__':
    # When running this file, if it is the 'main' file
    # i.e. its not being imported from another python file run this
    bot.load_extension('jishaku')
    bot.run(os.environ.get("TOKEN"))