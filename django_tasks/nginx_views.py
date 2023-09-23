import os

from django import http, urls, views
from django.contrib.auth.decorators import login_required


class NginxAccelRedirectView(views.View):
    #: These headers are cleared-out so that Nginx can serve their own
    nginx_headers = ['Content-Type',
                     'Content-Disposition',
                     'Accept-Ranges',
                     'Set-Cookie',
                     'Cache-Control',
                     'Expires']
    location = ''

    @classmethod
    def get_url_path(cls, location: str, **kwargs):
        assert location, 'A prefix is required'
        return urls.path(os.path.join(location, '<path:path>').strip('/'),
                         login_required(cls.as_view(location=location)),
                         **kwargs)

    def get(self, request, path, *args, **kwargs):
        response = http.HttpResponse()

        for ignored_header in self.nginx_headers:
            del response[ignored_header]

        response['X-Accel-Redirect'] = f"/_{self.location.strip('/')}/{path}"

        return response


class NginxFileView(NginxAccelRedirectView):
    def get(self, request, path, *args, **kwargs):
        response = super().get(request, path, *args, **kwargs)
        response['Content-Disposition'] = f'attachment; filename="{path}"'
        return response
