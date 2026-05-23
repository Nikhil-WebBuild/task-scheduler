from django.apps import AppConfig

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        from django.db.models.signals import post_migrate
        from django.dispatch import receiver

        @receiver(post_migrate, sender=self)
        def on_post_migrate(sender, **kwargs):
            from .views import create_admin
            create_admin()