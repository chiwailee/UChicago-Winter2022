#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------
# ----Project Lab: Manteio Capital----
# Authors: Tobias Rodriguez del Pozo
#          Sean Lin
# Date: 2022-03-16
# ------------------------------------

import pandas as pd
import matplotlib.pyplot as plt
import scipy
from typing import Union, Tuple, Sequence, Iterable, List, Callable
from functools import partial

# Import utils for date slicing.
from auction_trading.utils import calc_n_prior, calc_n_prior_generator, Number


def calc_steepener(
    spread: Union[pd.DataFrame, pd.Series], multiplier: int = 10_000
) -> Number:
    """
    Calculate the steepener for the given spread.
    :param spread: Spread to calculate steepener for.
    :return: Steepener PnL.
    """

    pnl = (spread.iloc[-1] - spread.iloc[0]) * multiplier
    try:
        return pnl[0]
    except:
        return pnl


def calc_flattener(
    spread: Union[pd.DataFrame, pd.Series], multiplier: int = 10_000,
) -> Number:
    """
    Calculate the flattener for the given spread.
    :param spread: Spread to calculate flattener for.
    :return: Flattener PnL.
    """
    pnl = (spread.iloc[0] - spread.iloc[-1]) * multiplier
    try:
        return pnl[0]
    except:
        return pnl


def calc_single_trade(
    before: Union[pd.DataFrame, pd.Series],
    after: Union[pd.DataFrame, pd.Series],
    multiplier: int = 10_000,
    trades: Union[List[str], Tuple[str]] = ("steepener", "flattener"),
) -> Tuple[float, float]:
    """
    Calculate the PnL for the spread.
    :param before: Data n days before the auction.
    :param after: Data n days after the auction.
    :param multiplier: Multiplier to use for PnL calculation.
    :return: Tuple containing PnL for the spread.
    :param trades: Order of trades to make. Default is ("steepener", "flattener").
                   But can also be ("flattener", "steepener"), ("steepener", "steepener"), etc.
    """

    # Calculate PnL using multiplier of 10_000 for each 1bp change in spread.
    # Use the first value of days_before and last value of days_below to calculate the slope.
    # NOTE: Not sure if this is the correct calculation.
    assert trades[0] in ("steepener", "flattener") and trades[1] in (
        "steepener",
        "flattener",
    ), "Trades must be either 'steepener' or 'flattener'."

    # Calculate PnL for pre-auction.
    if trades[0] == "steepener":
        before_pnl = calc_steepener(before, multiplier)
    else:
        before_pnl = calc_flattener(before, multiplier)

    # Calculate PnL for post-auction.
    if trades[1] == "steepener":
        after_pnl = calc_steepener(after, multiplier)
    else:
        after_pnl = calc_flattener(after, multiplier)
    try:
        return before_pnl[0], after_pnl[0]
    except:
        return before_pnl, after_pnl


def calc_slope_curve(
    spread: Union[pd.DataFrame, pd.Series],
    auction_date: pd.Timestamp,
    n: Number = None,
    n_prev: Number = None,
    n_post: Number = None,
    multiplier: int = 10_000,
    trades: Union[List[str], Tuple[str]] = ("steepener", "flattener"),
) -> Tuple[float, float]:
    """
    Calculate PnL from buying (?) the spread n days before the auction. Then, assume position is closed
    1 minute before the auction, simultaneously short the spread (bet on flattening). Close the
    position n days after the auction.
    :param spread: Spread to trade.
    :param auction_date: Date of auction.
    :param n: Days before to enter/close position.
    :param multiplier: Multiplier to use for PnL calculation.
    :param trades: Order of trades to make. Default is ("steepener", "flattener").
    :return: Tuple containing PnL from buying the spread n days before the auction and PnL from
             shorting the spread for n days after the auction.
    """

    days_before, days_after = calc_n_prior(spread, auction_date, n, n_prev, n_post)
    return calc_single_trade(days_before, days_after, multiplier, trades)


def calc_all_trades(
    spread: Union[pd.DataFrame, pd.Series],
    auction_dates: Union[Iterable[pd.Timestamp], pd.DatetimeIndex, pd.DataFrame],
    n: Union[Tuple[Number, Number], Number],
    multiplier: int = 10_000,
    trade_rule: Callable = lambda x: ("steepener", "flattener"),
) -> pd.DataFrame:
    """
    Calculate the PnL for each auction date.
    :param spread: Spread to trade.
    :param auction_dates: DataFrame containing auction dates.
    :param n: Days before to enter/close position.
    :param multiplier:  Multiplier to use for PnL calculation.
    :return: DataFrame containing PnL for each auction date.
    """

    if isinstance(n, tuple):
        n_prev, n_post = n
        n = None
    else:
        n_prev, n_post = None, None

    if isinstance(auction_dates, pd.DataFrame):
        auction_features = auction_dates.copy()['bond_series']
        auction_dates = list(auction_features.index)

    else:
        auction_features = None

    # PnL lists.
    prior = []
    after = []
    enter_at_pre = []
    enter_at_post = []
    exit_at_pre = []
    exit_at_post = []

    # Iterate through each auction date
    for idx, (p, a) in enumerate(calc_n_prior_generator(spread, auction_dates, n, n_prev, n_post, auction_features)):
        # Calculate PnL
        if auction_features is not None:
            trades = trade_rule(auction_features.iloc[idx])
        else:
            trades = ('steepener', 'flattener')

        prior_pnl, after_pnl = calc_single_trade(p, a, multiplier, trades)

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


def optimize_entry_time(
    spread: Union[pd.DataFrame, pd.Series],
    auction_dates: Union[Iterable[pd.Timestamp], pd.DatetimeIndex, pd.DataFrame],
    symmetric: bool = True,
    multiplier: int = 10_000,
    trade_rule: Callable = lambda x: ("steepener", "flattener"),
) -> Union[Number, Tuple[Number, Number]]:
    """
    Calculate optimal entry and exit time for the spread in the pre- / post-auction period.
    :param spread: Spread to trade.
    :param auction_dates: DataFrame containing auction dates.
    :param symmetric: If True, use the same number of days before and after the auction.
    :param multiplier:  Multiplier to use for PnL calculation.
    :return: n that maximizes PnL.
    """

    if symmetric:
        # Calculate PnL for both pre- and post-auction periods.
        def _calc_pnl(spread, auction_dates, n=None, multiplier=None, trade_rule=trade_rule):
            df = calc_all_trades(spread, auction_dates, n, multiplier, trade_rule)
            return df["Pre-Auction PnL"].sum() + df["Post-Auction PnL"].sum()

        # Partially evaluate _calc_pnl to use in scipy.optimize.minimize_scalar
        _calc_pnl_partial = partial(
            _calc_pnl,
            spread,
            auction_dates,
            multiplier=multiplier,
            trade_rule=trade_rule,
        )
        # Optimize for PnL.
        res = scipy.optimize.minimize_scalar(
            lambda n: -_calc_pnl_partial(n),
            bounds=(1, 5),
            method="bounded",
        ).x
        # Print results.
        print(
            f"Optimal entry/exit time: {res:,.2f} days before/after the auction. Pnl: ${_calc_pnl_partial(res):,.2f}"
        )
        return res
    else:
        # Calculate PnL for either pre- or post-auction period.
        # NOTE: there is redundant computation here, so this could be refactored.
        def _calc_pnl(
            spread, auction_dates, n=None, multiplier=None, trade_rule=trade_rule, col="Pre-Auction PnL"
        ):
            df = calc_all_trades(spread, auction_dates, n, multiplier, trade_rule)
            return df[col].sum()

        # Partially evaluate _calc_pnl to use in scipy.optimize.minimize_scalar
        _calc_pnl_partial = partial(
            _calc_pnl, spread, auction_dates, multiplier=multiplier, trade_rule=trade_rule
        )
        # Optimal pre-auction entry time.
        res_pre = scipy.optimize.minimize_scalar(
            lambda n: -_calc_pnl_partial(n, col="Pre-Auction PnL"),
            bounds=(1, 5),
            method="bounded",
        ).x

        # Optimal post-auction exit time.
        res_post = scipy.optimize.minimize_scalar(
            lambda n: -_calc_pnl_partial(n, col="Post-Auction PnL"),
            bounds=(1, 5),
            method="bounded",
        ).x

        # Print results.
        print(
            f"Optimal entry/exit time: {res_pre:,.2f} days before the "
            f"auction and {res_post:,.2f} days after the auction.\n"
            f"Pnl before auction: ${_calc_pnl_partial(res_pre, col='Pre-Auction PnL'):,.2f}.\n"
            f"Pnl after auction: ${_calc_pnl_partial(res_post, col='Post-Auction PnL'):,.2f}.\n"
            f"Pnl total: ${_calc_pnl_partial(res_pre, col='Pre-Auction PnL') + _calc_pnl_partial(res_post, col='Post-Auction PnL'):,.2f}."
        )
        return res_pre, res_post


def plot_single_trade(
    spread: Union[pd.DataFrame, pd.Series], auction_date: pd.Timestamp, n: Number
) -> None:
    """
    Plot the spread for n days before and after the auction. Include a vertical line at the auction date.
    :param spread: Spread to trade.
    :param auction_date: Date of auction.
    :param n: Days before to enter/close position.
    :return: None
    """

    fig, ax = plt.subplots(figsize=(16, 9))

    # Plot the spread.
    days_before, days_after = calc_n_prior(spread, auction_date, n)

    # Concat the two series.
    days_before = pd.concat([days_before, days_after])

    # Plot the series.
    days_before.plot(ax=ax, label="Spread")

    # Add vertical line at auction date.
    # Make the auction date at 1pm
    auction_date = auction_date.replace(hour=13, minute=0, second=0, microsecond=0)
    ax.axvline(auction_date, color="red", linestyle="--", label="Auction Date")

    # Calculate PnL.
    before_pnl, after_pnl = calc_slope_curve(spread, auction_date, n)

    # Add one label for the PnL before auction
    ax.text(
        0.2,
        0.99,
        f"PnL Before: ${before_pnl:,.2f}\nPnL After: ${after_pnl:,.2f}",
        ha="left",
        va="top",
        transform=ax.transAxes,
    )

    ax.legend()

    ax.set_title(f"Spread for {n} Days Before and After Auction Date")

    ax.set_xlabel("Date")
    ax.set_ylabel("Spread (bp)")

    plt.show()
