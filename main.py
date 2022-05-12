from bot import *
from dotenv import load_dotenv, dotenv_values

load_dotenv()
config = dotenv_values(".env")

if __name__=="__main__": startBot(config['DISCORD_TOKEN'])

