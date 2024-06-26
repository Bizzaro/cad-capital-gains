from datetime import date
import requests_mock as rm

from capgains.commands import capgains_calc as CapGainsCalc
from capgains.transaction import Transaction
from capgains.transactions import Transactions


def test_no_ticker(transactions, capfd, exchange_rates_mock):
    """Testing capgains_calc without any optional filters"""
    CapGainsCalc.capgains_calc(transactions, 2018)
    out, _ = capfd.readouterr()
    assert out == """\
ANET-2018
[Total Gains = 6,970.00]
+------------+---------------+----------+-------+------------+----------+-----------+---------------------+
| date       | description   | ticker   |   qty |   proceeds |      ACB |   outlays |   capital gain/loss |
|------------+---------------+----------+-------+------------+----------+-----------+---------------------|
| 2018-02-20 | RSU VEST      | ANET     |    50 |  12,000.00 | 5,010.00 |     20.00 |            6,970.00 |
+------------+---------------+----------+-------+------------+----------+-----------+---------------------+

GOOGL-2018
No capital gains

"""  # noqa: E501


def test_tickers(transactions, capfd, exchange_rates_mock):
    """Testing capgains_calc with a ticker"""
    CapGainsCalc.capgains_calc(transactions, 2018, ['ANET'])
    out, _ = capfd.readouterr()
    assert out == """\
ANET-2018
[Total Gains = 6,970.00]
+------------+---------------+----------+-------+------------+----------+-----------+---------------------+
| date       | description   | ticker   |   qty |   proceeds |      ACB |   outlays |   capital gain/loss |
|------------+---------------+----------+-------+------------+----------+-----------+---------------------|
| 2018-02-20 | RSU VEST      | ANET     |    50 |  12,000.00 | 5,010.00 |     20.00 |            6,970.00 |
+------------+---------------+----------+-------+------------+----------+-----------+---------------------+

"""  # noqa: E501


def test_no_transactions(capfd):
    """Testing capgains_calc without any transactions"""
    CapGainsCalc.capgains_calc(Transactions([]), 2018)
    out, _ = capfd.readouterr()
    assert out == """\
No transactions available
"""


def test_unknown_year(transactions, capfd, exchange_rates_mock):
    """Testing capgains_calc with a year matching no transactions"""
    CapGainsCalc.capgains_calc(transactions, 1998)
    out, _ = capfd.readouterr()
    assert out == """\
ANET-1998
No capital gains

GOOGL-1998
No capital gains

"""


def test_superficial_loss_not_displayed(capfd, exchange_rates_mock):
    """Testing capgains_calc with a superficial loss transaction"""
    transactions = [
        Transaction(
            date(2018, 1, 1),
            'ESPP PURCHASE',
            'ANET',
            'BUY',
            100,
            100.00,
            10.00,
            'USD'
        ),
        Transaction(
            date(2018, 1, 2),
            'RSU VEST',
            'ANET',
            'SELL',
            99,
            50.00,
            10.00,
            'USD'
        ),
        Transaction(
            date(2018, 12, 1),
            'RSU VEST',
            'ANET',
            'SELL',
            1,
            1000.00,
            10.00,
            'USD'
        )
    ]
    transactions = Transactions(transactions)
    CapGainsCalc.capgains_calc(transactions, 2018)
    out, _ = capfd.readouterr()
    assert out == """\
ANET-2018
[Total Gains = -8,160.00]
+------------+---------------+----------+-------+------------+-----------+-----------+---------------------+
| date       | description   | ticker   |   qty |   proceeds |       ACB |   outlays |   capital gain/loss |
|------------+---------------+----------+-------+------------+-----------+-----------+---------------------|
| 2018-12-01 | RSU VEST      | ANET     |     1 |   2,000.00 | 10,140.00 |     20.00 |           -8,160.00 |
+------------+---------------+----------+-------+------------+-----------+-----------+---------------------+

"""  # noqa: E501


def test_calc_mixed_currencies(capfd, requests_mock):
    """Testing capgains_calc with mixed currencies"""
    usd_transaction = Transaction(
        date(2017, 2, 15),
        'ESPP PURCHASE',
        'ANET',
        'BUY',
        100,
        50.00,
        0.00,
        'USD')
    cad_transaction = Transaction(
        date(2018, 2, 20),
        'RSU VEST',
        'ANET',
        'SELL',
        100,
        50.00,
        0.00,
        'CAD')
    transactions = Transactions([
        usd_transaction,
        cad_transaction
    ])

    usd_observations = [{
        'd': usd_transaction.date.isoformat(),
        'FXUSDCAD': {
            'v': '2.0'
        }
    }]
    requests_mock.get(rm.ANY, json={"observations": usd_observations})
    CapGainsCalc.capgains_calc(transactions, 2018)
    out, _ = capfd.readouterr()
    assert out == """\
ANET-2018
[Total Gains = -5,000.00]
+------------+---------------+----------+-------+------------+-----------+-----------+---------------------+
| date       | description   | ticker   |   qty |   proceeds |       ACB |   outlays |   capital gain/loss |
|------------+---------------+----------+-------+------------+-----------+-----------+---------------------|
| 2018-02-20 | RSU VEST      | ANET     |   100 |   5,000.00 | 10,000.00 |      0.00 |           -5,000.00 |
+------------+---------------+----------+-------+------------+-----------+-----------+---------------------+

"""  # noqa: E501


def test_partial_shares(capfd, requests_mock):
    """Testing capgains_calc with partial shares"""
    partial_buy = Transaction(
        date(2017, 2, 15),
        'ESPP PURCHASE',
        'ANET',
        'BUY',
        0.5,
        50.00,
        0.00,
        'CAD')
    partial_sell = Transaction(
        date(2018, 2, 20),
        'RSU VEST',
        'ANET',
        'SELL',
        0.5,
        100.00,
        0.00,
        'CAD')
    transactions = Transactions([
        partial_buy,
        partial_sell
    ])

    CapGainsCalc.capgains_calc(transactions, 2018)
    out, _ = capfd.readouterr()
    assert out == """\
ANET-2018
[Total Gains = 25.00]
+------------+---------------+----------+-------+------------+-------+-----------+---------------------+
| date       | description   | ticker   |   qty |   proceeds |   ACB |   outlays |   capital gain/loss |
|------------+---------------+----------+-------+------------+-------+-----------+---------------------|
| 2018-02-20 | RSU VEST      | ANET     |   0.5 |      50.00 | 25.00 |      0.00 |               25.00 |
+------------+---------------+----------+-------+------------+-------+-----------+---------------------+

"""  # noqa: E501
