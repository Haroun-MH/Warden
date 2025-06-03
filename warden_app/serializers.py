from rest_framework import serializers
from .models import LogEntry, AnomalyReport

class LogEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = LogEntry
        fields = '__all__'

class AnomalyReportSerializer(serializers.ModelSerializer):
    log_entry = LogEntrySerializer(read_only=True) # Or PrimaryKeyRelatedField for submission if needed
    
    class Meta:
        model = AnomalyReport
        fields = '__all__'