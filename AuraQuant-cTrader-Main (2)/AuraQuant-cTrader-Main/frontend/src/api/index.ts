import { User, Strategy } from '@/types';
import apiClient from './client';

// #region AUTHENTICATION
// =====================================================================

export const loginUser = async (credentials: any) => {
  const response = await apiClient.post('/api/login/', credentials);
  return response.data;
};

export const registerUser = async (userInfo: any) => {
  const response = await apiClient.post('/api/register/', userInfo);
  return response.data;
};

export const fetchUserProfile = async (): Promise<User> => {
  const response = await apiClient.get('/api/user/');
  return response.data;
};

// #endregion

// #region ROBOT & DATA API FUNCTIONS
// =====================================================================

export const getStrategies = async (): Promise<AdaptedStrategy[]> => {
  const response = await apiClient.get('/api/strategies/');
  return adaptStrategies(response.data);
};

export const activateRobot = async (variables: { strategyId: number; mt5AccountId: number; lotSize: number }) => {
    const response = await apiClient.post('/api/instances/', {
      strategy: variables.strategyId,
      mt5_account: variables.mt5AccountId,
      lot_size: variables.lotSize,
    });
    return response.data;
};

export const deactivateRobot = async (instanceId: number) => {
    const response = await apiClient.delete(`/api/instances/${instanceId}/`);
    return response;
};

export const getAccountPulse = async (): Promise<any> => {
    const response = await apiClient.get('/api/account-pulse/');
    return response.data;
};

export const getActiveRobots = async (): Promise<AdaptedInstance[]> => {
    const response = await apiClient.get('/api/instances/');
    return adaptInstances(response.data);
};

export const getTradeHistory = async (accountId: string): Promise<AdaptedTrade[]> => {
    const response = await apiClient.get('/api/trade-history/', {
        params: { account_id: accountId }
    });
    return adaptTrades(response.data);
};

export const getAccounts = async (): Promise<any[]> => {
    const response = await apiClient.get('/api/accounts/');
    return response.data;
};

export const createAccount = async (accountData: any) => {
  const response = await apiClient.post('/api/accounts/', accountData);
  return response.data;
};

export const getStrategyDetails = async (id: string): Promise<AdaptedStrategy> => {
  const response = await apiClient.get(`/api/strategies/${id}/`);
  return adaptStrategies([response.data])[0];
};

export const getEquityHistory = async (): Promise<{date: string, equity: number}[]> => {
    const response = await apiClient.get('/api/equity-history/');
    return response.data;
};

// #endregion

// #region DATA ADAPTERS
// ========================================================================

export interface AdaptedTrade {
  id: string | number;
  symbol: string;
  type: 'buy' | 'sell';
  volume: number | null;
  openPrice: number | null;
  profit: number | null;
  openTime: string;
  strategyName: string;
}

export const adaptTrades = (backendTrades: any[]): AdaptedTrade[] => {
    if (!Array.isArray(backendTrades)) return [];
    return backendTrades.map(trade => ({
        id: trade.id,
        symbol: trade.symbol,
        type: trade.trade_type,
        volume: trade.volume !== null ? parseFloat(trade.volume) : null,
        openPrice: trade.price_entry !== null ? parseFloat(trade.price_entry) : null,
        profit: trade.profit_loss !== null ? parseFloat(trade.profit_loss) : null,
        openTime: trade.timestamp,
        strategyName: trade.strategy_name || 'N/A',
    }));
}

export interface AdaptedInstance {
    id: number;
    isActive: boolean;
    totalProfit: number;
    strategyName: string;
    strategyId: number;
    riskLevel: 'Baixo' | 'Médio' | 'Alto' | 'N/A';
    winRate: number;
}

export const adaptInstances = (backendInstances: any[]): AdaptedInstance[] => {
    if (!Array.isArray(backendInstances)) return [];
    return backendInstances.map(instance => {
        const drawdown = instance.strategy?.backtest_results?.['Drawdown Máximo [%]'];
        let riskLevel: 'Baixo' | 'Médio' | 'Alto' | 'N/A' = 'N/A';
        if (drawdown !== null && drawdown !== undefined) {
          if (drawdown < 10) riskLevel = 'Baixo';
          else if (drawdown <= 20) riskLevel = 'Médio';
          else riskLevel = 'Alto';
        }

        return {
            id: instance.id,
            isActive: instance.is_active,
            totalProfit: instance.total_profit,
            strategyName: instance.strategy?.name ?? 'N/A',
            strategyId: instance.strategy?.id,
            riskLevel: riskLevel,
            winRate: instance.strategy?.backtest_results?.['Taxa de Acerto (Win Rate) [%]'] ?? 0,
        }
    });
}

export interface AdaptedStrategy {
  id: number;
  name: string;
  description: string;
  isFree: boolean;
  performance: string | null;
  tradesPerMonth: number | null;
  category: string;
  riskLevel: 'Baixo' | 'Médio' | 'Alto' | 'N/A';
  original: any;
}

export const adaptStrategies = (backendStrategies: any[]): AdaptedStrategy[] => {
  if (!Array.isArray(backendStrategies)) {
    console.error("adaptStrategies expected an array, but received:", backendStrategies);
    return [];
  }

  return backendStrategies.map(strategy => {
    const backtest = strategy.backtest_results || {};

    const drawdown = backtest['Drawdown Máximo [%]'];
    let riskLevel: 'Baixo' | 'Médio' | 'Alto' | 'N/A' = 'N/A';
    if (drawdown !== null && drawdown !== undefined) {
      if (drawdown < 10) riskLevel = 'Baixo';
      else if (drawdown <= 20) riskLevel = 'Médio';
      else riskLevel = 'Alto';
    }

    const rawPerformance = backtest['Retorno Total [%]'] ?? null;
    let formattedPerformance: string | null = null;
    if (rawPerformance !== null) {
      formattedPerformance = `${rawPerformance > 0 ? '+' : ''}${rawPerformance.toFixed(2)}%`;
    }

    return {
      id: strategy.id,
      name: strategy.name,
      description: strategy.description,
      isFree: strategy.suggested_capital === 0,
      performance: formattedPerformance,
      tradesPerMonth: backtest['Média de Trades/Mês'] ?? null,
      category: strategy.strategy_type,
      riskLevel,
      original: strategy,
    };
  });
};
