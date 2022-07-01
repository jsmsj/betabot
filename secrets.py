from dotenv import load_dotenv
import os
load_dotenv()

MODS = [int(i) for i in os.getenv('MODS').split(',')]
announcement_chan_id = int(os.getenv('announcement_channel_id'))
leaderboard_chan_id = int(os.getenv('leaderboard_channel_id'))