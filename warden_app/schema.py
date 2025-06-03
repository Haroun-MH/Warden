import graphene
from graphene_django import DjangoObjectType
from .models import LogEntry, AnomalyReport

class LogEntryType(DjangoObjectType):
    class Meta:
        model = LogEntry
        fields = "__all__"

class AnomalyReportType(DjangoObjectType):
    class Meta:
        model = AnomalyReport
        fields = "__all__"

class Query(graphene.ObjectType):
    all_log_entries = graphene.List(LogEntryType)
    all_anomaly_reports = graphene.List(AnomalyReportType)
    log_entries_by_anomaly_score = graphene.List(
        LogEntryType,
        min_score=graphene.Float(),
        max_score=graphene.Float()
    )

    def resolve_all_log_entries(root, info):
        return LogEntry.objects.all()

    def resolve_all_anomaly_reports(root, info):
        return AnomalyReport.objects.all()

    def resolve_log_entries_by_anomaly_score(root, info, min_score=None, max_score=None):
        # This assumes AnomalyReport has a 'bert_score' and is related to LogEntry
        # and LogEntry has a way to access this score, e.g., via a related AnomalyReport.
        # For this example, let's assume a direct or indirect way to filter LogEntry by a score.
        # If LogEntry itself doesn't have a score, this query needs adjustment based on actual model relations.
        
        # Placeholder: Actual filtering logic will depend on how anomaly scores are stored and related to LogEntry.
        # This might involve joining with AnomalyReport and filtering on bert_score.
        # For now, returning all logs if no direct score field on LogEntry.
        # Example: return LogEntry.objects.filter(anomaly_reports__bert_score__gte=min_score) if using related AnomalyReport
        
        queryset = LogEntry.objects.filter(is_anomaly=True) # Initial filter for anomalous logs
        
        # We need to filter based on the bert_score in the related AnomalyReport
        # This requires a join and potentially distinct() if a LogEntry can have multiple AnomalyReports
        if min_score is not None:
            queryset = queryset.filter(anomaly_reports__bert_score__gte=min_score)
        if max_score is not None:
            queryset = queryset.filter(anomaly_reports__bert_score__lte=max_score)
            
        return queryset.distinct()

schema = graphene.Schema(query=Query)