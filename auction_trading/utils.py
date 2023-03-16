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


def calc_n_prior(
    spread: Union[pd.DataFrame, pd.Series], auction_date: pd.Timestamp, n: int
) -> Tuple[Union[pd.Series, pd.DataFrame], Union[pd.Series, pd.DataFrame]]:
    """
    Calculate the n days prior to the auction date. Ideally, split it at 1pm on the auction, since
    treasury auctions occur at 1pm.

    :param spread: Should be DataFrame containing asset or spread.
    :param auction_date: Date of the auction.
    :param n: Number of days to return prior to the auction.
    :return: Tuple containing the data n days before and n days after the auction.
    """

    # Set the time of auction date to 12:59:59
    auction_date_prior = auction_date.replace(hour=12, minute=59, second=59)

    # Subtract 5 days from the auction date
    n_days_prior = auction_date - pd.Timedelta(days=n)
    n_days_after = auction_date + pd.Timedelta(days=n)

    # Get the data from the n days prior to the auction date
    n_days_prior_data = spread.loc[n_days_prior:auction_date_prior]

    # Get the data from the n days after the auction date
    n_days_after_data = spread.loc[auction_date_prior:n_days_after]

    return n_days_prior_data, n_days_after_data


def calc_n_prior_generator(
    spread: Union[pd.DataFrame, pd.Series],
    auction_dates: Iterable[pd.Timestamp],
    n: int,
) -> Iterable[Tuple[Union[pd.Series, pd.DataFrame], Union[pd.Series, pd.DataFrame]]]:
    """
    Generator to calculate the n days prior to the auction date. Ideally, split it at 1pm on the auction, since
    treasury auctions occur at 1pm. Functionality is the same as calc_n_prior, but since it's a generator it
    makes it easier to iterate through all auction dates.

    :param spread: Should be DataFrame containing asset or spread.
    :param auction_dates: DataFrame containing auction dates.
    :param n: Number of days to return prior to the auction.
    :return: Tuple containing the data n days before and n days after the auction.
    """

    # Iterate through each auction date
    for date in auction_dates:
        # Calculate the n days prior to the auction date
        n_days_prior_data, n_days_after_data = calc_n_prior(spread, date, n)
        yield n_days_prior_data, n_days_after_data
