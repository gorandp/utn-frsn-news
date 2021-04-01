import pymongo

def connect(config: dict):
    return DB(**config)

# Source: https://stackoverflow.com/a/6798042/12692806
class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class DB(metaclass=Singleton):
    __client__ = None
    database = None


    def __init__(self, **kwargs):
        if kwargs:
            self.connect(**kwargs)
            self.test_connection(**kwargs)

    def connect(self,
        DATABASE_NAME=None,
        DB_CONNECTION_STRING=None,
        DB_HOST=None,
        DB_PORT=None,
        DB_USER=None,
        DB_PASS=None,
        DB_AUTH_SOURCE=None,
        **kwargs
    ):
        """ Establish connection with DB """
        DATABASE_NAME = "compra_publica" if DATABASE_NAME is None else DATABASE_NAME

        if DB_CONNECTION_STRING is not None:
            # Connection String 
            #
            # Used in:
            # - Development
            # - Testing
            self.__client__ = pymongo.MongoClient(DB_CONNECTION_STRING)

        else:
            # Host connection
            # 
            # Used for local conection with SSH or also with
            # intern IP of datacenter

            self.__client__ = pymongo.MongoClient(
                host=DB_HOST,
                port=DB_PORT,
                username=DB_USER,
                password=DB_PASS,
                authSource=DB_AUTH_SOURCE
            )

        # Database init
        self.database = self.__client__[DATABASE_NAME]

    def test_connection(self, DB_AVOID_TEST=None, **kwargs):
        if not DB_AVOID_TEST:
            self.__client__.server_info()

    def close(self):
        """ Close connection """
        self.__client__.close()
        self.__client__ = None
        self.database = None
