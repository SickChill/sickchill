class BaseConfig:
    """
    Base config class
    """

    DEBUG = True
    TESTING = False
    SERVER_NAME = "SickChill"


class ProductionConfig(BaseConfig):
    """
    Production specific config
    """

    DEBUG = False


class DevelopmentConfig(BaseConfig):
    """
    Development environment specific configuration
    """

    DEBUG = True
    TESTING = True
