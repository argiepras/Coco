from nation.models import *
from django.utils.deprecation import MiddlewareMixin
from django.http import HttpResponse
from nation.tasks import meta_processing


class Banmiddleware(MiddlewareMixin):
    def __init__(self, get_response=None):
        self.get_response = get_response

    def process_request(self, request):
        # the view (and later middleware) are called.
        if Ban.objects.filter(IP=request.META.get('REMOTE_ADDR')).exists():
            return HttpResponse('yuo are baned ;_;')


class Meta_middleware(MiddlewareMixin):
    def __init__(self, get_response=None):
        self.get_response = get_response

    def process_request(self, request):
        #storing metadata for last online and multi detection
        #delegated to a celery process because dbio
        try:
            header = request.META['HTTP_USER_AGENT']
        except:
            header = ''
        if 'ios' in header.lower() or \
        'android' in header.lower() or \
        'mobile' in header.lower():
            request.mobile = True
        else:
            request.mobile = False
        if not request.is_ajax() and not request.user.is_anonymous():
            referral = request.META.get('REFERER')
            ip = request.META.get('REMOTE_ADDR')
            pk = request.user.pk
            meta_processing.apply_async(args=[header, ip, pk, referral])
