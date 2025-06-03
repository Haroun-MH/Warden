from django.apps import AppConfig
from django.conf import settings

class WardenAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'warden_app'

    def ready(self):
        print("WardenAppConfig ready method called.")
        # Import tasks here to avoid circular imports and ensure models are loaded
        from . import tasks
        try:
            # Attempt to load the BERT model and tokenizer when the app is ready.
            # This makes them available globally within the tasks module.
            print("Attempting to load BERT model and tokenizer from WardenAppConfig...")
            tasks.load_bert_model_and_tokenizer() # This function is defined in tasks.py
            # No need to store on settings if tasks.py manages them globally
            # print(f"BERT Model: {'Loaded' if tasks.model else 'Not Loaded'}")
            # print(f"BERT Tokenizer: {'Loaded' if tasks.tokenizer else 'Not Loaded'}")
        except Exception as e:
            # Log a critical error if model loading fails, but allow the app to continue running.
            # Tasks that depend on the model will need to handle its absence.
            print(f"CRITICAL_ERROR_IN_APPS_READY: Failed to load BERT model/tokenizer: {e}")
            # Ensure settings reflect that the model is not available if other parts check settings
            # settings.BERT_MODEL = None
            # settings.BERT_TOKENIZER = None
            # settings.BERT_MODEL_NAME = None

        # Initialize OpenAI API key from settings if not already done by Django's settings load
        # This is more of a check or can be used if API key needs dynamic setup
        if not hasattr(settings, 'OPENAI_API_KEY'):
            settings.OPENAI_API_KEY = None # Or load from environment/secrets manager here
            print("OPENAI_API_KEY was not set in Django settings. Initialized to None.")
        else:
            print(f"OPENAI_API_KEY found in Django settings: {'Exists' if settings.OPENAI_API_KEY else 'Not Set or Empty'}")

        # You can also connect signals here if needed
        # from . import signals
        print("WardenAppConfig ready method finished.")
