export interface User {
  id: string;
  email: string;
  name?: string;
}

export interface Robot {
    id: number;
    strategy: {
        name: string;
        risk_level: string;
        win_rate: number;
    };
    is_active: boolean;
    total_profit: string;
    mt5_account: {
        balance: string;
    };
}

export interface Trade {
    trade_type: string;
    symbol: string;
    volume: number;
    open_price: number;
    profit: number;
    open_time: string;
}

export interface Strategy {
    id: number;
    name: string;
    description: string;
    suggested_capital: number;
    strategy_type: string;
    backtest_results: {
        [key: string]: any;
    };
}
