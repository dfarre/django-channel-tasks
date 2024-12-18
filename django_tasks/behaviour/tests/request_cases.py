import json

import requests

from rest_framework.test import APIClient


from django_tasks.http_status import HttpStatus
from django_tasks.typing import JSON


def get_test_credential(name: str):
    with open(f'.test_{name}.txt') as secret_file:
        return secret_file.read().strip()


class RequestResponseCase:
    """An HTTP request-response example, for testing and documentation purposes."""

    #: The base URL for all requests.
    base_url: str = 'http://127.0.0.1:8003'

    #: Headers included in all requests.
    default_request_headers: dict[str, str] = {
        'Authorization': f'Token {get_test_credential("token")}',
        'Content-Type': 'application/json',
    }

    #: The client instance to employ to perform requests.
    client = requests

    def __init__(self, method: str, uri: str, data: JSON = None, **headers: str):
        self.method = method.strip().lower()
        self.uri = uri.strip()
        self.data = data
        self.headers = headers
        self.headers.update(self.default_request_headers)
        self.perform()

    @property
    def response(self):
        return self._response

    @property
    def status_code(self) -> HttpStatus:
        return self._status_code

    @property
    def url(self) -> str:
        return f'{self.base_url}/{self.uri}'

    def generate_rst_lines(self, name: str | int = 'example'):
        yield f'**Request {name}**:\n\n'
        yield '.. sourcecode:: http\n\n'
        yield f'   {self.method.upper()} /{self.uri} HTTP/1.1\n'

        for key, header in self.headers.items():
            yield f'   {key.capitalize()}: {header}\n'

        if self.data:
            yield '   \n'
            for data_line in json.dumps(self.data, indent=4).splitlines():
                yield f'   {data_line}\n'

        yield f'\n**Response {name}**:\n\n'
        yield '.. sourcecode:: http\n\n'
        yield f'   HTTP/1.1 {self.status_code} {self.status_code.name}\n'

        for key, header in self.response.headers.items():
            yield f'   {key.capitalize()}: {header}\n'

        if getattr(self.response, 'data', None):
            yield '   \n'
            for data_line in json.dumps(self.response.data, indent=4).splitlines():
                yield f'   {data_line}\n'

    def perform(self):
        """Response property setter."""
        self._response = getattr(self.client, self.method)(self.url, data=self.data, headers=self.headers)
        self._status_code = HttpStatus(self.response.status_code)


class WsgiRequestResponseCase(RequestResponseCase):
    base_url = ''
    client = APIClient()


class HttpEndpointCaseSet:
    def __init__(self, file_name: str, *request_response_cases: RequestResponseCase):
        self.file_name = file_name
        self.cases = request_response_cases

    @property
    def rst_path(self) -> str:
        return f"sphinx/source/requests/{self.file_name}.rst"

    def write_rst(self):
        with open(self.rst_path, 'w') as rst_file:
            for request_response_case in self.cases:
                rst_file.writelines(request_response_case.generate_rst_lines())
                rst_file.write('\n')
