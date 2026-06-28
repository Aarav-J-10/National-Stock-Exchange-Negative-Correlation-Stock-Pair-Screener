import argparse
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf


def read_symbols(path):
    table = pd.read_csv(path)
    column = "symbol" if "symbol" in table.columns else table.columns[0]
    symbols = table[column].dropna().astype(str).str.strip().str.upper()
    symbols = symbols[symbols != ""]
    return sorted(set(symbols))


def nse_symbol(symbol):
    symbol = symbol.strip().upper()
    return symbol if symbol.endswith(".NS") else f"{symbol}.NS"


def download_prices(symbols, start, end):
    tickers = [nse_symbol(symbol) for symbol in symbols]
    raw = yf.download(tickers, start=start, end=end, auto_adjust=True, progress=False, threads=True)

    if raw.empty:
        raise RuntimeError("No price data was downloaded")

    if isinstance(raw.columns, pd.MultiIndex):
        prices = raw["Close"]
    else:
        prices = raw[["Close"]]
        prices.columns = tickers[:1]

    prices = prices.dropna(axis=1, how="all")
    prices = prices.loc[:, prices.nunique(dropna=True) > 1]
    return prices


def log_returns(prices):
    returns = np.log(prices).diff()
    returns = returns.replace([np.inf, -np.inf], np.nan)
    return returns


def latest_rolling_correlation(returns, first, second, window):
    values = returns[first].rolling(window).corr(returns[second]).dropna()
    if values.empty:
        return np.nan
    return values.iloc[-1]


def pair_table(returns, min_days, threshold, top, method, rolling_window):
    matrix = returns.corr(method=method, min_periods=min_days)
    rows = []

    for first, second in combinations(matrix.columns, 2):
        correlation = matrix.loc[first, second]

        if pd.isna(correlation):
            continue

        overlap = returns[[first, second]].dropna().shape[0]

        if overlap < min_days:
            continue

        rows.append(
            {
                "stock_a": first.replace(".NS", ""),
                "stock_b": second.replace(".NS", ""),
                "correlation": correlation,
                "distance_from_minus_one": abs(correlation + 1),
                "overlap_days": overlap,
                f"latest_{rolling_window}d_correlation": latest_rolling_correlation(
                    returns, first, second, rolling_window
                ),
            }
        )

    pairs = pd.DataFrame(rows)

    if pairs.empty:
        return pairs

    pairs = pairs.sort_values(["distance_from_minus_one", "correlation"], ascending=[True, True])
    filtered = pairs[pairs["correlation"] <= threshold]

    if filtered.empty:
        return pairs.head(top).reset_index(drop=True)

    return filtered.head(top).reset_index(drop=True)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tickers", default="data/tickers.csv")
    parser.add_argument("--start", default="2023-01-01")
    parser.add_argument("--end", default=None)
    parser.add_argument("--threshold", type=float, default=-0.70)
    parser.add_argument("--top", type=int, default=50)
    parser.add_argument("--min-days", type=int, default=250)
    parser.add_argument("--rolling-window", type=int, default=60)
    parser.add_argument("--method", choices=["pearson", "spearman", "kendall"], default="pearson")
    parser.add_argument("--output", default="outputs/negative_correlation_pairs.csv")
    return parser.parse_args()


def main():
    args = parse_args()
    tickers_path = Path(args.tickers)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    symbols = read_symbols(tickers_path)
    prices = download_prices(symbols, args.start, args.end)
    returns = log_returns(prices)
    result = pair_table(
        returns=returns,
        min_days=args.min_days,
        threshold=args.threshold,
        top=args.top,
        method=args.method,
        rolling_window=args.rolling_window,
    )

    result.to_csv(output_path, index=False)

    print(f"stocks scanned: {prices.shape[1]}")
    print(f"date range: {prices.index.min().date()} to {prices.index.max().date()}")
    print(f"saved: {output_path}")

    if result.empty:
        print("no valid pairs found")
    else:
        print(result.to_string(index=False))


if __name__ == "__main__":
    main()
