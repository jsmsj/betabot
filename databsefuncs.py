import motor.motor_asyncio
import os
from dotenv import  load_dotenv
import certifi
import discord
import asyncio

ca = certifi.where()
load_dotenv()

client = motor.motor_asyncio.AsyncIOMotorClient(os.environ.get('DBURL'),tlsCAFile=ca)

db = client['pbcryptichunt']

col_levans = db['queans_json']
col_user_data_time = db['user_data_time']
col_registered_users = db['registered_users']
col_mod_logs = db['mod_logs']

########### general funcs
def sortByLevel(data):
    return data['level']

def sortByTimestamp(data):
    return data['timestamp']
###############

##### level - answer functions
async def insert_levans(lev,ans,channel_id):
    doc = {"level":lev,"answer":ans,"channel_id":channel_id}
    await col_levans.insert_one(doc)
    return

async def get_ansforlev(lev):
    data = await col_levans.find_one({"level":lev})
    return data['answer']

async def get_channelforlev(lev):
    data = await col_levans.find_one({"level":lev})
    return data['channel_id']

async def delete_lev(lev):
    await col_levans.delete_one({"level":lev})
    return
################

################ user-data-time --> log functions
async def insert_userdatatime(userid,type,data,timestamp,level=None):
    """type: ["SUBMISSION","REGISTRATION","ERROR","INFO"]""" 
    doc = {
        "userid":userid,
        "type":type,
        "data":data,
        "timestamp" : timestamp,
        "level":level if level else 0
    }
    await col_user_data_time.insert_one(doc)
    return

async def find_userdatatime(user:discord.User=None):
    if user:
        data = col_user_data_time.find({"userid":user.id},{"_id":0})
    else:
        data = col_user_data_time.find({},{"_id":0})
    docs = await data.to_list(length=None)
    docs.sort(key=sortByTimestamp,reverse=True)
    return docs
########################

######################### registered users functions
async def insert_registered_user(userid,fake_name,real_name,level=None,completed=False):
    doc = {"userid":userid,"real_name":real_name,"fake_name":fake_name,"level":level if level else 0,"completed":"False" if not completed else "True"}
    await col_registered_users.insert_one(doc)
    return

async def is_registered(userid):
    return True if await col_registered_users.find_one({"userid":userid}) else False

async def is_completed(userid):
    data = await col_registered_users.find_one({"userid":userid})
    return False if data['completed'] == "False" else True

async def is_fakename_unique(fake_name):
    return False if await col_registered_users.find_one({"fake_name":fake_name}) else True

async def update_level(userid,level):
    await col_registered_users.update_one({"userid":userid},{"$set":{"level":level}})
    return

async def update_completion_status(userid,status):
    await col_registered_users.update_one({"userid":userid},{"$set":{"completed":status}})

async def get_level(userid):
    user = await col_registered_users.find_one({"userid":userid})
    return user['level']

async def give_level_descending():
    data = col_registered_users.find({},{"fake_name":1,"level":1,"completed":1,"_id":0})
    docs = await data.to_list(length=None)
    docs.sort(key=sortByLevel,reverse=True)
    return docs

async def get_all_registered_users():
    data = col_registered_users.find()
    docs = await data.to_list(length=None)
    return docs

async def get_registered_user_from_id(userid):
    data = await col_registered_users.find_one({"userid":userid})
    return data

async def delete_registered_user(userid):
    await col_registered_users.delete_one({"userid":userid})

async def get_registered_user_from_fake_name(fake_name):
    data = await col_registered_users.find_one({"fake_name":fake_name})
    return data
#####################

#################### mod logs functions
async def insert_mod_logs(userid,type,data,timestamp):
    """type: ["STOP_EVENT","START_EVENT","REGISTRATION_MESSAGE","RULE_CONF_MSG"]"""
    doc = {
        "userid" : userid,
        "type": type,
        "data":data,
        "timestamp":timestamp
    }
    await col_mod_logs.insert_one(doc)

async def get_mod_logs(user:discord.User=None):
    if user:
        data = col_mod_logs.find({"userid":user.id},{"_id":0})
    else:
        data = col_mod_logs.find({},{"_id":0})
    docs = await data.to_list(length=None)
    docs.sort(key=sortByTimestamp,reverse=True)
    return docs
#####################

# ############# export stuff
# import pandas as pd

# async def export_to_csv():
#     data = col_user_data_time.find()
#     docs = await data.to_list(length=None)
#     docs.sort(key=sortByTimestamp,reverse=True)
#     df = pd.DataFrame(docs)
#     df.to_csv('1.csv',index=False)
# ######################

# asyncio.run(export_to_csv())

# def mySortKey(data):
#     return data['timestamp']

# ls = asyncio.run(find_userdatatime(1311))
# ls.sort(key=mySortKey,reverse=True)

# print(ls)

# async def temp():
#     await insert_registered_user(21312322,"fdsfsd1","rerer",12)
#     await insert_registered_user(223222457132,"fdsfsd2","rerer",155)
#     await insert_registered_user(276585612,"fdsfsd3","rerer",15)
#     await insert_registered_user(2168484312212,"fdsfsd4","rerer",3)
#     await insert_registered_user(2168484312212,"fdsfsd5","rerer",4)
#     await insert_registered_user(2168484312212,"fdsfsd6","rerer",5)
#     await insert_registered_user(2168484312212,"fdsfsd7","rerer",6)
#     await insert_registered_user(2168484312212,"fdsfsd8","rerer",7)
#     await insert_registered_user(2168484312212,"fdsfsd9","rerer",8)
#     await insert_registered_user(2168484312212,"fdsfsd10","rerer",22)
#     await insert_registered_user(2168484312212,"fdsfsd11","rerer",5489)
#     await insert_registered_user(2168484312212,"fdsfsd12","rerer",42)
#     await insert_registered_user(2168484312212,"fdsfsd13","rerer",443)
#     await insert_registered_user(2168484312212,"fdsfsd14","rerer",2)

# asyncio.run(temp())

# asyncio.run(insert_registered_user(223290569062,"another2","rereaddar",155))