from celery import shared_task
from django.utils import timezone
from .models import LogEntry, AnomalyReport
from django.conf import settings
import openai
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import torch.nn.functional as F

# --- BERT Model and Tokenizer Loading ---
# It's highly recommended to load the model once when the Django app starts.
# You can do this in the ready() method of your AppConfig (e.g., warden_app/apps.py).
# For simplicity in this example, we load it here. Be mindful of memory usage in production.
MODEL_NAME = 'distilbert-base-uncased-finetuned-sst-2-english' # A good general-purpose sentiment model
tokenizer = None
model = None

def load_bert_model_and_tokenizer():
    global tokenizer, model
    if tokenizer is None or model is None:
        try:
            print(f"Loading BERT model and tokenizer: {MODEL_NAME}...")
            tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
            model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)
            model.eval()  # Set model to evaluation mode
            print(f"BERT model '{MODEL_NAME}' and tokenizer loaded successfully.")
        except Exception as e:
            print(f"CRITICAL: Error loading BERT model '{MODEL_NAME}': {e}")
            # In a production system, you might want to raise an exception or have a fallback.
            tokenizer = None # Ensure they are None if loading fails
            model = None

# The model is now loaded via AppConfig.ready() in apps.py
# load_bert_model_and_tokenizer() # This call is no longer needed here
# --- End of BERT Model Loading ---

@shared_task
def process_log_entry(log_entry_id):
    """
    Processes a single log entry: parses it (if needed), classifies it using BERT,
    and creates an AnomalyReport if it's an anomaly.
    """
    global tokenizer, model # Allow access to the globally loaded model and tokenizer

    if tokenizer is None or model is None:
        print(f"BERT model or tokenizer not loaded for {MODEL_NAME}. Attempting to reload...")
        load_bert_model_and_tokenizer() # Attempt to reload if not loaded
        if tokenizer is None or model is None:
            print(f"Failed to load BERT model for processing log {log_entry_id}. Skipping BERT classification.")
            # Optionally, mark the log as needing re-processing or handle the error
            try:
                log_entry = LogEntry.objects.get(id=log_entry_id)
                log_entry.analysis_notes = f"Skipped BERT: Model {MODEL_NAME} not available."
                log_entry.save()
            except LogEntry.DoesNotExist:
                pass # Log entry doesn't exist, nothing to update
            return

    try:
        log_entry = LogEntry.objects.get(id=log_entry_id)
    except LogEntry.DoesNotExist:
        print(f"LogEntry with id {log_entry_id} not found.")
        return

    print(f"Processing log entry ID: {log_entry.id} - Message: {log_entry.message[:100]}...")

    # --- BERT-based Anomaly Classification --- 
    is_anomaly_detected = False
    bert_score_value = None
    reason_for_anomaly = ""
    bert_model_name_used = MODEL_NAME

    try:
        inputs = tokenizer(log_entry.message, return_tensors="pt", truncation=True, max_length=512, padding=True)
        with torch.no_grad(): # Disable gradient calculations for inference
            logits = model(**inputs).logits
        
        # For 'distilbert-base-uncased-finetuned-sst-2-english':
        # Label 0: NEGATIVE, Label 1: POSITIVE
        # We'll consider NEGATIVE sentiment as a potential anomaly indicator.
        probabilities = F.softmax(logits, dim=-1)
        negative_score = probabilities[0][0].item() # Probability of being NEGATIVE
        positive_score = probabilities[0][1].item() # Probability of being POSITIVE

        bert_score_value = negative_score # Using negative score as the primary anomaly indicator

        # Define a threshold for anomaly (e.g., if negative probability > 0.7)
        anomaly_threshold = 0.7 
        if negative_score > anomaly_threshold:
            is_anomaly_detected = True
            reason_for_anomaly = f"High negative sentiment detected (score: {negative_score:.4f})."
        else:
            reason_for_anomaly = f"Low negative sentiment (score: {negative_score:.4f}). Positive score: {positive_score:.4f}."
        
        print(f"Log ID {log_entry.id}: BERT classification complete. Negative score: {negative_score:.4f}, Positive score: {positive_score:.4f}")

    except Exception as e:
        print(f"Error during BERT classification for log ID {log_entry.id}: {e}")
        reason_for_anomaly = f"Error during BERT processing: {e}"
        # Keep is_anomaly_detected as False or handle error as appropriate
        # log_entry.analysis_notes = f"BERT Error: {e}" # Optionally add notes to the log entry

    # --- End of BERT Classification --- 

    log_entry.is_anomaly = is_anomaly_detected
    log_entry.save()

    if is_anomaly_detected:
        AnomalyReport.objects.create(
            log_entry=log_entry,
            reason=reason_for_anomaly,
            bert_model_used=bert_model_name_used,
            bert_score=bert_score_value
        )
        report = AnomalyReport.objects.create(
            log_entry=log_entry,
            reason=reason_for_anomaly,
            bert_model_used=bert_model_name_used,
            bert_score=bert_score_value
        )
        print(f"Anomaly detected for Log ID {log_entry.id}. Report created with ID: {report.id}.")
        # Trigger summarization and notification task
        summarize_and_notify_anomaly.delay(report.id)
    else:
        print(f"No anomaly detected for Log ID {log_entry.id}.")

@shared_task
def periodically_classify_unanalyzed_logs():
    """
    Periodically fetches log entries that haven't been marked as anomaly or not
    (e.g., where is_anomaly is False and no AnomalyReport exists or a specific flag)
    and queues them for processing.
    This task is intended to be run periodically by Celery Beat.
    """
    # This logic assumes new logs might not be processed immediately.
    # We are looking for logs that are not yet analyzed (is_anomaly is still False)
    # and do not have an associated anomaly report (to avoid re-processing if a report was manually deleted but is_anomaly was True)
    # A more robust way might be to have a dedicated 'analysis_status' field in LogEntry.
    
    # For this example, let's process logs where `is_anomaly` is False and no AnomalyReport exists.
    # This is a simplified approach. In a real system, you might have a 'processed_by_bert_at' timestamp.
    unanalyzed_log_ids = LogEntry.objects.filter(
        is_anomaly=False, 
        anomaly_reports__isnull=True
    ).values_list('id', flat=True)[:100] # Process in batches

    if not unanalyzed_log_ids:
        print("No unanalyzed log entries found to process.")
        return

    print(f"Found {len(unanalyzed_log_ids)} unanalyzed log entries. Queuing for processing...")
    for log_id in unanalyzed_log_ids:
        process_log_entry.delay(log_id)
    print(f"Successfully queued {len(unanalyzed_log_ids)} log entries.")


@shared_task
def summarize_and_notify_anomaly(anomaly_report_id):
    """
    Generates an AI-driven summary for an anomaly report and sends a notification.
    """
    try:
        report = AnomalyReport.objects.select_related('log_entry').get(id=anomaly_report_id)
    except AnomalyReport.DoesNotExist:
        print(f"AnomalyReport with id {anomaly_report_id} not found for summarization.")
        return

    print(f"Summarizing and notifying for Anomaly Report ID: {report.id}")

    # Configure OpenAI API key
    if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY == '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':
        print("OpenAI API key not configured or is a placeholder. Skipping summarization.")
        # Simulate a basic notification without AI summary
        notification_message = (
            f"Anomaly Alert!\n"
            f"Log ID: {report.log_entry.id}\n"
            f"Timestamp: {report.log_entry.timestamp}\n"
            f"Service: {report.log_entry.service_name}\n"
            f"Message: {report.log_entry.message[:200]}...\n"
            f"Reason: {report.reason}\n"
            f"BERT Score: {report.bert_score:.4f}"
        )
        print(f"--- Notification (Basic) ---\n{notification_message}\n---------------------------")
        return

    openai.api_key = settings.OPENAI_API_KEY

    log_message_snippet = report.log_entry.message[:1000] # Take a snippet for the prompt

    prompt_text = (
        f"An automated system detected an anomaly in a log entry.\n"
        f"Please provide a concise summary (1-2 sentences) suitable for a notification, highlighting the key issue.\n\n"
        f"Log Entry Details:\n"
        f"- Service: {report.log_entry.service_name}\n"
        f"- Timestamp: {report.log_entry.timestamp.strftime('%Y-%m-%d %H:%M:%S %Z')}\n"
        f"- Original Log Message (snippet): \"{log_message_snippet}\"\n"
        f"- Detected Anomaly Reason: {report.reason}\n"
        f"- Anomaly Score (from BERT model): {report.bert_score:.4f}\n"
        f"Summary for notification:"
    )

    summary = "Could not generate AI summary."
    try:
        print("Calling OpenAI API for summarization...")
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo", # Or use "gpt-4" if available and preferred
            messages=[
                {"role": "system", "content": "You are an expert at summarizing technical alerts concisely."},
                {"role": "user", "content": prompt_text}
            ],
            max_tokens=100,
            temperature=0.5,
        )
        if response.choices and response.choices[0].message:
            summary = response.choices[0].message.content.strip()
        print(f"OpenAI API summary received: {summary}")
    except Exception as e:
        print(f"Error calling OpenAI API: {e}")
        summary = f"AI summary failed. Reason: {report.reason}" # Fallback summary

    # Simulate sending a notification (e.g., email, Slack)
    notification_message = (
        f"Anomaly Alert!\n"
        f"Log ID: {report.log_entry.id}\n"
        f"Timestamp: {report.log_entry.timestamp}\n"
        f"Service: {report.log_entry.service_name}\n"
        f"Summary: {summary}\n"
        f"Original Message (snippet): {report.log_entry.message[:100]}...\n"
        f"BERT Score: {report.bert_score:.4f}"
    )

    print(f"--- Notification (AI Summarized) ---\n{notification_message}\n------------------------------------")

    # Here you would add actual notification logic, e.g.:
    # send_email_notification(subject="Anomaly Detected", message=notification_message, recipient_list=['admin@example.com'])
    # send_slack_notification(channel="#alerts", message=notification_message)