import click
import tabulate
from itertools import groupby
import csv

from capgains.exchange_rate import ExchangeRate
from capgains.ticker_gains import TickerGains

# describes how to align the individual table columns
colalign = (
    "left",   # date
    "left",   # description
    "left",   # ticker
    "right",  # qty
    "right",  # proceeds
    "right",  # acb
    "right",  # commission
    "right",  # capital gain
)


def _get_total_gains(transactions):
    total = 0
    for t in transactions:
        total += t.capital_gain
    return total


def _get_map_of_currencies_to_exchange_rates(transactions):
    """First, split the list of transactions into sublists where each sublist
    will only contain transactions with the same currency"""

    contiguous_currencies = sorted(transactions.transactions,
                                   key=lambda t: t.currency)
    currency_groups = [list(g) for _, g in groupby(contiguous_currencies,
                                                   lambda t: t.currency)]
    currencies_to_exchange_rates = dict()
    # Create a separate ExchangeRate object for each currency
    for currency_group in currency_groups:
        currency = currency_group[0].currency
        min_date = currency_group[0].date
        max_date = currency_group[-1].date
        currencies_to_exchange_rates[currency] = ExchangeRate(
            currency, min_date, max_date)
    return currencies_to_exchange_rates


def calculate_gains(transactions, year, ticker):
    ticker_transactions = transactions.filter_by(tickers=[ticker],
                                                 max_year=year)
    er_map = _get_map_of_currencies_to_exchange_rates(ticker_transactions)
    tg = TickerGains(ticker)
    tg.add_transactions(ticker_transactions, er_map)
    # for every transactions class, there is a transaction class
    return ticker_transactions.filter_by(year=year, action='SELL', description="Stocks", superficial_loss=False)


def capgains_calc(transactions, year, tickers=None):
    """Take a list of transactions and print the calculated capital
    gains in a separate tabular format for each specified ticker."""
    filtered_transactions = transactions.filter_by(tickers=tickers)
    if not filtered_transactions:
        click.echo("No transactions available")
        return

    output_queue = []

    for ticker in filtered_transactions.tickers:
        transactions_to_report = calculate_gains(filtered_transactions, year,
                                                 ticker)
        if transactions_to_report:
            click.echo("{}-{}".format(ticker, year))

            total_gains = _get_total_gains(transactions_to_report)
            click.echo("[Total Gains = {0:,.2f}]".format(total_gains))
            headers = ["date", "description", "ticker", "qty", "proceeds", "ACB",
                       "outlays", "capital gain/loss"]
            rows = [[
                t.date,
                t.description,
                t.ticker,
                "{0:f}".format(t.qty.normalize()),
                "{:,.2f}".format(t.proceeds),
                "{:,.2f}".format(t.acb),
                "{:,.2f}".format(t.expenses),
                "{:,.2f}".format(t.capital_gain)
            ] for t in transactions_to_report]
            output = tabulate.tabulate(rows, headers=headers, tablefmt="psql",
                                       colalign=colalign, disable_numparse=True)
            click.echo("{}\n".format(output))

            for r in rows:
                # https://faq.mytaxexpress.com/index.php?action=faq&cat=8&id=137&artlang=en
                # myTaxExpress format: qty, stock name, sell price, buy price/acb, expense
                output_queue.append([r[3], r[2], r[4], r[5], r[6]])

    with open(f'schedule3-{year}.csv', 'w', encoding='UTF8', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(output_queue)
