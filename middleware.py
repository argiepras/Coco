from nation.models import *
from django.utils.deprecation import MiddlewareMixin
from django.http import HttpResponse


class Banmiddleware(MiddlewareMixin):
    def __init__(self, get_response=None):
        self.get_response = get_response

    def process_request(self, request):
        # Code to be executed for each request before
        # the view (and later middleware) are called.
        for x in range(40):
            print x
        print "shit is fugged yo"
        if True:
            response = HttpResponse('yuo are baned ;_;')
        else:
            response = get_response(request)
        print response
        return response
