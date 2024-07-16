# -*- coding: utf-8 -*-
"""
Created on 2021-11-18

"""
from bson.objectid import ObjectId
import pandas as pd
import pythia.utility as py_ut
import pythia.banks.mongodb_service.bank_account as py_ba

BANK_STATEMENT_FIELDS = ['_id', 'as_of_date', 'record_date', 'bank_code', 'account_code', 'label',
                         'currency_code', 'debit', 'credit', 'amount', 'domain']


def build_query_statements(**kwargs) -> dict:
    """
    build the query dict according to input parameters to request the bank statement collection
    """
    query = {}
    if 'id' in kwargs:
        query['_id'] = ObjectId(kwargs['id'])
    if 'bank_code' in kwargs:
        query['bank_code'] = kwargs['bank_code']
    if 'domain' in kwargs:
        query['domain'] = kwargs['domain']
    if 'account_code' in kwargs:
        param_account_code = kwargs['account_code']
        if isinstance(param_account_code, list):
            query['account_code'] = {'$in': param_account_code}
        else:
            query['account_code'] = param_account_code
    if 'max_date' in kwargs:
        if 'as_of_date' in query:
            query['as_of_date']["$lt"] = py_ut.to_datetime(kwargs['max_date'])
        else:
            query['as_of_date'] = {"$lt": py_ut.to_datetime(kwargs['max_date'])}
    if 'min_date' in kwargs:
        if 'as_of_date' in query:
            query['as_of_date']["$gte"] = py_ut.to_datetime(kwargs['min_date'])
        else:
            query['as_of_date'] = {"$gte": py_ut.to_datetime(kwargs['min_date'])}
    if 'creditor' in kwargs:
        query['credit'] = {"$gt": 0}
    if 'debtor' in kwargs:
        query['debit'] = {"$gt": 0}
    return query


def query_statements_as_dict(bank_statements_collection, **kwargs):
    data_struct = {}
    for field in BANK_STATEMENT_FIELDS:
        data_struct[field] = []
    query = build_query_statements(**kwargs)
    result = bank_statements_collection.find(query)
    for statement in result:
        add = True
        if 'allocated' in kwargs:
            if kwargs['allocated']:
                add = is_bank_statement_allocated(statement)
            else:
                add = not is_bank_statement_allocated(statement)
        if 'label' in kwargs:
            if kwargs['label'] not in statement['label']:
                add = False
        if add:    
            for field in BANK_STATEMENT_FIELDS:
                if field in statement:
                    data_struct[field].append(statement[field])
                else:
                    data_struct[field].append(None)
    return data_struct           


def query_statements(bank_statements_collection, **kwargs):
    data_struct = query_statements_as_dict(bank_statements_collection, **kwargs)
    return pd.DataFrame(data=data_struct)


def query_balances(bank_statements_collection, bank_accounts_collection, **kwargs) -> pd:
    query = build_query_statements(**kwargs)
    cursors = bank_statements_collection.aggregate([
        {'$match':  query},
        {'$group': {'_id': "$account_code", 'debit': {'$sum': '$debit'}, 'credit': {'$sum': '$credit'},
                    'amount': {'$sum': '$amount'}}}
    ])
    data_struct = {
        'account_code': [],
        'account_label': [],
        'account_type': [],
        'debit': [],
        'credit': [],
        'amount': []
    }
    bank_accounts = py_ba.fill_bank_account_struct(bank_accounts_collection)

    for statement in cursors:        
        data_struct['account_code'].append(statement['_id'])
        data_struct['debit'].append(statement['debit'])
        data_struct['credit'].append(statement['credit'])
        data_struct['amount'].append(statement['amount'])
        if statement['_id'] in bank_accounts:
            data_struct['account_label'].append(bank_accounts[statement['_id']]['label'])
            data_struct['account_type'].append(bank_accounts[statement['_id']]['account_type'])
        else:
            data_struct['account_label'].append(None)
            data_struct['account_type'].append(None)    
    return pd.DataFrame(data=data_struct)


def query_statements_period(bank_statements_collection, **kwargs) -> pd:
    query = build_query_statements(**kwargs)
    cursors = bank_statements_collection.aggregate([
        {'$match': query},
        {'$group': {'_id': "$account_code", 'min_as_of_date': {'$min': '$as_of_date'},
                    'max_as_of_date': {'$max': '$as_of_date'},
                    'bank_code': {'$min': '$bank_code'}}}
    ])
    data_struct = {
        'bank_code': [],
        'account_code': [],
        'min_as_of_date': [],
        'max_as_of_date': []
    }
    for statement in cursors:
        data_struct['bank_code'].append(statement['bank_code'])
        data_struct['account_code'].append(statement['_id'])
        data_struct['min_as_of_date'].append(statement['min_as_of_date'])
        data_struct['max_as_of_date'].append(statement['max_as_of_date'])   
    return pd.DataFrame(data=data_struct)


def allocate_bank_statement(bank_statements_collection, bank_statement, budget_allocation):
    """
    allocate the bank statement to one or several budget allocation. 
    The budget allocation should be an array of dict.
    Each item in this array is a structure : 
            * budget_code : the identifier of the budget category
            * ratio : optional, a float, set the amount ratio allocated to the budget code. max : 1.0; min : 0.0
            * amount: optional, a float, set the amount allocated to the budget code. max : Max(0.0,statement.amount);
            min : Min(0.0,statement.amount)
    """
    bank_statements_collection.update_one({'_id': bank_statement['_id']}, {'$set': {'allocations': budget_allocation}})


def allocate_bank_statements(bank_statements_collection, bank_statements: pd, budget_allocation):
    """
    allocate the bank statements (pd dataframes) to the same budget allocation
    """
    for bank_statement in bank_statements.apply(lambda x: x.to_dict(), axis=1).to_list():
        allocate_bank_statement(bank_statements_collection, bank_statement, budget_allocation)


def unset_bank_statement_allocation(bank_statements_collection, bank_statement):
    bank_statements_collection.update_one({'_id': bank_statement['_id']}, {'$unset': {'allocations': ''}})


def is_bank_statement_allocated(bank_statement: dict) -> bool:
    """
    check the content of the bank_statement
    """
    allocated_amount = float(0)
    if 'allocations' in bank_statement:        
        for allocation in bank_statement['allocations']:
            if 'ratio' in allocation:
                allocated_amount = allocated_amount + (allocation['ratio'] * bank_statement['amount'])
            else:     
                if 'amount' in allocation:
                    allocated_amount = allocated_amount + allocation['amount']
                else:
                    allocated_amount = allocated_amount + (float(1.0) * bank_statement['amount'])
        return allocated_amount == bank_statement['amount']
    return False
          

def mark_as_internal_bank_statement(bank_statements_collection, bank_statement: dict):
    """
    allocate fully the bank statement to the internal category. Reserved for statement identified as a xfer
    between two accounts
    """
    return allocate_bank_statement(bank_statements_collection, bank_statement,
                                   [{'budget_code': 'internal', 'ratio': float(1)}])


def to_budget_line(bank_statement, budget_code, ratio=None, amount=None) -> dict:
    """
    create a budget line for a bank_statement, an allocation to a budget code and a ratio/amount.
    The full amount is allocated per default (neither ratio nor amount)
    """
    primary_budget_code = budget_code
    codes = budget_code.split(".")
    if len(codes) > 0:
        primary_budget_code = codes[0]
    if ratio:
        return {
            'bank_statement_id': bank_statement['_id'],
            'primary_budget_code': primary_budget_code,
            'budget_code': budget_code,
            'record_date': bank_statement['record_date'],
            'label': bank_statement['label'],
            'currency_code': bank_statement['currency_code'],
            'amount': bank_statement['amount']*ratio,
            'domain': bank_statement['domain']
        }
    if amount:
        local_ratio = float(1.0)
        if bank_statement['amount'] != float(0):
            if bank_statement['amount'] == amount:
                local_ratio = float(1.0)
            else:
                local_ratio = amount / bank_statement['amount']
        return {
            'bank_statement_id': bank_statement['_id'],
            'primary_budget_code': primary_budget_code,
            'budget_code': budget_code,
            'record_date': bank_statement['record_date'],
            'label': bank_statement['label'],
            'currency_code': bank_statement['currency_code'],
            'amount': bank_statement['amount']*local_ratio,
            'domain': bank_statement['domain']
        }
    return {
            'bank_statement_id': bank_statement['_id'],
            'primary_budget_code': primary_budget_code,
            'budget_code': budget_code,
            'record_date': bank_statement['record_date'],
            'label': bank_statement['label'],
            'currency_code': bank_statement['currency_code'],
            'amount': bank_statement['amount'],
            'domain': bank_statement['domain']
        }


def to_budget_lines(bank_statement):
    if 'allocations' in bank_statement:
        allocations = bank_statement['allocations']
        budget_lines = []
        for allocation in allocations:
            if 'ratio' in allocation:
                budget_lines.append(to_budget_line(bank_statement, allocation['budget_code'], allocation['ratio']))
            else:
                if 'amount' in allocation:    
                    budget_lines.append(to_budget_line(bank_statement, allocation['budget_code'], None,
                                                       allocation['amount']))
                else:
                    budget_lines.append(to_budget_line(bank_statement, allocation['budget_code']))
        return budget_lines
    # no allocation done => unaffected category
    return [to_budget_line(bank_statement, 'unaffected')]


BUDGET_LINE_FIELDS = ['_id', 'bank_statement_id', 'primary_budget_code', 'budget_code', 'record_date', 'label',
                      'currency_code', 'amount', 'domain']


def query_budget_lines_as_dict(bank_statements_collection, **kwargs) -> dict:
    data_struct = {}
    for field in BUDGET_LINE_FIELDS:
        data_struct[field] = []
    query = build_query_statements(**kwargs)
    bank_statements = bank_statements_collection.find(query)        
    for bank_statement in bank_statements:
        budget_lines = to_budget_lines(bank_statement)
        for budget_line in budget_lines:
            add = True
            if 'budget_code' in kwargs:
                if kwargs['budget_code'] not in budget_line['budget_code']:
                    add = False
            if add:
                for field in BUDGET_LINE_FIELDS:
                    if field in budget_line:
                        data_struct[field].append(budget_line[field])
                    else:
                        data_struct[field].append(None)   
    return data_struct


def query_budget_lines(bank_statements_collection, **kwargs) -> pd:
    data_struct = query_budget_lines_as_dict(bank_statements_collection, **kwargs)
    return pd.DataFrame(data=data_struct)
