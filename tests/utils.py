import os
from logging import getLogger

import pytest


log = getLogger(os.path.basename(__file__).split('.')[0])


def pretty_parametrize(test_data, id_field='id', use_id_field_as_param=False):
    """Parametrize tests by test_data value: list of dict with test case params

    Some sugar over pytest.mark.parametrize

    :param test_data: [list of dict] - pretty test data. Example:
    [
        {'a': 1, 'b':2, 'expected': '3'},
        ...
    ]
    test_data elements MUST be dicts, dicts MUST content identical lists of keys
    :param id_field: [str] - id field in test_data dictionaries, use as id in pytest.paramtrize
    :param use_id_field_as_param: [bool] - if true, id_field used in tests as parameter
    :return: [pytest.mark.parametrize result]
    """
    if len(test_data) == 0:
        raise AssertionError('Empty test_data list')

    contain_non_dict_element = any(not isinstance(d, dict) for d in test_data)
    if contain_non_dict_element:
        raise AssertionError('test_data param contain non-dict elements')

    list_with_keys = [list(d.keys()) for d in test_data]
    if (
        list_with_keys[1:] != list_with_keys[:-1]
    ):  # hack: check if all unhashible elements in list identical
        raise AssertionError('Keys in test_data are not identical')

    argnames = sorted(test_data[0].keys())
    keys_contain_id_field = bool(id_field in argnames)
    if keys_contain_id_field and not use_id_field_as_param:
        argnames.remove(id_field)

    argvalues = list()
    for test_data_element in test_data:
        argval = list()
        for argname in argnames:
            argval.append(test_data_element[argname])
        argvalues.append(argval)

    if keys_contain_id_field:
        ids = [d[id_field] for d in test_data]
        return pytest.mark.parametrize(argnames=argnames, argvalues=argvalues, ids=ids)
    else:
        return pytest.mark.parametrize(argnames=argnames, argvalues=argvalues)
