import { PageLayout } from "@/components/PageLayout";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";
import {
  TrendingUp,
  Target,
  Shield,
  Settings,
  Play,
  BarChart3,
  Calendar,
  Users,
  Star,
  Download,
  Loader2,
} from "lucide-react";
import { useParams } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getStrategyDetails, getAccounts, activateRobot, deactivateRobot, getActiveRobots, AdaptedInstance, adaptInstances } from "@/api";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter,
  DialogDescription,
} from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useState } from "react";
import { useToast } from "@/hooks/use-toast";


const activationSchema = z.object({
  mt5AccountId: z.string().nonempty("Selecione uma conta"),
  lotSize: z.coerce.number().min(0.01, "O lote mínimo é 0.01"),
});

type ActivationForm = z.infer<typeof activationSchema>;


const RobotDetails = () => {
  const { id } = useParams<{ id: string }>();
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [isActivationModalOpen, setIsActivationModalOpen] = useState(false);

  const { data: robotData, isLoading, isError } = useQuery({
    queryKey: ['strategyDetails', id],
    queryFn: () => getStrategyDetails(id!),
    enabled: !!id,
  });
  
  const { data: accounts = [] } = useQuery({
    queryKey: ['accounts'],
    queryFn: getAccounts,
  });

  const { data: activeRobots, isLoading: isLoadingActiveRobots } = useQuery({
    queryKey: ['activeRobots'],
    queryFn: getActiveRobots,
  });

  const {
    register,
    handleSubmit,
    formState: { errors },
    setValue,
  } = useForm<ActivationForm>({
    resolver: zodResolver(activationSchema),
  });

  const activationMutation = useMutation({
    mutationFn: activateRobot,
    onSuccess: (newlyActivatedInstance) => {
      toast({
        title: "Robô Ativado!",
        description: "A sua instância foi ativada com sucesso.",
      });
      const adaptedInstance = adaptInstances([newlyActivatedInstance])[0];
      queryClient.setQueryData(['activeRobots'], (oldData: AdaptedInstance[] | undefined) => {
        return oldData ? [...oldData, adaptedInstance] : [adaptedInstance];
      });
      setIsActivationModalOpen(false);
    },
    onError: (error: any) => {
      const errorMessage = error.response?.data?.error || "Ocorreu um erro ao ativar o robô.";
      toast({
        title: "Erro na Ativação",
        description: errorMessage,
        variant: "destructive",
      });
    },
  });
  
  const onActivateSubmit = (data: ActivationForm) => {
    activationMutation.mutate({
      strategyId: parseInt(id!),
      mt5AccountId: parseInt(data.mt5AccountId),
      lotSize: data.lotSize,
    });
  };

  const deactivateMutation = useMutation({
    mutationFn: deactivateRobot,
    onSuccess: (_, deactivatedInstanceId) => {
      toast({
        title: "Sucesso!",
        description: "Robô desativado.",
      });
      queryClient.setQueryData(['activeRobots'], (oldData: AdaptedInstance[] | undefined) => {
        return oldData ? oldData.filter((instance) => instance.id !== deactivatedInstanceId) : [];
      });
    },
    onError: (error: any) => {
      toast({
        title: "Erro ao desativar",
        description: error.message || "Não foi possível desativar o robô.",
        variant: "destructive",
      });
    },
  });


  if (isLoading) {
    return (
      <PageLayout>
        <div className="container mx-auto px-6 py-12">
          <Skeleton className="h-12 w-1/2 mb-4" />
          <Skeleton className="h-6 w-3/4 mb-8" />
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
            {Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-32 rounded-lg" />)}
          </div>
          <Skeleton className="h-96 rounded-lg" />
        </div>
      </PageLayout>
    );
  }

  if (isError || !robotData) {
    return (
      <PageLayout>
        <div className="container mx-auto px-6 py-12 text-center">
          <h1 className="text-2xl font-bold text-destructive">Erro</h1>
          <p className="text-muted-foreground">Não foi possível carregar os detalhes da estratégia.</p>
        </div>
      </PageLayout>
    );
  }

  // Helper to safely access backtest results from the 'original' property
  const backtest = robotData.original?.backtest_results || {};
  const activeInstance = activeRobots?.find(activeRobot => activeRobot.strategyId === robotData.id && activeRobot.isActive);
  const totalTrades = backtest['Total de Trades'] || 0;
  const winRate = backtest['Taxa de Acerto (Win Rate) [%]'] || 0;
  const sharpeRatio = backtest['Índice Sharpe'] || 0;
  const avgTrade = backtest['Resultado Médio por Trade [%]'] || 0;
  const maxDrawdown = backtest['Drawdown Máximo [%]'] || 0;

  return (
    <PageLayout>
      <div className="container mx-auto px-6 py-12">
        {/* Header Section */}
        <div className="mb-8">
          <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6">
            <div>
              <div className="flex items-center gap-3 mb-2">
                <Badge variant="outline" className="text-xs">ID: {robotData.id}</Badge>
                <Badge className={"bg-green-500/10 text-green-500 border-green-500/20"}>
                  Verificada
                </Badge>
              </div>
              <h1 className="text-4xl font-bold mb-2">{robotData.name}</h1>
              <p className="text-muted-foreground text-lg max-w-3xl">{robotData.description}</p>

              <div className="flex items-center gap-6 mt-4">
                <div className="flex items-center gap-1">
                  <Star className="w-5 h-5 fill-primary text-primary" />
                  <span className="font-semibold">N/A</span>
                </div>
                <div className="flex items-center gap-2">
                  <Users className="w-4 h-4 text-muted-foreground" />
                  <span className="text-sm">N/A assinantes</span>
                </div>
                <div className="text-sm text-muted-foreground">
                  por Aura Quant Team
                </div>
              </div>
            </div>

            <div className="flex items-center">
              {activeInstance ? (
                <Button
                  size="lg"
                  variant="destructive"
                  onClick={() => {
                    if (activeInstance) {
                      deactivateMutation.mutate(activeInstance.id);
                    }
                  }}
                  disabled={deactivateMutation.isPending || isLoadingActiveRobots}
                >
                  {deactivateMutation.isPending ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Play className="w-4 h-4 mr-2" />}
                  Desativar Robô
                </Button>
              ) : (
              <Dialog open={isActivationModalOpen} onOpenChange={setIsActivationModalOpen}>
                <DialogTrigger asChild>
                  <Button size="lg" className="bg-gradient-primary text-black font-semibold" disabled={isLoadingActiveRobots}>
                    {isLoadingActiveRobots ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Play className="w-4 h-4 mr-2" />}
                    Ativar Robô
                  </Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle>Ativar {robotData.name}</DialogTitle>
                    <DialogDescription>
                      Selecione sua conta MT5 e defina o tamanho do lote para iniciar.
                    </DialogDescription>
                  </DialogHeader>
                  <form onSubmit={handleSubmit(onActivateSubmit)}>
                    <div className="space-y-4">
                      <div>
                        <Label htmlFor="mt5AccountId">Conta MT5</Label>
                        <Select onValueChange={(value) => setValue("mt5AccountId", value)}>
                          <SelectTrigger>
                            <SelectValue placeholder="Selecione uma conta" />
                          </SelectTrigger>
                          <SelectContent>
                            {accounts.map((account) => (
                              <SelectItem key={account.id} value={String(account.id)}>
                                {account.nickname} ({account.account_login})
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                        {errors.mt5AccountId && <p className="text-sm text-destructive mt-1">{errors.mt5AccountId.message}</p>}
                      </div>
                      <div>
                        <Label htmlFor="lotSize">Tamanho do Lote</Label>
                        <Input id="lotSize" type="number" step="0.01" {...register("lotSize")} />
                        {errors.lotSize && <p className="text-sm text-destructive mt-1">{errors.lotSize.message}</p>}
                      </div>
                    </div>
                    <DialogFooter className="mt-4">
                      <Button type="submit" disabled={activationMutation.isPending}>
                        {activationMutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                        Ativar Agora
                      </Button>
                    </DialogFooter>
                  </form>
                </DialogContent>
              </Dialog>
              )}
            </div>

          </div>
        </div>

        {/* Performance Overview Cards */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <Card className="border-border/20 bg-gradient-to-br from-background to-muted/5">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-green-500" />
                Retorno Total
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-green-500">{robotData.performance || 'N/A'}</div>
              <p className="text-xs text-muted-foreground mt-1">Desde o lançamento</p>
            </CardContent>
          </Card>

          <Card className="border-border/20 bg-gradient-to-br from-background to-muted/5">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <Calendar className="w-4 h-4 text-primary" />
                Trades / Mês
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{robotData.tradesPerMonth || 'N/A'}</div>
              <p className="text-xs text-muted-foreground mt-1">Média dos últimos 12 meses</p>
            </CardContent>
          </Card>

          <Card className="border-border/20 bg-gradient-to-br from-background to-muted/5">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <Target className="w-4 h-4 text-blue-500" />
                Taxa de Acerto
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{winRate.toFixed(1)}%</div>
              <Progress value={winRate} className="mt-2 h-2" />
            </CardContent>
          </Card>

          <Card className="border-border/20 bg-gradient-to-br from-background to-muted/5">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <Shield className="w-4 h-4 text-orange-500" />
                Max Drawdown
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-orange-500">{maxDrawdown.toFixed(2)}%</div>
              <p className="text-xs text-muted-foreground mt-1">Maior perda consecutiva</p>
            </CardContent>
          </Card>
        </div>

        {/* Detailed Information Tabs */}
        <Tabs defaultValue="performance" className="space-y-6">
          <TabsList className="grid w-full grid-cols-4 lg:w-auto lg:grid-cols-4">
            <TabsTrigger value="performance">Performance</TabsTrigger>
            <TabsTrigger value="trades">Histórico</TabsTrigger>
            <TabsTrigger value="settings">Configurações</TabsTrigger>
            <TabsTrigger value="info">Informações</TabsTrigger>
          </TabsList>

          <TabsContent value="performance" className="space-y-6">
            <div className="grid lg:grid-cols-3 gap-6">
              <Card className="lg:col-span-2">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <BarChart3 className="w-5 h-5" />
                    Curva de Performance
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="h-64 bg-gradient-to-br from-muted/10 to-muted/5 rounded-lg flex items-center justify-center">
                    <div className="text-center text-muted-foreground">
                      <BarChart3 className="w-12 h-12 mx-auto mb-2 opacity-50" />
                      <p>Gráfico de performance indisponível.</p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Métricas Avançadas</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex justify-between">
                    <span className="text-sm text-muted-foreground">Índice Sharpe</span>
                    <span className="font-semibold">{sharpeRatio.toFixed(2)}</span>
                  </div>
                  <Separator />
                  <div className="flex justify-between">
                    <span className="text-sm text-muted-foreground">Lucro Médio por Trade</span>
                    <span className="font-semibold text-green-500">+{avgTrade.toFixed(2)}%</span>
                  </div>
                  <Separator />
                  <div className="flex justify-between">
                    <span className="text-sm text-muted-foreground">Total de Trades</span>
                    <span className="font-semibold">{totalTrades}</span>
                  </div>
                  <Separator />
                  <div className="flex justify-between">
                    <span className="text-sm text-muted-foreground">Trades Vencedores</span>
                    <span className="font-semibold text-green-500">{Math.round(totalTrades * winRate / 100)}</span>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="trades" className="space-y-6">
             <Card>
              <CardHeader>
                <CardTitle>Histórico de Trades (Exemplo)</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground">O histórico de trades real para esta estratégia não está disponível nesta visualização.</p>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="settings" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Configurações Padrão</CardTitle>
              </CardHeader>
              <CardContent>
                 <p className="text-muted-foreground">As configurações são definidas no momento da ativação do robô.</p>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="info" className="space-y-6">
            <div className="grid lg:grid-cols-3 gap-6">
              <Card className="lg:col-span-2">
                <CardHeader>
                  <CardTitle>Sobre Esta Estratégia</CardTitle>
                </CardHeader>
                <CardContent className="prose prose-sm max-w-none text-muted-foreground leading-relaxed">
                  <p>{robotData.description}</p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Informações Técnicas</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <div className="text-sm text-muted-foreground">Categoria</div>
                    <div className="font-semibold">{robotData.category}</div>
                  </div>
                  <Separator />
                  <div>
                    <div className="text-sm text-muted-foreground">Capital Mínimo</div>
                    <div className="font-semibold">${robotData.original?.suggested_capital || 'N/A'}</div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </PageLayout>
  );
};

export default RobotDetails;
