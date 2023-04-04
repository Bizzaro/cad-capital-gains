from datetime import timedelta
from datetime import datetime
from decimal import Decimal
import click
import tabulate


class TickerGains:
    def __init__(self, ticker):
        self._ticker = ticker
        self._share_balance = 0
        self._total_acb = 0

    def add_transactions(self, transactions, exchange_rates):
        """Adds all transactions and updates the calculated values"""
        for t in transactions:
            rate = exchange_rates[t.currency].get_rate(t.date)
            t.exchange_rate = rate
            if (self._add_transaction(t)):
                if self._is_superficial_loss(t, transactions):
                    self._total_acb -= t.capital_gain
                    t.set_superficial_loss()

    def _superficial_window_filter(self, transaction, min_date, max_date):
        """Filter out BUY transactions that fall within
        the 61 day superficial loss window"""
        return transaction.date >= min_date and transaction.date <= max_date

    def _is_superficial_loss(self, transaction, transactions):
        """Figures out if the transaction is a superficial loss"""
        # Has to be a capital loss
        if (transaction.capital_gain >= 0):
            return False
        min_date = transaction.date - timedelta(days=30)
        max_date = transaction.date + timedelta(days=30)
        filtered_transactions = list(filter(
            lambda t: self._superficial_window_filter(t, min_date, max_date),
            transactions))
        # Has to have a purchase either 30 days before or 30 days after
        if (not any(t.action == 'BUY' for t in filtered_transactions)):
            return False
        # Has to have a positive share balance after 30 days
        transaction_idx = filtered_transactions.index(transaction)
        balance = transaction._share_balance
        for window_transaction in filtered_transactions[transaction_idx+1:]:
            if window_transaction.action == 'SELL':
                balance -= window_transaction.qty
            else:
                balance += window_transaction.qty
        return balance > 0

    def _add_transaction(self, transaction):
        """Adds a transaction and updates the calculated values."""
        if self._share_balance == 0:
            # to prevent divide by 0 error
            old_acb_per_share = 0
        else:
            old_acb_per_share = self._total_acb / self._share_balance

        proceeds = (transaction.qty * transaction.price) * transaction.exchange_rate  # noqa: E501

        if (transaction._description == "Stocks"):
            if transaction.action == "SELL":
                self._share_balance -= transaction.qty
                acb = old_acb_per_share * transaction.qty
                capital_gain = proceeds - transaction.expenses - acb
                self._total_acb -= acb
            elif transaction.action == "BUY":
                self._share_balance += transaction.qty
                acb = proceeds + transaction.expenses
                capital_gain = Decimal(0.0)
                self._total_acb += acb
        elif (transaction._description == "Equity and Index Options"):
            # only output option trades relevant to the current tax year
            if (transaction.date.year != datetime.now().year - 1):
                return False

            # describes how to align the individual table columns
            colalign = (
                "left",   # Date
                "left",   # Option name
                "left",   # Operation
                "right",  # Quantity
                "right",  # Price (CAD)
                "right",  # Fee
                "right",  # Number
            )

            # example 2:
            # buy to open - plus fees
            # sell to close - minus fees

            # example 6:
            # sell to open - minus fees
            # buy to close - plus fees
            option_name = transaction.ticker[-1]

            if (option_name == "P"):
                option_name = "PUT"
            elif (option_name == "C"):
                option_name = "CALL"

            if (transaction.action == "BUY"):
                proceeds_or_acb = "{:,.2f}".format(
                    proceeds + transaction.expenses)
            elif (transaction.action == "SELL"):
                proceeds_or_acb = "N/A"

            headers = ["date", "option name", "operation",
                       "qty", "price (CAD)", "fee", "acb"]

            rows = [[
                transaction.date,
                transaction.ticker,
                f"{transaction.action} {option_name}",
                "{0:f}".format(transaction.qty.normalize()),
                "{:,.2f}".format(proceeds),
                "{:,.2f}".format(transaction.expenses),
                proceeds_or_acb,
            ]]
            output = tabulate.tabulate(rows, headers=headers, tablefmt="psql",
                                       colalign=colalign, disable_numparse=True)
            click.echo("{}\n".format(output))
            return False

        if self._share_balance < 0:
            click.echo(
                f"Transaction caused negative share balance. Please make sure you own \"{transaction.ticker}\"! Add all transactions from all years into the .csv.")
            return False

        transaction.share_balance = self._share_balance
        transaction.proceeds = proceeds
        transaction.capital_gain = capital_gain
        transaction.acb = acb
        return True
