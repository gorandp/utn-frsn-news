import dotenv
dotenv.load_dotenv()

from bot.scraper import Scraper
from bot.messager import Messager

# GCP tutorial followed
# https://cloud.google.com/blog/products/application-development/how-to-schedule-a-recurring-python-script-on-gcp

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
