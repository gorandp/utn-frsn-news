import os
import dotenv

dotenv.load_dotenv()

from bot.messager import Messager


messager = Messager()
messager.process_queue()
