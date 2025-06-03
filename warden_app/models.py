from django.db import models

class LogEntry(models.Model):
    SEVERITY_CHOICES = [
        ('INFO', 'Info'),
        ('WARNING', 'Warning'),
        ('ERROR', 'Error'),
        ('CRITICAL', 'Critical'),
        ('DEBUG', 'Debug'),
    ]

    timestamp = models.DateTimeField(help_text="The time the log event occurred.")
    source = models.CharField(max_length=100, help_text="Source of the log (e.g., 'application', 'nginx', 'database').")
    message = models.TextField(help_text="The log message content.")
    severity = models.CharField(
        max_length=10,
        choices=SEVERITY_CHOICES,
        default='INFO',
        help_text="Severity level of the log."
    )
    raw_log = models.TextField(help_text="The original raw log line.")
    is_anomaly = models.BooleanField(default=False, help_text="Flag indicating if this log entry is considered an anomaly.")

    def __str__(self):
        return f"[{self.timestamp}] [{self.severity}] {self.source}: {self.message[:50]}..."

    class Meta:
        ordering = ['-timestamp'] # Default ordering for queries
        verbose_name = "Log Entry"
        verbose_name_plural = "Log Entries"

    # Timestamp ordering validation: 
    # Ensuring that new log entries always have a timestamp greater than or equal to the latest existing log entry 
    # is typically handled at the data ingestion layer or by database constraints rather than model validation.
    # Django's ORM doesn't provide a straightforward way to validate a field against aggregate values (like MAX(timestamp)) 
    # of other rows in the table during a single model's save() operation without complex queries.
    # For now, we rely on the data source providing logs in chronological order or pre-processing them.

class AnomalyReport(models.Model):
    log_entry = models.ForeignKey(LogEntry, on_delete=models.CASCADE, related_name='anomaly_reports',
                                  help_text="The log entry identified as an anomaly.")
    reported_at = models.DateTimeField(auto_now_add=True, help_text="When this anomaly report was created.")
    reason = models.TextField(help_text="Explanation of why this log is considered an anomaly.")
    bert_model_used = models.CharField(max_length=100, blank=True, null=True, help_text="Name or version of the BERT model used for detection.")
    bert_score = models.FloatField(blank=True, null=True, help_text="Confidence score from the BERT model.")
    acknowledged = models.BooleanField(default=False, help_text="Has this anomaly been reviewed and acknowledged?")
    notes = models.TextField(blank=True, null=True, help_text="Additional notes from reviewers.")

    def __str__(self):
        return f"Anomaly Report for Log ID {self.log_entry.id} at {self.reported_at}"

    class Meta:
        ordering = ['-reported_at']
        verbose_name = "Anomaly Report"
        verbose_name_plural = "Anomaly Reports"
