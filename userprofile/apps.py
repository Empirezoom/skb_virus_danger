from django.apps import AppConfig


class UserprofileConfig(AppConfig):
    name = 'userprofile'

    def ready(self):
        import userprofile.models  # ensure signals are loaded
