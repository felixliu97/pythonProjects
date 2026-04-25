from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable, Iterable

import pandas as pd
import yfinance as yf


DEFAULT_TICKERS = ["A200.AX", "VHY.AX", "SYI.AX"]
DEFAULT_LOOKBACK_YEARS = 5
DEFAULT_RSI_PERIOD = 14
DEFAULT_RSI_THRESHOLDS = [30.0, 35.0, 40.0]
DEFAULT_BUY_AMOUNT = 1000.0
DEFAULT_BROKERAGES = [0.0, 3.0]
OUTPUT_CSV = Path(__file__).with_name("backtest_dividend_etf_results.csv")
FALLBACK_OUTPUT_CSV = Path(__file__).with_name("backtest_dividend_etf_results.latest.csv")


@dataclass
class StrategyConfig:
    strategy: str
    signal_rule: str
    buy_signal_fn: Callable[[pd.DataFrame], pd.Series]


@dataclass
class BacktestResult:
    strategy: str
    ticker: str
    start_date: str
    end_date: str
    signal_rule: str
    buy_amount: float
    brokerage_per_trade: float
    total_buys: int
    total_invested: float
    total_brokerage: float
    total_cash_outlay: float
    total_units: float
    ending_price: float
    ending_price_value: float
    total_dividends: float
    net_invested_capital: float
    price_only_profit: float
    net_profit: float
    price_return_pct: float
    net_return_pct: float
    price_only_annualized_return_pct: float
    max_drawdown_pct: float


def calculate_rsi(prices: pd.Series, period: int = DEFAULT_RSI_PERIOD) -> pd.Series:
    delta = prices.diff()
    gains = delta.clip(lower=0)
    losses = -delta.clip(upper=0)

    avg_gain = gains.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    avg_loss = losses.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    no_loss_mask = avg_loss == 0
    rsi = rsi.mask(no_loss_mask & (avg_gain > 0), 100.0)
    rsi = rsi.mask(no_loss_mask & (avg_gain == 0), 50.0)
    return rsi


def load_history(ticker: str, start: str) -> pd.DataFrame:
    history = yf.Ticker(ticker).history(start=start, auto_adjust=False, actions=True)
    if history.empty:
        raise ValueError(f"No price history returned for {ticker}")
    if isinstance(history.columns, pd.MultiIndex):
        history.columns = history.columns.get_level_values(0)
    if "Dividends" not in history.columns:
        history["Dividends"] = 0.0
    return history[["Close", "Dividends"]].dropna(subset=["Close"]).copy()


def add_monthly_buy_signal(data: pd.DataFrame) -> pd.Series:
    normalized_index = data.index.tz_localize(None) if getattr(data.index, "tz", None) is not None else data.index
    months = pd.Series(normalized_index.to_period("M"), index=data.index)
    return months.ne(months.shift(1))


def build_rsi_strategy(threshold: float) -> StrategyConfig:
    strategy_name = f"rsi_below_{int(threshold)}"
    signal_rule = f"RSI(14) < {threshold:.0f}"

    def signal_fn(frame: pd.DataFrame) -> pd.Series:
        return frame["RSI"] < threshold

    return StrategyConfig(strategy=strategy_name, signal_rule=signal_rule, buy_signal_fn=signal_fn)


def build_monthly_dca_strategy() -> StrategyConfig:
    def signal_fn(frame: pd.DataFrame) -> pd.Series:
        return frame["MonthlyBuySignal"]

    return StrategyConfig(
        strategy="monthly_dca",
        signal_rule="First trading day of each month",
        buy_signal_fn=signal_fn,
    )


def get_default_start_date() -> str:
    end = pd.Timestamp.today().normalize()
    start = end - pd.DateOffset(years=DEFAULT_LOOKBACK_YEARS)
    return start.strftime("%Y-%m-%d")


def run_backtest(
    ticker: str,
    strategy_config: StrategyConfig,
    start: str | None = None,
    rsi_period: int = DEFAULT_RSI_PERIOD,
    buy_amount: float = DEFAULT_BUY_AMOUNT,
    brokerage_per_trade: float = 0.0,
) -> tuple[BacktestResult, pd.DataFrame]:
    if start is None:
        start = get_default_start_date()
    data = load_history(ticker, start)
    data["RSI"] = calculate_rsi(data["Close"], period=rsi_period)
    data["MonthlyBuySignal"] = add_monthly_buy_signal(data)
    data["BuySignal"] = strategy_config.buy_signal_fn(data).fillna(False)

    units = 0.0
    invested = 0.0
    total_brokerage = 0.0
    total_dividends = 0.0
    equity_curve: list[float] = []
    cash_outlay_curve: list[float] = []
    buy_count = 0

    for row in data.itertuples():
        if row.BuySignal:
            bought_units = buy_amount / row.Close
            units += bought_units
            invested += buy_amount
            total_brokerage += brokerage_per_trade
            buy_count += 1

        dividend_cash = units * row.Dividends if row.Dividends else 0.0
        total_dividends += dividend_cash

        portfolio_value = units * row.Close
        equity_curve.append(portfolio_value)
        cash_outlay_curve.append(invested + total_brokerage)

    data["PortfolioValue"] = equity_curve
    data["InvestedCapital"] = data["BuySignal"].astype(float).cumsum() * buy_amount
    data["CashOutlay"] = cash_outlay_curve

    ending_price = float(data["Close"].iloc[-1])
    ending_price_value = float(units * ending_price)
    total_cash_outlay = invested + total_brokerage
    net_invested_capital = total_cash_outlay - total_dividends
    price_only_profit = ending_price_value - total_cash_outlay
    net_profit = ending_price_value - net_invested_capital
    price_return_pct = (price_only_profit / total_cash_outlay * 100) if total_cash_outlay else 0.0
    net_return_pct = (net_profit / net_invested_capital * 100) if net_invested_capital else 0.0

    start_ts = pd.Timestamp(data.index[0]).normalize()
    end_ts = pd.Timestamp(data.index[-1]).normalize()
    years = max((end_ts - start_ts).days / 365.25, 1 / 365.25)
    price_only_annualized_return_pct = ((ending_price_value / total_cash_outlay) ** (1 / years) - 1) * 100 if total_cash_outlay else 0.0

    rolling_peak = data["PortfolioValue"].cummax()
    drawdown = (data["PortfolioValue"] - rolling_peak) / rolling_peak
    max_drawdown_pct = float(drawdown.min() * 100) if not drawdown.dropna().empty else 0.0

    result = BacktestResult(
        strategy=strategy_config.strategy,
        ticker=ticker,
        start_date=str(start_ts.date()),
        end_date=str(end_ts.date()),
        signal_rule=strategy_config.signal_rule,
        buy_amount=buy_amount,
        brokerage_per_trade=round(brokerage_per_trade, 2),
        total_buys=buy_count,
        total_invested=round(invested, 2),
        total_brokerage=round(total_brokerage, 2),
        total_cash_outlay=round(total_cash_outlay, 2),
        total_units=round(units, 6),
        ending_price=round(ending_price, 4),
        ending_price_value=round(ending_price_value, 2),
        total_dividends=round(total_dividends, 2),
        net_invested_capital=round(net_invested_capital, 2),
        price_only_profit=round(price_only_profit, 2),
        net_profit=round(net_profit, 2),
        price_return_pct=round(price_return_pct, 2),
        net_return_pct=round(net_return_pct, 2),
        price_only_annualized_return_pct=round(price_only_annualized_return_pct, 2),
        max_drawdown_pct=round(max_drawdown_pct, 2),
    )
    return result, data


def format_currency(value: float) -> str:
    return f"${value:,.2f}"


def results_to_frame(results: Iterable[BacktestResult]) -> pd.DataFrame:
    frame = pd.DataFrame(asdict(item) for item in results)
    return frame.sort_values(by=["strategy", "ticker", "brokerage_per_trade"]).reset_index(drop=True)


def save_results_csv(frame: pd.DataFrame) -> Path:
    try:
        frame.to_csv(OUTPUT_CSV, index=False)
        return OUTPUT_CSV
    except PermissionError:
        frame.to_csv(FALLBACK_OUTPUT_CSV, index=False)
        return FALLBACK_OUTPUT_CSV


def print_results(results: Iterable[BacktestResult]) -> None:
    rows = []
    for item in results:
        rows.append(
            {
                "Strategy": item.strategy,
                "Ticker": item.ticker,
                "Brokerage": format_currency(item.brokerage_per_trade),
                "Start": item.start_date,
                "End": item.end_date,
                "Rule": item.signal_rule,
                "BuyAmount": format_currency(item.buy_amount),
                "Buys": item.total_buys,
                "Invested": format_currency(item.total_invested),
                "Fees": format_currency(item.total_brokerage),
                "CashOutlay": format_currency(item.total_cash_outlay),
                "NetInvested": format_currency(item.net_invested_capital),
                "EndPriceValue": format_currency(item.ending_price_value),
                "Dividends": format_currency(item.total_dividends),
                "PriceProfit": format_currency(item.price_only_profit),
                "NetProfit": format_currency(item.net_profit),
                "PriceReturn%": f"{item.price_return_pct:.2f}%",
                "NetReturn%": f"{item.net_return_pct:.2f}%",
                "PriceCAGR%": f"{item.price_only_annualized_return_pct:.2f}%",
                "MaxDD%": f"{item.max_drawdown_pct:.2f}%",
            }
        )

    frame = pd.DataFrame(rows)
    print(frame.to_string(index=False))


def main() -> None:
    strategies = [build_monthly_dca_strategy()]
    strategies.extend(build_rsi_strategy(threshold) for threshold in DEFAULT_RSI_THRESHOLDS)

    all_results = []
    for strategy_config in strategies:
        for brokerage in DEFAULT_BROKERAGES:
            for ticker in DEFAULT_TICKERS:
                result, _ = run_backtest(
                    ticker=ticker,
                    strategy_config=strategy_config,
                    brokerage_per_trade=brokerage,
                )
                all_results.append(result)

    results_frame = results_to_frame(all_results)
    save_results_csv(results_frame)


if __name__ == "__main__":
    main()
