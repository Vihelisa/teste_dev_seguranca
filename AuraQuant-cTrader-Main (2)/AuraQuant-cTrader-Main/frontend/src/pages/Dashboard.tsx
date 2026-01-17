import { PageLayout } from "@/components/PageLayout";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Switch } from "@/components/ui/switch";
import { OnboardingTour } from "@/components/OnboardingTour";
import { useState, useEffect, useMemo } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  getAccountPulse,
  getActiveRobots,
  getTradeHistory,
  getAccounts,
  deactivateRobot,
  activateRobot,
  getEquityHistory,
  AdaptedStrategy, // Assuming this can be used for activation target
  AdaptedInstance
} from "@/api";
import { Skeleton } from "@/components/ui/skeleton";
import { useToast } from "@/hooks/use-toast";
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Terminal } from "lucide-react";


// Re-using the Activation Dialog logic from Marketplace
const ActivationDialog = ({
  robot,
  isOpen,
  onClose,
  onConfirm,
  isActivating,
}: {
  robot: AdaptedInstance; // Changed to AdaptedInstance
  isOpen: boolean;
  onClose: () => void;
  onConfirm: (data: { mt5AccountId: number; lotSize: number }) => void;
  isActivating: boolean;
}) => {
  const { data: accounts, isLoading: isLoadingAccounts, isError: isAccountsError } = useQuery({
    queryKey: ['accounts'],
    queryFn: getAccounts,
    enabled: isOpen,
  });

  const [selectedAccount, setSelectedAccount] = useState<string>("");
  const [lotSize, setLotSize] = useState<string>("0.01");

  const handleConfirm = () => {
    if (selectedAccount && lotSize) {
      onConfirm({
        mt5AccountId: parseInt(selectedAccount, 10),
        lotSize: parseFloat(lotSize),
      });
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Reativar Robô: {robot.strategyName}</DialogTitle>
          <DialogDescription>
            Selecione a conta e configure os parâmetros para reativar este robô.
          </DialogDescription>
        </DialogHeader>
        <div className="grid gap-4 py-4">
          {isAccountsError ? (
            <Alert variant="destructive">
              <Terminal className="h-4 w-4" />
              <AlertTitle>Erro!</AlertTitle>
              <AlertDescription>
                Não foi possível carregar suas contas MT5. Tente novamente mais tarde.
              </AlertDescription>
            </Alert>
          ) : !isLoadingAccounts && accounts?.length === 0 ? (
             <Alert>
              <Terminal className="h-4 w-4" />
              <AlertTitle>Nenhuma Conta Encontrada</AlertTitle>
              <AlertDescription>
                Você precisa cadastrar uma conta MT5 na página "Minhas Contas" antes de ativar um robô.
              </AlertDescription>
            </Alert>
          ) : (
            <>
              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor="account" className="text-right">
                  Conta MT5
                </Label>
                <Select onValueChange={setSelectedAccount} value={selectedAccount} disabled={isLoadingAccounts}>
                  <SelectTrigger className="col-span-3">
                    <SelectValue placeholder={isLoadingAccounts ? "Carregando..." : "Selecione uma conta"} />
                  </SelectTrigger>
                  <SelectContent>
                    {accounts?.map(acc => (
                      <SelectItem key={acc.id} value={String(acc.id)}>
                        {acc.nickname} ({acc.account_login})
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor="lotSize" className="text-right">
                  Tamanho do Lote
                </Label>
                <Input
                  id="lotSize"
                  type="number"
                  value={lotSize}
                  onChange={(e) => setLotSize(e.target.value)}
                  className="col-span-3"
                />
              </div>
            </>
          )}
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={onClose}>Cancelar</Button>
          <Button onClick={handleConfirm} disabled={isActivating || !selectedAccount || !lotSize || isAccountsError || accounts?.length === 0}>
            {isActivating ? "Ativando..." : "Confirmar Ativação"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};


const Dashboard = () => {
  const [showTour, setShowTour] = useState(false);
  const { toast } = useToast();
  const queryClient = useQueryClient();

  // Data Fetching
  const { data: pulseData, isLoading: isLoadingPulse } = useQuery({
    queryKey: ['accountPulse'],
    queryFn: getAccountPulse,
  });

  const { data: activeRobots, isLoading: isLoadingRobots } = useQuery({
    queryKey: ['activeRobots'],
    queryFn: getActiveRobots,
  });

  const { data: accounts, isLoading: isLoadingAccounts } = useQuery({
    queryKey: ['accounts'],
    queryFn: getAccounts,
  });

  const primaryAccountId = accounts?.[0]?.id;

  const { data: tradeHistory, isLoading: isLoadingHistory } = useQuery({
    queryKey: ['tradeHistory', primaryAccountId],
    queryFn: () => getTradeHistory(primaryAccountId!),
    enabled: !!primaryAccountId,
  });

  const { data: equityHistory, isLoading: isLoadingEquityHistory } = useQuery({
      queryKey: ['equityHistory', primaryAccountId],
      queryFn: getEquityHistory,
      enabled: !!primaryAccountId,
  });

  // Derived state for the chart
  const weeklyGrowth = useMemo(() => {
    if (!equityHistory || equityHistory.length < 2) return 0;
    const firstDay = equityHistory[0].equity;
    const lastDay = equityHistory[equityHistory.length - 1].equity;
    if (firstDay === 0) return 0;
    return ((lastDay - firstDay) / firstDay) * 100;
  }, [equityHistory]);


  // Mutations
  const deactivateMutation = useMutation({
    mutationFn: deactivateRobot,
    onSuccess: () => {
      toast({ title: "Sucesso", description: "Robô desativado.", variant: "success" });
      queryClient.invalidateQueries({ queryKey: ['activeRobots'] });
      queryClient.invalidateQueries({ queryKey: ['accountPulse'] });
    },
    onError: (error: any) => {
      toast({ title: "Erro", description: error.message || "Não foi possível desativar o robô.", variant: "destructive" });
    },
  });

  const [activationTarget, setActivationTarget] = useState<AdaptedInstance | null>(null);

  const activateMutation = useMutation({
    mutationFn: (variables: { strategyId: number; mt5AccountId: number; lotSize: number }) =>
      activateRobot(variables),
    onSuccess: () => {
      toast({ title: "Sucesso!", description: `Robô ativado.`, variant: "success" });
      queryClient.invalidateQueries({ queryKey: ['activeRobots'] });
      queryClient.invalidateQueries({ queryKey: ['accountPulse'] });
      setActivationTarget(null);
    },
    onError: (error: any) => {
      const errorMessage = error.response?.data?.error || "Não foi possível ativar o robô.";
      toast({ title: "Erro ao ativar robô", description: errorMessage, variant: "destructive" });
    },
  });

  const handleActivateConfirm = (data: { mt5AccountId: number; lotSize: number }) => {
    if (activationTarget && activationTarget.strategyId) {
      activateMutation.mutate({
        strategyId: activationTarget.strategyId,
        mt5AccountId: data.mt5AccountId,
        lotSize: data.lotSize,
      });
    } else {
      console.error("Activation target is missing or does not have a strategyId.", activationTarget);
      toast({ title: "Erro de Dados", description: "Não foi possível encontrar a ID da estratégia para reativação.", variant: "destructive" });
    }
  };

  const handleSwitchChange = (checked: boolean, robot: AdaptedInstance) => {
    if (checked) {
      setActivationTarget(robot);
    } else {
      deactivateMutation.mutate(robot.id);
    }
  };

  // Onboarding Tour Logic
  useEffect(() => {
    const hasSeenTour = localStorage.getItem('dashboard-tour-completed');
    if (!hasSeenTour) {
      setTimeout(() => setShowTour(true), 1000);
    }
  }, []);

  const completeTour = () => {
    localStorage.setItem('dashboard-tour-completed', 'true');
    setShowTour(false);
  };

  const skipTour = () => {
    localStorage.setItem('dashboard-tour-completed', 'true');
    setShowTour(false);
  };

  return (
    <>
      <PageLayout 
        title="Dashboard"
        description="Monitore seus robôs ativos, performance e histórico de operações em tempo real."
        showFooter={false}
      >
        <div className="container mx-auto px-6 py-12">
          {/* Overview Stats */}
          <div id="stats-section" className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            {isLoadingPulse ? (
              Array.from({ length: 4 }).map((_, i) => (
                <Card key={i} className="p-6 bg-gradient-card border-border/20">
                  <Skeleton className="h-4 w-1/2 mb-2" />
                  <Skeleton className="h-8 w-3/4 mb-1" />
                  <Skeleton className="h-3 w-1/3" />
                </Card>
              ))
            ) : (
              <>
                <Card className="p-6 bg-gradient-card border-border/20">
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="text-sm font-medium text-muted-foreground">Saldo Total</h3>
                    <svg className="w-4 h-4 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
                    </svg>
                  </div>
                  <div className="text-2xl font-bold">US$ {(pulseData?.equity ?? 0).toFixed(2)}</div>
                  <p className="text-xs text-muted-foreground">Capital disponível</p>
                </Card>

                <Card className="p-6 bg-gradient-card border-border/20">
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="text-sm font-medium text-muted-foreground">Lucro Hoje</h3>
                    <svg className="w-4 h-4 text-neon-green" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                    </svg>
                  </div>
                  <div className="text-2xl font-bold text-neon">{(pulseData?.pnl ?? 0) > 0 ? '+' : ''}US$ {(pulseData?.pnl ?? 0).toFixed(2)}</div>
                  <p className="text-xs text-muted-foreground">
                    {(pulseData?.balance ?? 0) > 0 ? `${(((pulseData?.pnl ?? 0) / (pulseData?.balance ?? 1)) * 100).toFixed(2)}% no dia` : '0.00% no dia'}
                  </p>
                </Card>

                <Card className="p-6 bg-gradient-card border-border/20">
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="text-sm font-medium text-muted-foreground">Robôs Ativos</h3>
                    <svg className="w-4 h-4 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                    </svg>
                  </div>
                  <div className="text-2xl font-bold">{pulseData?.active_robots_count || 0}/{pulseData?.total_robots_count || 0}</div>
                  <p className="text-xs text-muted-foreground">Em execução</p>
                </Card>

                <Card className="p-6 bg-gradient-card border-border/20">
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="text-sm font-medium text-muted-foreground">Taxa de Acerto</h3>
                    <svg className="w-4 h-4 text-yellow-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  {/* TODO: This metric should come from the backend */}
                  <div className="text-2xl font-bold text-yellow-400">N/A</div>
                  <p className="text-xs text-muted-foreground">Últimos 30 dias</p>
                </Card>
              </>
            )}
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Active Robots */}
            <div id="robots-section">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-2xl font-bold">Robôs Ativos</h2>
                <Button asChild variant="outline" size="sm">
                  <a href="/marketplace">+ Adicionar Robô</a>
                </Button>
              </div>

              <div className="space-y-4">
                {isLoadingRobots ? (
                  Array.from({ length: 3 }).map((_, i) => (
                    <Card key={i} className="p-6 bg-gradient-card border-border/20">
                      <Skeleton className="h-6 w-3/4 mb-4" />
                      <Skeleton className="h-4 w-full mb-2" />
                      <Skeleton className="h-4 w-full mb-4" />
                      <Skeleton className="h-10 w-full" />
                    </Card>
                  ))
                ) : (
                  activeRobots?.map((robot) => (
                    <Card key={robot.id} className="p-6 bg-gradient-card border-border/20">
                      <div className="flex items-start justify-between mb-4">
                        <div>
                          <h3 className="font-semibold text-lg">{robot.strategyName}</h3>
                          <div className="flex items-center gap-2 mt-1">
                            <Badge
                              variant={robot.isActive ? 'default' : 'secondary'}
                              className={robot.isActive ? 'bg-primary/10 text-primary' : 'bg-muted/50'}
                            >
                              {robot.isActive ? 'Em Execução' : 'Pausado'}
                            </Badge>
                            <Badge
                              variant="outline"
                              className={
                                robot.riskLevel === 'Baixo' ? 'border-green-400/20 text-green-400' :
                                robot.riskLevel === 'Médio' ? 'border-yellow-400/20 text-yellow-400' :
                                'border-red-400/20 text-red-400'
                              }
                            >
                              Risco {robot.riskLevel}
                            </Badge>
                          </div>
                        </div>
                        <Switch
                          checked={robot.isActive}
                          onCheckedChange={(checked) => handleSwitchChange(checked, robot)}
                          disabled={deactivateMutation.isPending}
                        />
                      </div>

                      <div className="grid grid-cols-2 gap-4 mb-4">
                        <div>
                          <p className="text-sm text-muted-foreground">Lucro Total</p>
                          <div className="font-semibold text-neon">{(robot.totalProfit ?? 0) > 0 ? '+' : ''}US$ {(robot.totalProfit ?? 0).toFixed(2)}</div>
                        </div>
                        <div>
                          <p className="text-sm text-muted-foreground">Taxa de Acerto</p>
                          <div className="font-semibold">{(robot.winRate ?? 0).toFixed(1)}%</div>
                        </div>
                      </div>

                      {/* Removed Progress and other buttons as data is not available */}
                    </Card>
                  ))
                )}
              </div>
            </div>

            {/* Recent Trades */}
            <div id="trades-section">
              <h2 className="text-2xl font-bold mb-6">Operações Recentes</h2>
              <Card className="p-6 bg-gradient-card border-border/20">
                <div className="space-y-4">
                  {isLoadingHistory || isLoadingAccounts ? (
                    Array.from({ length: 4 }).map((_, i) => (
                      <div key={i} className="flex items-center justify-between py-3 border-b border-border/20 last:border-0">
                        <Skeleton className="h-5 w-1/4" />
                        <Skeleton className="h-5 w-1/4" />
                      </div>
                    ))
                  ) : (
                    tradeHistory?.map((trade, index) => (
                      <div key={index} className="flex items-center justify-between py-3 border-b border-border/20 last:border-0">
                        <div className="flex items-center gap-3">
                          <div className={`w-2 h-2 rounded-full ${
                            trade.type === 'buy' ? 'bg-green-400' : 'bg-red-400'
                          }`} />
                          <div>
                            <div className="font-semibold">{trade.symbol}</div>
                            <div className="text-sm text-muted-foreground">
                              {trade.type.toUpperCase()} {trade.volume ?? 'N/A'} lots @ {(trade.openPrice !== null ? trade.openPrice : 0).toFixed(2)}
                            </div>
                          </div>
                        </div>
                        <div className="text-right">
                          {trade.profit !== null ? (
                            <div className={`font-semibold ${
                              trade.profit >= 0 ? 'text-neon' : 'text-red-400'
                            }`}>
                              {trade.profit >= 0 ? '+' : ''}US$ {trade.profit.toFixed(2)}
                            </div>
                          ) : (
                            <div className="text-sm text-muted-foreground italic">Em andamento</div>
                          )}
                          <div className="text-sm text-muted-foreground">{new Date(trade.openTime).toLocaleTimeString()}</div>
                        </div>
                      </div>
                    ))
                  )}
                </div>
                <Button variant="outline" className="w-full mt-4" asChild>
                  <a href="/trading-history">Ver Todas as Operações</a>
                </Button>
              </Card>

              {/* Performance Chart */}
                <div id="chart-section">
                    <Card className="p-6 mt-6 bg-gradient-card border-border/20">
                        <h3 className="font-semibold mb-4">Performance dos Últimos 7 Dias</h3>
                        <div className="h-48">
                            {isLoadingEquityHistory ? (
                                <Skeleton className="h-full w-full" />
                            ) : !equityHistory || equityHistory.length === 0 ? (
                                <div className="flex items-center justify-center h-full text-muted-foreground">
                                    Dados insuficientes para gerar o gráfico.
                                </div>
                            ) : (
                                <ResponsiveContainer width="100%" height="100%">
                                    <AreaChart data={equityHistory} margin={{ top: 5, right: 20, left: -10, bottom: 5 }}>
                                        <defs>
                                            <linearGradient id="colorEquity" x1="0" y1="0" x2="0" y2="1">
                                                <stop offset="5%" stopColor="hsl(var(--primary))" stopOpacity={0.8}/>
                                                <stop offset="95%" stopColor="hsl(var(--primary))" stopOpacity={0}/>
                                            </linearGradient>
                                        </defs>
                                        <XAxis
                                            dataKey="date"
                                            tickFormatter={(str) => new Date(str).toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' })}
                                            stroke="hsl(var(--muted-foreground))"
                                            fontSize={12}
                                        />
                                        <YAxis
                                            orientation="right"
                                            tickFormatter={(val) => `$${(val / 1000).toFixed(1)}k`}
                                            stroke="hsl(var(--muted-foreground))"
                                            fontSize={12}
                                        />
                                        <Tooltip
                                            contentStyle={{
                                                backgroundColor: 'hsl(var(--background))',
                                                borderColor: 'hsl(var(--border))'
                                            }}
                                            labelFormatter={(label) => new Date(label).toLocaleDateString('pt-BR', {weekday: 'long', day: 'numeric', month: 'long'})}
                                            formatter={(value: number) => [value.toLocaleString('en-US', { style: 'currency', currency: 'USD' }), 'Equity']}
                                        />
                                        <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border) / 0.5)" />
                                        <Area type="monotone" dataKey="equity" stroke="hsl(var(--primary))" fillOpacity={1} fill="url(#colorEquity)" />
                                    </AreaChart>
                                </ResponsiveContainer>
                            )}
                        </div>
                         <div className="text-center mt-4">
                            <div className={`text-2xl font-bold ${weeklyGrowth >= 0 ? 'text-neon' : 'text-red-400'}`}>
                                {weeklyGrowth >= 0 ? '+' : ''}{weeklyGrowth.toFixed(2)}%
                            </div>
                            <p className="text-sm text-muted-foreground">Crescimento na semana</p>
                        </div>
                    </Card>
                </div>
            </div>
          </div>
        </div>
      </PageLayout>

      <OnboardingTour
        isVisible={showTour}
        onComplete={completeTour}
        onSkip={skipTour}
      />

      {activationTarget && (
        <ActivationDialog
          robot={activationTarget}
          isOpen={!!activationTarget}
          onClose={() => setActivationTarget(null)}
          onConfirm={handleActivateConfirm}
          isActivating={activateMutation.isPending}
        />
      )}
    </>
  );
};

export default Dashboard;