
import sys, os
from contextlib import contextmanager
from timeit import default_timer
from itertools import count
from turtle import pos
import pandas as pd
import requests
from re import match

# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from .constants import base_url, states, brewery_types, dtypes


def _validate_state(state):
    if state is None:
        return
    elif state.lower() not in states:
        raise ValueError(f'Invalid state entered, \'{state}\'')


def _validate_brewery_type(brewery_type):
    if brewery_type is None:
        return
    elif brewery_type not in brewery_types:
        raise ValueError(f'Invalid brewery_type entered. Must be in '
                         '{brewery_types}, but got \'{brewery_type}\'.')


def _validate_postal_code(postal_code):
    if postal_code is None:
        return
    elif not match('(^\\d{5}$)|(^\\d{5}-\\d{4}$)', postal_code):
        raise ValueError(f'Invalid postal_code entered, {postal_code}')


def _format_request_params(state=None, city=None, brewery_type=None, postal_code=None, page=None,
                           per_page=50):
    _validate_state(state)
    _validate_brewery_type(brewery_type)
    _validate_postal_code(postal_code)

    params = {'by_state': state,
              'by_city': city,
              'by_type': brewery_type,
              'by_postal': postal_code
              }
    if page is not None:
        params['page'] = str(page)
        params['per_page'] = str(per_page)

    return params


def _get_request(params=None):
    response = requests.get(base_url, params=params)
    return response


def _get_data(params=None):
    r = _get_request(params=params)
    json = r.json()
    if json:
        return pd.DataFrame(json).astype(dtypes)
    else:
        return pd.DataFrame()


@contextmanager
def timer(verbose=False):
    start_time = default_timer()
    yield
    elapsed = default_timer() - start_time
    if verbose:
        sys.stdout.write(f'\nTime elapsed: {elapsed:0.2f} sec')
        sys.stdout.flush()


def load(state=None, city=None, brewery_type=None, postal_code=None, verbose=False):
    """ Query the Open Brewery DB

    Parameters
    ----------
    state : str, optional
        State name (case-insensitive) to select (default is ``None``, all
        states will be included). Note that `'district of columbia'` is a
        valid ``state``.
    city : str, optional
        City name (case-insensitive) to select (default is ``None``, all
        cities will be included).
    brewery_type : {None, 'micro', 'regional', 'brewpub', 'large', 'planning', 'bar', 'contract', 'proprietor'}
        Brewery type to select (default is ``None``, all brewery types will be
        included).
    postal_code : str, optional
        Postal code to select (default is ``None``, all postal codes will be included).
    verbose : bool, optional
        Option for verbose output (default is ``False``).

        .. versionadded:: 0.1.1

    Returns
    -------
    data : pandas.DataFrame
        DataFrame with query results

    Examples
    --------
    Get information about all micro breweries in Wisconsin

    >>> import openbrewerydb
    >>> data = openbrewerydb.load(state='wisconsin',
    ...                           brewery_type='micro')
    """
    data = []
    num_breweries = 0
    with timer(verbose=verbose):
        for page in count(start=1):
            params = _format_request_params(state=state,
                                            city=city,
                                            brewery_type=brewery_type,
                                            page=page,
                                            postal_code=postal_code,
                                            per_page=50)
            df = _get_data(params=params)

            if df.empty:
                break

            num_breweries += df.shape[0]
            if verbose:
                msg = f'\rLoaded data for {num_breweries} breweries'
                sys.stdout.write(msg)
                sys.stdout.flush()

            data.append(df)

    if not data:
        raise ValueError('No data found for this query')

    df = pd.concat(data, ignore_index=True)

    return df
