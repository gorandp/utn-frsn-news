import dotenv
dotenv.load_dotenv()

from bot.scraper import Scraper
from bot.messager import Messager

# Enforced main.py by GCP
# and also data/context variables passed to "entry points"
# (the 2 functions you see)
# https://stackoverflow.com/questions/58452034/main-takes-0-positional-arguments-but-2-were-given

def main_scraper(data, context):
    """Triggered from a message on a Cloud Pub/Sub topic.
    Args:
        data (dict): Event payload.
        context (google.cloud.functions.Context): Metadata for the event.
    """
    scraper = Scraper()
    scraper.start()

def main_messenger(data, context):
    """Triggered from a message on a Cloud Pub/Sub topic.
    Args:
        data (dict): Event payload.
        context (google.cloud.functions.Context): Metadata for the event.
    """
    messager = Messager()
    messager.process_queue()

# if __name__ == "__main__":
#     main_scraper({}, {})
#     main_messenger({}, {})
