class BaseStr(str):
    max_length = 1024

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        v = v.strip()
        if len(v) > ProductName.max_length:
            raise ValueError(f'{cls.__name__} too long, max length is {cls.max_length}')
        return v


class GoodsID(BaseStr):
    max_length = 128

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(
            type='string',
            examples=['12345', 'f23t'],
        )


class ProductName(BaseStr):
    max_length = 1024

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(
            type='string',
            examples=['POTATO', 'shampoo'],
        )


class CategoryName(BaseStr):
    max_length = 1024

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(
            type='string',
            examples=['life', 'sport'],
        )
