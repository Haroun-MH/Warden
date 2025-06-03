from django.apps import AppConfig


class WardenAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'warden_app'

    def ready(self):
        # This method is called when Django starts.
        # Import tasks here to avoid circular dependencies and ensure models are loaded.
        from . import tasks
        print("WardenAppConfig ready: Attempting to load BERT model...")
        tasks.load_bert_model_and_tokenizer() # Load the model
