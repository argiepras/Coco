from nation.models import *
from django.utils.deprecation import MiddlewareMixin
from django.http import HttpResponse
from nation.tasks import meta_processing


class Banmiddleware(MiddlewareMixin):
    def __init__(self, get_response=None):
        self.get_response = get_response

    def process_request(self, request):
        # Code to be executed for each request before
        # the view (and later middleware) are called.
        if Ban.objects.filter(IP=request.META.get('REMOTE_ADDR')).exists():
            return HttpResponse('yuo are baned ;_;')
        return get_response(request)


class Meta_middleware(MiddlewareMixin):
    def __init__(self, get_response=None):
        self.get_response = get_response

    def process_request(self, request):
        #storing metadata for last online and multi detection
        #delegated to a celery process because dbio
        if request.is_ajax() or request.user.is_authenticated:
            header = request.META.get('HTTP_USER_AGENT')
            referral = request.META.get('REFERER')
            ip = request.META.get('REMOTE_ADDR')
            pk = request.user.pk
            meta_processing.apply_async(args=[header, ip, pk, referral])
        return get_response(request)
