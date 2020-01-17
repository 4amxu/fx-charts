import math
import numpy as np
import statistics as stats


def renko(ds, **kwargs):
    """
    Creates Renko chart bars from a iterable data array.

    Input:
        ds: an array with the data used to build the Renko bricks
        kwargs: the possible args are the following:
            fixed: creates the renko chart with a fixed brick size
            percentage: creates the renko chart where a new brick represents 
                a increment or a decrement on the price
            atr: creates the renko chart using the average true range (ATR)
            condensed: a boolean value. if it is true, creates always a brick
                for each candlestick, otherwise only creates a brick if there
                is a change in price grather than the brick step

    Return: an array with renko levels. The levels can be negative or
        positive. A positive level indicates a green candle and the negative
        value indicates a red candle. The values are the bottom of the
        renko candles.
    """

    if not hasattr(ds, "__iter__"):
        raise Exception("Not iterable object")

    condensed = True
    if "condensed" in kwargs:
        condensed = kwargs["condensed"]

    if "fixed" in kwargs:
        return _renko_step(ds, kwargs["fixed"], condensed)
    elif "percentage" in kwargs:
        return _renko_percentage(ds, kwargs["percentage"], condensed)
    elif "atr" in kwargs:
        return _renko_atr(ds, kwargs["atr"], condensed)

    raise ValueError("Not recognized method")


def _renko_step(ds, step, condensed):
    last_price = ds[0]
    chart = [last_price]
    for price in ds:
        bricks = math.floor(abs(price-last_price)/step)
        if bricks == 0:
            if condensed:
                chart.append(chart[-1])
            continue

        sign = int(np.sign(price-last_price))
        chart += [sign*(last_price+(sign*step*x)) for x in range(1, bricks+1)]
        last_price = abs(chart[-1])
    return chart


def _renko_percentage(ds, percentage, condensed):
    last_price = ds[0]
    chart = [last_price]
    for price in ds:
        inc = (price-last_price)/last_price
        if abs(inc) < percentage:
            if condensed:
                chart.append(chart[-1])
            continue

        sign = int(np.sign(price-last_price))
        bricks = math.floor(inc/percentage)
        step = math.floor((percentage * (price-last_price)) / inc)
        chart += [sign*(last_price+(sign*step*x))
                  for x in range(1, abs(bricks)+1)]
        last_price = abs(chart[-1])
    return chart


def _renko_atr(ohlc, atr_n, condensed):
    # calculate the first ATR
    curr_atr = 0
    for i in range(1, atr_n + 1):
        prev_close = ohlc["close"][i-1]
        curr_high = ohlc["high"][i]
        curr_low = ohlc["low"][i]

        curr_atr = curr_atr + (max(curr_high, prev_close)
                               - min(curr_low, prev_close))

    curr_atr = curr_atr / atr_n

    last_price = ohlc["close"][atr_n+1]
    chart = [last_price]
    for i in range(atr_n + 2, len(ohlc)):
        price = ohlc["close"][i]
        bricks = math.floor(abs(price-last_price)/curr_atr)
        if bricks == 0:
            if condensed:
                chart.append(chart[-1])
            continue

        sign = int(np.sign(price-last_price))
        chart += [sign*(last_price+(sign*curr_atr*x))
                  for x in range(1, bricks+1)]
        last_price = abs(chart[-1])

        prev_close = ohlc["close"][i-1]
        curr_high = ohlc["high"][i]
        curr_low = ohlc["low"][i]
        new_atr = max(curr_high, prev_close) - min(curr_low, prev_close)
        curr_atr = (curr_atr*(atr_n-1) + new_atr) / atr_n

    return chart


def ha_candlesticks(ohlc):
    """
    Computes the Heikin-Ashi candlesticks from OHLC data set.

    Input:
        ohlc: a pandas dataframe or dict of arryas containing the values
            of open, high, low and close

    Return: a dict with the open, high, low and close arrays for
        Heikin-Ashi candlesticks
    """

    if "open" not in ohlc or not hasattr(ohlc["open"], "__iter__"):
        raise Exception("Expect 'open' array")
    elif "high" not in ohlc or not hasattr(ohlc["high"], "__iter__"):
        raise Exception("Expect 'high' array")
    elif "low" not in ohlc or not hasattr(ohlc["low"], "__iter__"):
        raise Exception("Expect 'low' array")
    elif "close" not in ohlc or not hasattr(ohlc["close"], "__iter__"):
        raise Exception("Expect 'close' array")

    o = ohlc["open"]
    h = ohlc["high"]
    l = ohlc["low"]
    c = ohlc["close"]

    ha_c = [stats.mean([o[0], h[0], l[0], c[0]])]
    ha_o = [stats.mean([o[0], c[0]])]
    ha_h = [np.nan]
    ha_l = [np.nan]
    for i in range(1, len(o)):
        ha_c.append(stats.mean([o[i], h[i], l[i], c[i]]))
        ha_o.append(stats.mean([ha_o[i-1], ha_c[i-1]]))
        ha_h.append(max([h[i], ha_o[i], ha_c[i]]))
        ha_l.append(min([l[i], ha_o[i], ha_c[i]]))

    return {
        "open": ha_o[1:],
        "high": ha_h[1:],
        "low": ha_l[1:],
        "close": ha_c[1:]
    }
