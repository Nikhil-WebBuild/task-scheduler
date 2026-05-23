from django.apps import AppConfig

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        from django.db.models.signals import post_migrate
        from django.dispatch import receiver

        # Using post_migrate signal instead of calling create_admin() directly in ready().
        # Calling DB queries inside ready() causes a crash on a fresh database
        # because migrations have not run yet and the tables do not exist.
        # post_migrate fires after all migrations are applied, so the tables are guaranteed to exist.
        @receiver(post_migrate, sender=self)
        def on_post_migrate(sender, **kwargs):
            from .views import create_admin
            create_admin()