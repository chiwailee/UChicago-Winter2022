#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------
# ----Project Lab: Manteio Capital----
# Authors: Tobias Rodriguez del Pozo
#          Sean Lin
# Date: 2022-03-16
# ------------------------------------

from typing import Union, Tuple, Iterable
import pandas as pd
import matplotlib.pyplot as plt

# Import utils for date slicing.
from auction_trading.utils import calc_n_prior, calc_n_prior_generator


def calc_single_trade(
    before: Union[pd.DataFrame, pd.Series],
    after: Union[pd.DataFrame, pd.Series],
    multiplier: int = 10_000,
) -> Tuple[float, float]:
    """
    Calculate the PnL for the spread.
    :param before: Data n days before the auction.
    :param after: Data n days after the auction.
    :param multiplier: Multiplier to use for PnL calculation.
    :return: Tuple containing PnL for the spread.
    """

    # Calculate PnL using multiplier of 10_000 for each 1bp change in spread.
    # Use the first value of days_before and last value of days_below to calculate the slope.
    # NOTE: Not sure if this is the correct calculation.
    before_pnl = (before.iloc[0] - before.iloc[-1]) * multiplier

    # Now, bet on flattening of the curve for days after.
    after_pnl = (after.iloc[-1] - after.iloc[0]) * multiplier

    try:
        return before_pnl[0], after_pnl[0]
    except:
        return before_pnl, after_pnl


def calc_slope_curve(
    spread: Union[pd.DataFrame, pd.Series],
    auction_date: pd.Timestamp,
    n: int,
    multiplier: int = 10_000,
) -> Tuple[float, float]:
    """
    Calculate PnL from buying (?) the spread n days before the auction. Then, assume position is closed
    1 minute before the auction, simultaneously hort the spread (bet on flattening). Close the
    position n days after the auction.
    :param spread: Spread to trade.
    :param auction_date: Date of auction.
    :param n: Days before to enter/close position.
    :param multiplier: Multiplier to use for PnL calculation.
    :return: Tuple containing PnL from buying the spread n days before the auction and PnL from
             shorting the spread for n days after the auction.
    """

    days_before, days_after = calc_n_prior(spread, auction_date, n)
    return calc_single_trade(days_before, days_after, multiplier)


def calc_all_trades(
    spread: Union[pd.DataFrame, pd.Series],
    auction_dates: Iterable[pd.Timestamp],
    n: int,
    multiplier: int = 10_000,
) -> pd.DataFrame:
    """
    Calculate the PnL for each auction date.
    :param spread: Spread to trade.
    :param auction_dates: DataFrame containing auction dates.
    :param n: Days before to enter/close position.
    :param multiplier:  Multiplier to use for PnL calculation.
    :return: DataFrame containing PnL for each auction date.
    """

    # PnL lists.
    prior = []
    after = []
    enter_at_pre = []
    enter_at_post = []
    exit_at_pre = []
    exit_at_post = []

    # Iterate through each auction date
    for p, a in calc_n_prior_generator(spread, auction_dates, n):
        # Calculate PnL
        prior_pnl, after_pnl = calc_single_trade(p, a, multiplier)

        # Append PnL to list
        prior.append(prior_pnl)
        after.append(after_pnl)

        # Append enter and exit times to list
        enter_at_pre.append(p.index[0])
        enter_at_post.append(a.index[0])

        exit_at_pre.append(p.index[-1])
        exit_at_post.append(a.index[-1])

    # Return DataFrame indexed by auction dates.
    # Note: given the index, be careful when using these results as it may introduce
    # lookahead bias, since we are returning ex-post PnL for each auction date.
    return pd.DataFrame(
        {
            "Enter at Pre-Auction Time": enter_at_pre,
            "Exit at Pre-Auction Time": exit_at_pre,
            "Pre-Auction PnL": prior,
            "Enter at Post-Auction Time": enter_at_post,
            "Exit at Post-Auction Time": exit_at_post,
            "Post-Auction PnL": after,
        },
        index=auction_dates,
    )


def plot_single_trade(
    spread: Union[pd.DataFrame, pd.Series], auction_date: pd.Timestamp, n: int
) -> None:
    """
    Plot the spread for n days before and after the auction. Include a vertical line at the auction date.
    :param spread: Spread to trade.
    :param auction_date: Date of auction.
    :param n: Days before to enter/close position.
    :return: None
    """

    fig, ax = plt.subplots(figsize=(16, 9))

    # Calculate before/after dates.
    days_before, days_after = calc_n_prior(spread, auction_date, n)

    # Plot the spread.
    days_before.plot(ax=ax, label="Before Auction")
    days_after.plot(ax=ax, label="After Auction")

    # Add vertical line at auction date.
    # Make the auction date at 1pm
    auction_date = auction_date.replace(hour=13, minute=0, second=0, microsecond=0)
    ax.axvline(auction_date, color="red", linestyle="--", label="Auction Date")

    # Add legend.
    ax.legend()

    # Add title.
    ax.set_title(f"Spread for {n} Days Before and After Auction Date")

    # Add labels.
    ax.set_xlabel("Date")
    ax.set_ylabel("Spread (bp)")

    # Show plot.
    plt.show()
