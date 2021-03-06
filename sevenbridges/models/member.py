import six

from sevenbridges.errors import ResourceNotModified
from sevenbridges.meta.fields import HrefField, StringField, CompoundField
from sevenbridges.meta.resource import Resource
from sevenbridges.models.compound.permissions import Permissions


class Member(Resource):
    """
    Central resource for managing project members.
    """
    _URL = {
        'permissions': '/permissions'
    }

    href = HrefField()
    username = StringField(read_only=False)
    permissions = CompoundField(Permissions)

    def __str__(self):
        return six.text_type('<Member: username={username}>'
                             .format(username=self.username))

    def save(self):
        """
        Saves modification to the api server.
        """
        data = self._modified_data()
        try:
            data = data['permissions']
            if bool(data):
                url = six.text_type(self.href) + self._URL['permissions']
                self._api.patch(url=url, data=data, append_base=False)
        except KeyError:
            raise ResourceNotModified()
