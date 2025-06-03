from django.shortcuts import render
from rest_framework import generics
from .models import LogEntry
from .serializers import LogEntrySerializer
from .permissions import HMACPermission
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator


class LogEntryListCreate(generics.ListCreateAPIView):
    queryset = LogEntry.objects.all()
    serializer_class = LogEntrySerializer

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        HMACPermission is applied only for POST requests.
        """
        if self.request.method == 'POST':
            return [HMACPermission()]
        return super().get_permissions()

    @method_decorator(ratelimit(key='ip', rate='100/m', block=True), name='post') # Rate limit POST (ingestion)
    @method_decorator(ratelimit(key='ip', rate='500/m', block=True), name='get')  # More lenient rate limit for GET (listing)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

class LogEntryDetail(generics.RetrieveAPIView):
    queryset = LogEntry.objects.all()
    serializer_class = LogEntrySerializer

    # Consider adding rate limiting to LogEntryDetail if needed, e.g.:
    # @method_decorator(ratelimit(key='ip', rate='500/m', block=True), name='get')
    # def dispatch(self, *args, **kwargs):
    #     return super().dispatch(*args, **kwargs)


def index_view(request):
    """Renders the main dashboard page."""
    return render(request, 'warden_app/index.html')
