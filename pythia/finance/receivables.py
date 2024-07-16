# -*- coding: utf-8 -*-
"""
Created on 2019-01-04

"""

import pythia.finance.product as py_fi_pr
import pythia.finance.engine as py_fi_ng
from pythia.time.dateroll import build_roll


def receivable_flow_builder(data_dict):
    flow_date = data_dict.get('flow_date', None)
    flow_type = data_dict.get('flow_type', "BULLET")
    currency = data_dict.get('currency', None)
    le_np_id_obligor = data_dict.get('le_np_id_obligor', None)
    le_np_id_creditor = data_dict.get('le_np_id_creditor', None)
    amount, net_tax_amount, tax_amount = py_fi_pr.build_amount(data_dict)

    def generate_flows(le_np_id, bu_unit, flow_from, position_array):
        flows = []
        if flow_date >= flow_from:
            quantity = float(0)
            selected_position = py_fi_ng.select_position(position_array, flow_date)
            if selected_position:
                quantity = selected_position['quantity']
            le_np_id_from = None
            le_np_id_to = None
            if quantity:
                if quantity < 0:
                    # from obligor point of view
                    le_np_id_from = le_np_id
                    le_np_id_to = le_np_id_creditor
                    quantity = quantity * -1.0
                else:
                    # from creditor point of view, hold the risk
                    le_np_id_from = le_np_id_obligor
                    le_np_id_to = le_np_id
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


def create_invoice(product_registry,
                   invoice_id,
                   le_np_id_creditor,
                   le_np_id_debtor,
                   invoice_date,
                   currency,
                   amount,
                   tax_amount,
                   bu_unit,
                   calendar_dict,
                   payment_roll):
    dr = build_roll(payment_roll, calendars_dict=calendar_dict)
    payment_date = dr.roll(invoice_date)
    data_dict = {'product_id': invoice_id,
                 'payment_roll': payment_roll,
                 'flow_type': "INVOICE",
                 'currency': currency,
                 'le_np_id_debtor': le_np_id_debtor,
                 'le_np_id_creditor': le_np_id_creditor,
                 'flow_date': payment_date,
                 'amount': amount,
                 'tax_amount': tax_amount
                 }
    py_fi_pr.create_product(product_registry,
                            "INVOICE",
                            invoice_id,
                            receivable_flow_builder,
                            data_dict)
    trade = {
        'trade_id': "SETTLE_{}".format(invoice_id),
        'trade_date': invoice_date,
        'settle_date': invoice_date,
        'payment_date': invoice_date,
        'currency': 'EUR',
        'quantity': 1,
        'price': 0,
        'buyer_le_np_id': le_np_id_creditor,
        'seller_le_np_id': le_np_id_debtor,
        'product_type': 'INVOICE',
        'product_id': invoice_id,
        'business_unit': bu_unit
    }
    return trade


if __name__ == "__main__":
    registry = py_fi_pr.create_product_registry()
