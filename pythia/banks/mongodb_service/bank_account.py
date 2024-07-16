# -*- coding: utf-8 -*-
"""
Created on 2021-12-02

"""
import pandas as pd
import numpy as np


BANK_ACCOUNT_FIELDS = ['_id', 'bank_code', 'bic', 'iban_code', 'account_code', 'currency',
                       'label', 'account_type', 'opening_date', 'domain']


def build_query_accounts(**kwargs):
    """
    build the query dict according to input parameters to request the bank statement collection
    """
    query = {}
    if 'bank_code' in kwargs:
        query['bank_code'] = kwargs['bank_code']
    if 'domain' in kwargs:
        query['domain'] = kwargs['domain']
    if 'account_type' in kwargs:
        query['account_type'] = kwargs['account_type']
    if 'account_code' in kwargs:
        param_account_code = kwargs['account_code']
        if isinstance(param_account_code, list):
            query['account_code'] = {'$in': param_account_code}
        else:
            query['account_code'] = param_account_code
    return query


def query_accounts(bank_accounts_collection, **kwargs):
    """
    run the query dict according to input parameters to request the bank account collection
    """                 
    data_struct = {}
    for field in BANK_ACCOUNT_FIELDS:
        data_struct[field] = []
    query = build_query_accounts(**kwargs)
    result = bank_accounts_collection.find(query)
    for statement in result:
        for field in BANK_ACCOUNT_FIELDS:
            if field in statement:
                data_struct[field].append(statement[field])
            else:
                data_struct[field].append(np.nan)
    return pd.DataFrame(data=data_struct)


def find_one_bank_account_id(bank_accounts_collection, **kwargs):
    """
     query bank account according to the input parameters and return the id of the first record
    """
    query = build_query_accounts(**kwargs)
    result = bank_accounts_collection.find(query)
    for statement in result:
        return statement['_id']
    return None    


def find_bank_account_id(bank_accounts_collection, domain: str, bank_code: str, account_code: str):
    return find_one_bank_account_id(bank_accounts_collection, bank_code=bank_code, domain=domain,
                                    account_code=account_code)


def fill_bank_account_struct(bank_accounts_collection):
    bank_accounts = query_accounts(bank_accounts_collection).apply(lambda x: x.to_dict(), axis=1).to_list()
    data_struct = {}
    for bank_account in bank_accounts:
        data_struct[bank_account['account_code']] = bank_account
    return data_struct
