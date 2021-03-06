import six

from sevenbridges.meta.resource import Resource
from sevenbridges.decorators import inplace_reload
from sevenbridges.meta.transformer import Transform
from sevenbridges.models.compound.download_info import DownloadInfo
from sevenbridges.models.compound.file_origin import FileOrigin
from sevenbridges.models.compound.metadata import Metadata
from sevenbridges.transfer.download import Download
from sevenbridges.meta.fields import (
    HrefField, StringField, IntegerField, CompoundField, DateTimeField
)
from sevenbridges.transfer.utils import PartSize


class File(Resource):
    """
    Central resource for managing files.
    """
    _URL = {
        'query': '/files',
        'get': '/files/{id}',
        'delete': '/files/{id}',
        'copy': '/files/{id}/actions/copy',
        'download_info': '/files/{id}/download_info',
        'metadata': '/files/{id}/metadata'
    }

    href = HrefField()
    id = StringField()
    name = StringField(read_only=False)
    size = IntegerField(read_only=True)
    project = StringField(read_only=True)
    created_on = DateTimeField(read_only=True)
    modified_on = DateTimeField(read_only=True)
    origin = CompoundField(FileOrigin)
    metadata = CompoundField(Metadata, read_only=False)

    def __str__(self):
        return six.text_type('<File: id={id}>'.format(id=self.id))

    @classmethod
    def query(cls, project, names=None, metadata=None, origin=None,
              offset=None, limit=None, api=None):
        """
        Query ( List ) projects
        :param project: Project id
        :param names: Name list
        :param metadata: Metadata query dict
        :param origin: Origin query dict
        :param offset: Pagination offset
        :param limit: Pagination limit
        :param api: Api instance.
        :return: Collection object.
        """
        api = api or cls._API

        project = Transform.to_project(project)
        query_params = {}

        if names and isinstance(names, list):
            query_params['name'] = names

        metadata_params = {}
        if metadata and isinstance(metadata, dict):
            for k, v in metadata.items():
                metadata_params['metadata.' + k] = metadata[k]

        query_params.update(metadata_params)

        origin_params = {}
        if origin and isinstance(origin, dict):
            for k, v in origin.items():
                origin_params['origin.' + k] = origin[k]

        query_params.update(origin_params)

        return super(File, cls)._query(api=api, url=cls._URL['query'],
                                       project=project, offset=offset,
                                       limit=limit, **query_params)

    def copy(self, project, name=None):
        """
        Copies the current file.
        :param project: Destination project.
        :param name: Destination file name.
        :return: Copied File object.
        """
        project = Transform.to_project(project)
        data = {
            'project': project
        }
        if name:
            data['name'] = name
        new_file = self._api.post(url=self._URL['copy'].format(id=self.id),
                                  data=data).json()
        return File(api=self._api, **new_file)

    def download_info(self):
        """
        Fetches download information containing file url
        that can be used to download file.
        :return: Download info object.
        """
        info = self._api.get(url=self._URL['download_info'].format(id=self.id))
        return DownloadInfo(api=self._api, **info.json())

    def download(self, path, retry=5, timeout=10, chunk_size=67108864,
                 wait=True):
        """
        Downloads the file and returns a download handle.
        Download will not start until .start() method is invoked.
        :param path: Full path to the new file/
        :param retry:  Number of retries if error occurs during download.
        :param timeout:  Timeout for http requests.
        :param chunk_size:  Chunk size in bytes.
        :param wait: If true will wait for download to complete.
        :return: Download handle.
        """
        info = self.download_info()
        download = Download(url=info.url, file_path=path, retry=retry,
                            timeout=timeout,
                            chunk_size=chunk_size, api=self._api)
        if wait:
            download.start()
            download.wait()
        else:
            return download

    @inplace_reload
    def save(self, inplace=True):
        """
        Saves all modification to the file on the server.
        :param inplace Apply edits to the current instance or get a new one.
        :return: File instance.
        """
        modified_data = self._modified_data()
        if bool(modified_data):
            if 'metadata' in modified_data:
                self._api.patch(url=self._URL['metadata'].format(id=self.id),
                                data=modified_data['metadata'])
                self.metadata.dirty = {}
                return self.get(id=self.id)

            else:
                data = self._api.patch(url=self._URL['get'].format(id=self.id),
                                       data=modified_data).json()
                file = File(api=self._api, **data)
                return file

    def stream(self, part_size=32 * PartSize.KB):
        """
        Creates an iterator which can be used to stream the file content.
        :param part_size: Size of the part in bytes. Default 32KB
        :return Iterator
        """
        download_info = self.download_info()
        response = self._api.get(
            url=download_info.url, stream=True, append_base=False
        )
        for part in response.iter_content(part_size):
            yield part
