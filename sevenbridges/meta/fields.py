import six
from uuid import UUID
from datetime import datetime
from sevenbridges.errors import ReadOnlyPropertyError, ValidationError

empty = object()


# noinspection PyProtectedMember
class Field(object):
    def __init__(self, name=None, read_only=True, validator=None):
        self.name = name
        self.read_only = read_only
        self.validator = validator

    def __set__(self, instance, value):
        # using empty as sentinel, value can be only set once - first time
        if self.read_only and instance._data[self.name] is not empty:
            raise ReadOnlyPropertyError(
                'Property {} is marked as read only!'.format(self.name)
            )
        self.validate(value)
        try:
            current_value = instance._data[self.name]
            if current_value == value:
                return
        except KeyError:
            pass
        instance._dirty[self.name] = value
        instance._data[self.name] = value

    def __get__(self, instance, cls):
        try:
            data = instance._data[self.name]
            if data and (isinstance(self, CompoundField) or isinstance(
                    self, CompoundListField)):
                if self.name not in instance._compound_cache:
                    instance._compound_cache[self.name] = self.cls(**data)
                    return instance._compound_cache[self.name]
                else:
                    return instance._compound_cache[self.name]

            # This should be in DateTimeField
            elif data and isinstance(self, DateTimeField):
                return datetime.strptime(data, '%Y-%m-%dT%H:%M:%SZ')
            else:
                return data
        except (KeyError, AttributeError):
            return None

    def validate(self, value):
        if self.validator is not None:
            self.validator(value)


class CompoundField(Field):
    def __init__(self, cls, name=None, read_only=False):
        super(CompoundField, self).__init__(name=name, read_only=read_only)
        self.cls = cls


class DictField(Field, dict):
    def __init__(self, name=None, read_only=False):
        super(DictField, self).__init__(name=name, read_only=read_only)


class HrefField(Field):
    def __init__(self, name=None):
        super(HrefField, self).__init__(name=name)


class ObjectIdField(Field):
    def __init__(self, name=None, read_only=True):
        super(ObjectIdField, self).__init__(name=name, read_only=read_only)


class IntegerField(Field):
    def __init__(self, name=None, read_only=False):
        super(IntegerField, self).__init__(name=name, read_only=read_only)

    def validate(self, value):
        if value and not isinstance(value, six.integer_types):
            raise ValidationError(
                '{} is not a valid value for {}'.format(
                    value, self.__class__.__name__
                )
            )


class FloatField(Field):
    def __init__(self, name=None, read_only=False):
        super(FloatField, self).__init__(name=name, read_only=read_only)

    def validate(self, value):
        try:
            float(value)
        except ValueError:
            raise ValidationError(
                '{} is not a valid value for {}'.format(
                    value, self.__class__.__name__
                )
            )


class StringField(Field):
    def __init__(self, name=None, read_only=False, max_length=None):
        super(StringField, self).__init__(name=name, read_only=read_only)
        self.max_length = max_length

    def validate(self, value):
        super(StringField, self).validate(value)
        if value and not isinstance(value, six.string_types):
            raise ValidationError(
                '{} is not a valid value for {}'.format(
                    value, self.__class__.__name__)
            )
        if self.max_length is not None and len(value) > self.max_length:
            raise ValidationError('{}: max length exceeded.'.format(self.name))


class DateTimeField(Field):
    def __init__(self, name=None, read_only=True):
        super(DateTimeField, self).__init__(name=name, read_only=read_only)


class BooleanField(Field):
    def __init__(self, name=None, read_only=False):
        super(BooleanField, self).__init__(name=name, read_only=read_only)

    def validate(self, value):
        if value and not isinstance(value, bool):
            raise ValidationError(
                '{} is not a valid value for {}'.format(
                    value, self.__class__.__name__
                )
            )


class UuidField(Field):
    def __init__(self, name=None, read_only=True):
        super(UuidField, self).__init__(name=name, read_only=read_only)

    def validate(self, value):
        super(UuidField, self).validate(value)
        try:
            UUID(value, version=4)
        except ValueError:
            raise ValidationError(
                '{} is not a valid value for {}'.format(
                    value, self.__class__.__name__)
            )


class BasicListField(Field):
    def __init__(self, name=None, read_only=False, max_length=None):
        super(BasicListField, self).__init__(name=name, read_only=read_only)
        self.max_length = max_length

    def validate(self, value):
        super(BasicListField, self).validate(value)
        if value and not isinstance(value, list):
            raise ValidationError('Validation failed, not a list.')
        if self.max_length is not None and len(value) > self.max_length:
            raise ValidationError(
                'Exceeded {} allowed elements.'.format(self.max_length)
            )


class CompoundListField(Field):
    def __init__(self, cls, name=None, read_only=True):
        super(CompoundListField, self).__init__(name=name, read_only=read_only)
        self.cls = cls
