import os
import dotenv

dotenv.load_dotenv()

from bot.scraper import Scraper


scraper = Scraper()
scraper.start()
