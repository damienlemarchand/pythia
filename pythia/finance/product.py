# -*- coding: utf-8 -*-
"""
Created on 2018-12-14

"""


def no_flows(le_np_id, bu_unit, flow_from, position_array):
    """
    Default flow factory
    :param flow_from:
    :param position_array:
    :return:
    """
    return []


def factory_no_flows(data_dict):
    return no_flows


def create_product_registry():
    product_registry = {'default': {
        'default': {
            'factory': factory_no_flows
        }}}
    return product_registry


def create_product(product_registry, product_type, product_id, factory_flows, data_dict):
    if product_type not in product_registry:
        product_registry[product_type] = {}
    if product_id not in product_registry[product_type]:
        if not factory_flows:
            product_registry[product_type][product_id] = {'factory': factory_no_flows, 'events': []}
        else:
            product_registry[product_type][product_id] = {'factory': factory_flows, 'events': []}
    for key in data_dict:
        product_registry[product_type][product_id][key] = data_dict[key]


def find_flow_generator(product_registry, product_type, product_id, local_data=None):
    """
        Parse the product_registry to find the most specific generator of flow
    :param product_registry:
    :param product_type:
    :param product_id:
    :param local_data: local_data is a way to override data found in the product registry
    :return:
    """
    key_product_type = product_type
    if key_product_type not in product_registry:
        key_product_type = "default"
    key_product_id = product_id
    if key_product_id not in product_registry[key_product_type]:
        key_product_id = "default"
    data = product_registry[key_product_type][key_product_id]
    factory_fct = None
    if local_data:
        if 'factory' in local_data:
            factory_fct = local_data['factory']
    if not factory_fct:
        if 'factory' in data:
            factory_fct = data['factory']
    if not factory_fct:
        if 'factory' in product_registry[key_product_type]:
            factory_fct = product_registry[key_product_type]['factory']
    if not factory_fct:
        # no need to merge local data
        return factory_no_flows(data_dict=data)
    if local_data:
        merge_data = dict()
        for key in data:
            merge_data[key] = data[key]
        # local_data can override global data found in the registry
        for key in local_data:
            merge_data[key] = local_data[key]
        return factory_fct(data_dict=merge_data)
    return factory_fct(data_dict=data)


def build_amount(data_dict) -> tuple[float, float, float]:
    """
    Function extract amount, tax_amount, net_tax_amount information from the data dict
    Function handles optional case and finally return the amount and the eventually split of the amount
    between tax amount and net tax amount
    :param data_dict:
    :return:
    """
    amount = data_dict.get('amount', None)
    tax_amount = data_dict.get('tax_amount', None)
    net_tax_amount = data_dict.get('net_tax_amount', None)
    if not amount:
        if net_tax_amount:
            amount = net_tax_amount
        if tax_amount:
            if amount:
                amount = amount + tax_amount
            else:
                amount = tax_amount
    else:
        if net_tax_amount and not tax_amount:
            tax_amount = amount - net_tax_amount
        if not net_tax_amount and tax_amount:
            net_tax_amount = amount - tax_amount
        if not net_tax_amount and not tax_amount:
            net_tax_amount = amount
            tax_amount = float(0)
    return amount, net_tax_amount, tax_amount


def build_single_amount_product(data_dict):
    """from_le_np_id,
                          creditor_le_np_id,
                          amount,
                          currency,
                          issue_date,
                          payment_roll,
                          product_type = "INVOICE"):
    """
    flow_date = data_dict.get('flow_date', None)
    flow_type = data_dict.get('flow_type', "BULLET")
    currency = data_dict.get('currency', None)
    le_np_id_from = data_dict.get('le_np_id_from', None)
    le_np_id_to = data_dict.get('le_np_id_to', None)
    amount, net_tax_amount, tax_amount = build_amount(data_dict)

    def generate_flows(le_np_id, bu_unit, flow_from, position_array):
        flows = []
        if flow_date >= flow_from:
            quantity = float(0)
            for position in position_array:
                if position['from_date'] <= flow_date:
                    if not position['to_date']:
                        quantity = position['quantity']
                    else:
                        if position['to_date'] > flow_date:
                            quantity = position['quantity']
            if le_np_id == le_np_id_from:
                quantity = quantity * -1.0
            if quantity and amount:
                flow_amount = amount * quantity
                flow_tax_amount = tax_amount * quantity
                flow_net_tax_amount = net_tax_amount * quantity
                payment_flow = {'value_date': flow_date,
                                'product_type': 'CURRENCY',
                                'product_id': currency,
                                'flow_type': flow_type,
                                'from_le_np_id': le_np_id_from,
                                'to_le_np_id': le_np_id_to,
                                'quantity': flow_amount}
                if flow_tax_amount:
                    payment_flow['tax_amount'] = flow_tax_amount
                if flow_net_tax_amount:
                    payment_flow['net_tax_amount'] = flow_net_tax_amount
                if bu_unit:
                    payment_flow['from_business_unit'] = bu_unit
                    payment_flow['to_business_unit'] = bu_unit
                flows.append(payment_flow)
        return flows
    return generate_flows
