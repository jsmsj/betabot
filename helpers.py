import traceback
from dotenv import load_dotenv
from discord.ext import commands
import discord
import os
load_dotenv()
import secrets
from prettytable import PrettyTable
import datetime

import pytz

tz_IN = pytz.timezone('Asia/Kolkata') 


def get_registration_embed():
    em = discord.Embed(title="Register for the event",color=discord.Color.green())
    em.description = "Click the button below to register for the event."
    return em

def is_allowed():
    async def allowed(ctx):
        if ctx.author.id in secrets.MODS:
            return True
        else:
            return False
    return commands.check(allowed)

def format_response(response):
    return response.lower().strip().replace(" ","")

def give_incorrect_ans_em(user_ans,channel:discord.TextChannel):
    em = discord.Embed(title="Incorrect Answer",description=f"`{user_ans}` is the **incorrect** answer for the problem posted in {channel.mention}",color=discord.Color.green())
    return em

def give_correct_ans_em(user_ans,channel:discord.TextChannel):
    em = discord.Embed(title="Correct Answer",description=f"`{user_ans}` is the **correct** answer for the problem posted in {channel.mention}",color=discord.Color.green())
    return em

def get_string_for_rank(rank):
    if rank == 1: return "🥇"
    elif rank == 2: return "🥈"
    elif rank == 3: return "🥉"
    else: return f"#{rank}"

def give_leaderboard(ls):
    em = discord.Embed(title="Leaderboard",color=discord.Color.green())
    tbl = PrettyTable()
    tbl.field_names = ["Rank","Username","Level","Points"]
    for idx,val in enumerate(ls):
        if idx <=24:
            tbl.add_row([f"#{idx+1}" ,val['fake_name'],val['level'],(val['level'])*500 if val['completed'] !="True" else (val['level']+1)*500])
        else:
            break
    tbl.align['Rank'] = "l"
    tbl.align['Username'] = "c"
    tbl.align['Level'] = "c"
    tbl.align['Points'] = "r"
    em.description = f"```diff\n{tbl.get_string()}\n```"
    return em

def full_time(timestamp):
    dt_object = datetime.datetime.fromtimestamp(timestamp,tz=tz_IN)
    return dt_object.strftime("%H:%M:%S %d-%m-%Y %Z")

def giveLogEmbed(ls):
    quotient,remainder = len(ls)//6 , len(ls)%6
    total_embeds = quotient if remainder == 0 else quotient+1
    data_ls = [ls[i:i + 6] for i in range(0, len(ls), 6)]
    ls_embs = []
    for i in range(total_embeds):
        emb = discord.Embed(title=f"Logs -- {i+1}",color=discord.Color.green())
        emb.set_footer(text="Time format: hh:mm:ss dd-mm-yyyy")
        log_data = data_ls[i]
        for j in log_data:
            emb.add_field(name=j['type'],value=f"<@!{j['userid']}>\n```\n{j['data']}\n```\n{j['timestamp']}\n<t:{j['timestamp']}:R>\n{full_time(j['timestamp'])}",inline=False)
        ls_embs.append(emb)
    return ls_embs       

# def temp(x):
#     return [discord.Embed(title=f"{i}",description=f"hi {i}") for i in range(x)]

def errorembed(ctx:commands.Context,error):
    em = discord.Embed(title=f"⚠️ Error in {ctx.command.name}",color=discord.Color.red())
    em.description = f"```py\n{''.join(traceback.format_exception(type(error), error, error.__traceback__))[:4000]}\n```"
    em.add_field(name="Invoked by",value=f"{ctx.author.display_name}\n{ctx.author.id}\n{ctx.author.mention}")
    return em

def generate_user_data_embed(user_data):
    em = discord.Embed(title="User Registration Data",color=discord.Color.green())
    em.add_field(name="Real Name",value=user_data['real_name'],inline=False)
    em.add_field(name="Nick Name",value=user_data['fake_name'],inline=False)
    em.add_field(name="Event Completed ?",value=user_data['completed'],inline=False)
    em.add_field(name="Current Level",value=user_data['level'],inline=False)
    return em