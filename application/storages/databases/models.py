from tortoise import Model, fields

PRODUCT_COLLECTION_NAME = 'goods'


class BaseModel(Model):
    id = fields.IntField(pk=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    modified_at = fields.DatetimeField(auto_now=True)


class Product(BaseModel):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._categories = set()
        self._images = set()
        self._specifications = set()

    goods_id = fields.CharField(max_length=128, index=True, unique=True)
    name = fields.CharField(max_length=1024)
    price = fields.DecimalField(max_digits=10, decimal_places=2)

    attributes: fields.ReverseRelation['ProductAttribute']
    categories: fields.ManyToManyRelation['Category']
    images: fields.ReverseRelation['ProductImage']

    class Meta:
        table = 'product'

    def __str__(self):
        return self.name


class ProductAttribute(BaseModel):
    product: fields.ForeignKeyRelation[Product] = fields.ForeignKeyField(
        'models.Product', related_name='attributes', index=True
    )
    name = fields.CharField(max_length=256, index=True, unique=True)
    value = fields.CharField(max_length=1024)

    class Meta:
        table = 'product_attribute'

    def __str__(self):
        return self.name


class Category(BaseModel):
    products: fields.ManyToManyRelation[Product] = fields.ManyToManyField(
        'models.Product',
        related_name='categories',
        index=True,
        through='product_category',
        on_delete=fields.SET_NULL,
    )
    parent_category: fields.OneToOneRelation['Category'] = fields.OneToOneField(
        'models.Category',
        related_name='child_category',
        null=True,
        on_delete=fields.SET_NULL,
    )
    name = fields.CharField(max_length=1024, index=True, unique=True)

    class Meta:
        table = 'category'
        ordering = ['created_at']

    def __str__(self):
        return self.name


class ProductImage(BaseModel):
    product: fields.ForeignKeyRelation[Product] = fields.ForeignKeyField(
        'models.Product', related_name='images', index=True
    )
    name = fields.CharField(max_length=256, index=True, unique=True)
    url = fields.CharField(max_length=512, index=True)

    class Meta:
        table = 'product_image'

    def __str__(self):
        return self.name
