# NSE Negative Correlation Pair Finder

Finds NSE stock pairs whose daily return correlation is closest to `-1`.

The script downloads adjusted daily prices from Yahoo Finance, converts them into log returns, calculates pairwise correlations, and saves the most negatively correlated pairs to a CSV file.

## Setup

```bash
pip install -r requirements.txt
```

## Run

```bash
python src/nse_pair_finder.py
```

## Output

The result is saved here:

```text
outputs/negative_correlation_pairs.csv
```

## Change settings

```bash
python src/nse_pair_finder.py --start 2022-01-01 --threshold -0.6 --top 25
```

## Use your own universe

Edit:

```text
data/tickers.csv
```

Keep one column named:

```text
symbol
```

Example:

```text
symbol
RELIANCE
TCS
INFY
HDFCBANK
```

## Useful options

```bash
python src/nse_pair_finder.py --method spearman
```

```bash
python src/nse_pair_finder.py --rolling-window 120
```

```bash
python src/nse_pair_finder.py --output outputs/my_pairs.csv
```

## Note

A very strong negative correlation between two Indian equities is rare. If a pair appears close to `-1`, inspect it manually before treating it as real. Bad ticks, illiquidity, stale prices, and corporate action adjustment issues can create fake signals.
