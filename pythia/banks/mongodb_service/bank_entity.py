# -*- coding: utf-8 -*-
"""
Created on 2021-12-02

"""
import pandas as pd
import numpy as np


BANK_ENTITY_FIELDS = ['_id', 'bank_code', 'bic', 'label', 'domain']


def build_query_entities(**kwargs) -> dict:
    """
    query parameters :
        * bank_code: str
        * account_code:str
        * account_type:str
        * domain=None
    build the query dict according to input parameters to request the bank statement collection
    """
    query = {}
    if 'domain' in kwargs:
        query['domain'] = kwargs['domain']
    if 'account_type' in kwargs:
        query['account_type'] = kwargs['account_type']
    if 'bank_code' in kwargs:
        param_bank_code = kwargs['bank_code']
        if isinstance(param_bank_code, list):
            query['bank_code'] = {'$in': param_bank_code}
        else:
            query['bank_code'] = param_bank_code
    return query


def query_entities(bank_entities_collection, **kwargs) -> pd:
    """
    run the query dict according to input parameters to request the bank account collection and returns a panda dataset
    """                 
    data_struct = {}
    for field in BANK_ENTITY_FIELDS:
        data_struct[field] = []
    query = build_query_entities(**kwargs)
    result = bank_entities_collection.find(query)
    for statement in result:
        for field in BANK_ENTITY_FIELDS:
            if field in statement:
                data_struct[field].append(statement[field])
            else:
                data_struct[field].append(np.nan)
    return pd.DataFrame(data=data_struct)


def find_one_bank_entity_id(bank_entities_collection, **kwargs):
    query = build_query_entities(**kwargs)
    result = bank_entities_collection.find(query)
    for statement in result:
        return statement['_id']
    return None


def find_bank_id(bank_entities_collection, domain, bank_code):
    """
    return the bank id for one domain & bank code
    """
    return find_one_bank_entity_id(bank_entities_collection, bank_code=bank_code, domain=domain)
