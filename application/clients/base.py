import logging
from http import HTTPStatus
from json import JSONDecodeError
from typing import Optional, Tuple, Union, TypeVar, TYPE_CHECKING, Type
from urllib.parse import urljoin

import pydantic
import requests
import requests.adapters
import urllib3

if TYPE_CHECKING:
    SchemaModel = TypeVar('SchemaModel', bound='pydantic.BaseModel')


class Client:
    base_url = ''
    session: requests.Session = None
    timeout: Union[None, int, Tuple[int, int]] = None

    def __init__(self):
        self.session = self.session or requests.Session()
        self.logger = logging.getLogger(f'client.{self.__class__.__name__}')

    def get(self, path, **kwargs) -> requests.Response:
        return self.make_request('GET', path, **kwargs)

    def make_request(self, method, path, **kwargs) -> requests.Response:
        self.logger.info('Start request to path=%s', path)
        try:
            response = self.session.request(
                method=method,
                url=urljoin(self.base_url, path),
                timeout=self.timeout,
                **kwargs,
            )
        except requests.exceptions.RequestException:
            self.logger.exception('Fail get response path=%s', path)
            raise ClientException('Fail request')

        if response.status_code >= HTTPStatus.BAD_REQUEST:
            self.logger.warning('Response with fail status=%s path=%s, content=%s',
                                response.status_code, path, response.text)
            raise
        self.logger.info('Got success response path=%s', path)
        return response


class JSONClient(Client):
    def parse_json_response(
        self,
        response: requests.Response,
        schema: Type['SchemaModel'],
    ) -> 'SchemaModel':
        try:
            response_body = response.json()
        except JSONDecodeError:
            self.logger.exception('Parse json error')
            raise ClientException('Fail in parsing json body')

        try:
            return schema.parse_obj(response_body)
        except pydantic.ValidationError:
            self.logger.exception('Schema can not parse response')
            raise ClientException(f'{schema.__class__.__name__} can not parse response')


class ClientException(Exception):
    pass


class Session(requests.Session):
    def __init__(self, retry_policy: Optional[urllib3.Retry] = None):
        super().__init__()
        adapter = requests.adapters.HTTPAdapter(max_retries=retry_policy)
        self.mount('http://', adapter)
        self.mount('https://', adapter)

    @classmethod
    def create_with_retry_policy(cls, **retry_policy_kwargs):
        return cls(retry_policy=make_retry(**retry_policy_kwargs))


def make_retry(
    total=10,
    connect=5,
    read=5,
    backoff_factor=0.3,
    status=5,
    status_forcelist=frozenset([HTTPStatus.INTERNAL_SERVER_ERROR, HTTPStatus.BAD_GATEWAY]),
    **kwargs,
):
    """
    https://urllib3.readthedocs.io/en/latest/reference/urllib3.util.html#module-urllib3.util.retry

    total: Total number of retries to allow
    connect: How many connection-related errors to retry on.
    backoff_factor: A backoff factor to apply between attempts after the second try.
    status: How many times to retry on bad status codes.
    status_forcelist: A set of integer HTTP status codes that we should force a retry on.
    """
    return urllib3.Retry(
        total=total,
        connect=connect,
        read=read,
        backoff_factor=backoff_factor,
        status=status,
        status_forcelist=set(status_forcelist),
        **kwargs,
    )
