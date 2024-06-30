from bot_manager.models import acmodels
from star_manager.settings import config


class Router:
    def db_for_read(self, model, **hints):
        """
        Reads go to a randomly-chosen replica.
        """
        if model in list(acmodels.values()):
            return config.DATABASE
        else:
            return 'default'

    def db_for_write(self, model, **hints):
        """
        Writes always go to primary.
        """
        if model in list(acmodels.values()):
            return config.DATABASE
        else:
            return 'default'

    def allow_relation(self, obj1, obj2, **hints):
        """
        Relations between objects are allowed if both objects are
        in the primary/replica pool.
        """
        if obj1 in list(acmodels.values()) or obj2 in list(acmodels.values()):
            return config.DATABASE
        else:
            return 'default'

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        All non-auth models end up in this pool.
        """
        if model_name in list(acmodels.keys()):
            return config.DATABASE
        else:
            return 'default'
