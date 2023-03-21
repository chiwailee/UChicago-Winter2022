#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------
# ----Project Lab: Manteio Capital----
# Authors: Tobias Rodriguez del Pozo
#          Sean Lin
# Date: 2022-03-16
# ------------------------------------

from typing import Union, Tuple, Iterable, Sequence
import pandas as pd
from numpy import number

Number = Union[int, float, number]


def _calc_n_prior_symmetric(
    spread: Union[pd.DataFrame, pd.Series], auction_date: pd.Timestamp, n: Number
) -> Tuple[Union[pd.Series, pd.DataFrame], Union[pd.Series, pd.DataFrame]]:
    """
    Symmetrically calculate n days before/after the auction date.
    """
    # Subtract 5 days from the auction date
    n_days_prior = auction_date - pd.Timedelta(days=n)
    n_days_after = auction_date + pd.Timedelta(days=n)

    # Get the data from the n days prior to the auction date
    n_days_prior_data = spread.loc[n_days_prior:auction_date]

    # Get the data from the n days after the auction date
    n_days_after_data = spread.loc[auction_date:n_days_after]

    return n_days_prior_data, n_days_after_data


def calc_n_prior(
    spread: Union[pd.DataFrame, pd.Series],
    auction_date: pd.Timestamp,
    n: Number = None,
    n_prev: Number = None,
    n_post: Number = None,
    bond_series: Sequence[str] = None,
) -> Tuple[Union[pd.Series, pd.DataFrame], Union[pd.Series, pd.DataFrame]]:
    """
    Calculate the n days prior to the auction date. Ideally, split it at 1pm on the auction, since
    treasury auctions occur at 1pm. Supports asymmetric n days prior and n days after.

    :param spread: Spread we're interested in.
    :param auction_date: Auction date.
    :param n: If n is not None, then n_prev and n_post are ignored. Calculate
              n days prior and n days after the auction date.
    :param n_prev: If n is None, then n_prev and n_post cannot be None. Calculate
                   n_prev days prior to the auction date.
    :param n_post: Same as above but for after the auction date.
    :return: Split data into given days before/after the auction.
    """

    # Set the time of auction date to 12:59:59
    assert n is not None or (
        n_prev is not None and n_post is not None
    ), "n cannot be None if n_prev and n_post are None"

    if bond_series is not None:
        # Temporary fix for 2Y and 5Y auctions
        # This probably needs to be refactored.
        if len(bond_series) == 2:
            auction_date_morning = auction_date.replace(hour=11, minute=29, second=59)
            auction_date_afternoon = auction_date.replace(hour=12, minute=59, second=59)

            # Split n_days_prior_data to be n_days before the first auction
            if n is not None:
                n_days_prior, _ = _calc_n_prior_symmetric(spread, auction_date_morning, n)
                n_days_after, _ = _calc_n_prior_symmetric(spread, auction_date_afternoon, n)
                return n_days_prior, n_days_after
            else:
                n_days_prior, _ = _calc_n_prior_symmetric(
                    spread, auction_date_morning, n_prev
                )
                _, n_days_after = _calc_n_prior_symmetric(
                    spread, auction_date_afternoon, n_post
                )
                return n_days_prior, n_days_after
        else:
            auction_date_prior = auction_date.replace(hour=12, minute=59, second=59)
    else:
        auction_date_prior = auction_date.replace(hour=12, minute=59, second=59)

    if n is not None:
        return _calc_n_prior_symmetric(spread, auction_date_prior, n)

    assert n_prev is not None and n_post is not None, "n_prev and n_post cannot be None"

    n_days_prior_data, _ = _calc_n_prior_symmetric(spread, auction_date_prior, n_prev)
    _, n_days_after_data = _calc_n_prior_symmetric(spread, auction_date_prior, n_post)

    return n_days_prior_data, n_days_after_data


def calc_n_prior_generator(
    spread: Union[pd.DataFrame, pd.Series],
    auction_dates: Iterable[pd.Timestamp],
    n: Number = None,
    n_prev: Number = None,
    n_post: Number = None,
    bond_series: pd.Series = None,
) -> Iterable[Tuple[Union[pd.Series, pd.DataFrame], Union[pd.Series, pd.DataFrame]]]:
    """
    Generator to calculate the n days prior to the auction date. Ideally, split it at 1pm on the auction, since
    treasury auctions occur at 1pm. Functionality is the same as calc_n_prior, but since it's a generator it
    makes it easier to iterate through all auction dates.

    :param spread: Should be DataFrame containing asset or spread.
    :param auction_dates: DataFrame containing auction dates.
    :param n: Number of days to return prior to the auction.
    :param n_prev: Number of days to return prior to the auction.
    :param n_post: Number of days to return after the auction.
    :param bond_series: Series containing the bond series (auctions on that day).
    :return: Tuple containing the data n days before and n days after the auction.
    """

    if bond_series is not None:
        # Iterate through each auction date
        for idx, date in enumerate(auction_dates):
            # Calculate the n days prior to the auction date
            n_days_prior_data, n_days_after_data = calc_n_prior(
                spread, date, n, n_prev, n_post, bond_series.loc[date]
            )
            yield n_days_prior_data, n_days_after_data

    else:
        # Iterate through each auction date
        for date in auction_dates:
            # Calculate the n days prior to the auction date
            n_days_prior_data, n_days_after_data = calc_n_prior(
                spread, date, n, n_prev, n_post
            )
            yield n_days_prior_data, n_days_after_data
