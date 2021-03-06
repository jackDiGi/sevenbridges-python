from concurrent.futures import ThreadPoolExecutor
from sevenbridges.http.client import HttpClient
from sevenbridges.models.app import App
from sevenbridges.models.invoice import Invoice
from sevenbridges.models.task import Task
from sevenbridges.models.user import User
from sevenbridges.models.project import Project
from sevenbridges.models.endpoints import Endpoints
from sevenbridges.models.file import File
from sevenbridges.models.billing_group import BillingGroup


class Api(HttpClient):
    """Api aggregates all resource classes into single place"""

    users = User
    endpoints = Endpoints
    projects = Project
    files = File
    apps = App
    billing_groups = BillingGroup
    invoices = Invoice
    tasks = Task

    def __init__(self, url=None, token=None, oauth_token=None, config=None,
                 timeout=None, retry=5, download_max_workers=32,
                 upload_max_workers=16):
        """
        Initializes api object. If url and token are not supplied,
        the check for the .sbgrc configuration file will occur, checking if the
        section with the profile name is present in the .ini like configuration
        file. If profile is missing os.environ will be checked for auth-token
        and api-url variables.

        :param url: Api url.
        :param token: Secure token.
        :param oauth_token: Oauth token.
        :param config: Configuration profile.
        :param timeout: Client timeout.
        :param retry: Number of retries.
        :param download_max_workers: Max number of threads for download.
        :param upload_max_workers: Max number of threads for upload.
        :return: Api object instance.
        """
        super(Api, self).__init__(url=url, token=token,
                                  oauth_token=oauth_token,
                                  config=config, retry=retry, timeout=timeout)

        self.download_pool = ThreadPoolExecutor(
            max_workers=download_max_workers)
        self.upload_pool = ThreadPoolExecutor(max_workers=upload_max_workers)
