import { useState, useMemo } from "react";
import { Link } from "react-router-dom";
import { PageLayout } from "@/components/PageLayout";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getStrategies, activateRobot, deactivateRobot, getAccounts, getActiveRobots, AdaptedStrategy, AdaptedInstance, adaptInstances } from "@/api";
import { Skeleton } from "@/components/ui/skeleton";
import { useToast } from "@/hooks/use-toast";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Terminal } from "lucide-react";

// Activation Dialog Component
const ActivationDialog = ({
  robot,
  isOpen,
  onClose,
  onConfirm,
  isActivating,
}: {
  robot: AdaptedStrategy;
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
          <DialogTitle>Ativar Robô: {robot.name}</DialogTitle>
          <DialogDescription>
            Selecione a conta e configure os parâmetros para ativar este robô.
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
                  <SelectTrigger className="col-span-3" id="account">
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


const Marketplace = () => {
  const { data: strategies, isLoading, isError, error } = useQuery({
    queryKey: ['strategies'],
    queryFn: getStrategies,
  });

  const { data: activeRobots, isLoading: isLoadingActiveRobots } = useQuery({
    queryKey: ['activeRobots'],
    queryFn: getActiveRobots,
  });

  const [activationTarget, setActivationTarget] = useState<AdaptedStrategy | null>(null);
  const { toast } = useToast();
  const queryClient = useQueryClient();

  const activateMutation = useMutation({
    mutationFn: (variables: { strategyId: number; mt5AccountId: number; lotSize: number }) =>
      activateRobot(variables),
    onSuccess: (newlyActivatedInstance) => {
      toast({
        title: "Sucesso!",
        description: `Robô ativado.`,
        variant: "success",
      });
      const adaptedInstance = adaptInstances([newlyActivatedInstance])[0];
      queryClient.setQueryData(['activeRobots'], (oldData: AdaptedInstance[] | undefined) => {
        return oldData ? [...oldData, adaptedInstance] : [adaptedInstance];
      });
      setActivationTarget(null);
    },
    onError: (error: any) => {
      const errorMessage = error.response?.data?.error || "Não foi possível ativar o robô.";
      toast({
        title: "Erro ao ativar robô",
        description: errorMessage,
        variant: "destructive",
      });
    },
  });

  const deactivateMutation = useMutation({
    mutationFn: deactivateRobot,
    onSuccess: (_, deactivatedInstanceId) => {
      toast({
        title: "Sucesso!",
        description: "Robô desativado.",
        variant: "success",
      });
      queryClient.setQueryData(['activeRobots'], (oldData: AdaptedInstance[] | undefined) => {
        return oldData ? oldData.filter((instance) => instance.id !== deactivatedInstanceId) : [];
      });
    },
    onError: (error: any) => {
      const errorMessage = error.response?.data?.error || "Não foi possível desativar o robô.";
      toast({
        title: "Erro ao desativar robô",
        description: errorMessage,
        variant: "destructive",
      });
    },
  });

  const [searchTerm, setSearchTerm] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("todos");
  const [selectedRisk, setSelectedRisk] = useState("todos");
  const [selectedPrice, setSelectedPrice] = useState("todos");

  const categories = ["Todos", ...new Set(strategies?.map(s => s.category) || [])];
  const riskLevels = ["Todos", "Baixo", "Médio", "Alto"];

  const filteredStrategies = useMemo(() => {
    if (!strategies) return [];
    return strategies.filter(robot => {
      const searchTermMatch = robot.name.toLowerCase().includes(searchTerm.toLowerCase());
      const categoryMatch = selectedCategory === 'todos' || robot.category.toLowerCase() === selectedCategory;
      const riskMatch = selectedRisk === 'todos' || robot.riskLevel.toLowerCase() === selectedRisk;
      const priceMatch = selectedPrice === 'todos' || (selectedPrice === 'free' && robot.isFree) || (selectedPrice === 'premium' && !robot.isFree);
      return searchTermMatch && categoryMatch && riskMatch && priceMatch;
    });
  }, [strategies, searchTerm, selectedCategory, selectedRisk, selectedPrice]);

  const handleActivateConfirm = (data: { mt5AccountId: number; lotSize: number }) => {
    if (activationTarget) {
      activateMutation.mutate({
        strategyId: activationTarget.id,
        ...data,
      });
    }
  };

  const renderRobotGrid = () => {
    if (isLoading) {
      return (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {Array.from({ length: 6 }).map((_, i) => (
            <Card key={i} className="p-6 bg-gradient-card border-border/20">
              <Skeleton className="h-6 w-3/4 mb-2" />
              <Skeleton className="h-4 w-1/4 mb-4" />
              <Skeleton className="h-4 w-full mb-2" />
              <Skeleton className="h-4 w-full mb-4" />
              <div className="grid grid-cols-2 gap-4 mb-4">
                <Skeleton className="h-4 w-1/2" />
                <Skeleton className="h-4 w-1/2" />
                <Skeleton className="h-4 w-1/2" />
                <Skeleton className="h-4 w-1/2" />
              </div>
              <div className="flex gap-2">
                <Skeleton className="h-10 w-full" />
                <Skeleton className="h-10 w-full" />
              </div>
            </Card>
          ))}
        </div>
      );
    }

    if (isError) {
      return (
        <div className="text-center py-10 text-red-500">
          <p>Ocorreu um erro ao buscar os robôs.</p>
          <p className="text-sm text-muted-foreground">{(error as Error).message}</p>
        </div>
      );
    }

    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredStrategies.map((robot) => {
          const activeInstance = activeRobots?.find(activeRobot => activeRobot.strategyId === robot.id && activeRobot.isActive);
          
          const handleButtonClick = () => {
            if (activeInstance) {
              deactivateMutation.mutate(activeInstance.id);
            } else {
              setActivationTarget(robot);
            }
          };

          return (
            <Card key={robot.id} className="p-6 bg-gradient-card border-border/20 hover:border-primary/20 transition-all duration-300 hover:scale-[1.02]">
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h3 className="font-semibold text-lg mb-1">{robot.name}</h3>
                  <Badge
                    variant={robot.isFree ? 'secondary' : 'default'}
                    className={robot.isFree ? 'bg-primary/10 text-primary' : 'bg-yellow-500/10 text-yellow-400'}
                  >
                    {robot.isFree ? 'Verificado' : 'Premium'}
                  </Badge>
                </div>
                <div className="text-right">
                  <div className="font-bold text-lg">{robot.isFree ? 'Gratuito' : 'Premium'}</div>
                </div>
              </div>

              <p className="text-muted-foreground mb-4 text-sm">
                {robot.description}
              </p>

              <div className="grid grid-cols-2 gap-4 mb-4 text-sm">
                <div>
                  <span className="text-muted-foreground">Performance:</span>
                  <div className="font-semibold text-neon">{robot.performance ?? 'N/A'}</div>
                </div>
                <div>
                  <span className="text-muted-foreground">Trades/Mês:</span>
                  <div className="font-semibold">{robot.tradesPerMonth ?? 'N/A'}</div>
                </div>
                <div>
                  <span className="text-muted-foreground">Categoria:</span>
                  <div className="font-semibold">{robot.category}</div>
                </div>
                <div>
                  <span className="text-muted-foreground">Risco:</span>
                  <div className={`font-semibold ${
                    robot.riskLevel === 'Baixo' ? 'text-green-400' :
                    robot.riskLevel === 'Médio' ? 'text-yellow-400' :
                    robot.riskLevel === 'Alto' ? 'text-red-400' : ''
                  }`}>
                    {robot.riskLevel}
                  </div>
                </div>
              </div>

              <div className="flex gap-2">
                <Button asChild variant="outline" size="sm" className="flex-1">
                  <Link to={`/marketplace/strategy/${robot.id}`}>
                    Ver Detalhes
                  </Link>
                </Button>
                <Button
                  size="sm"
                  variant={activeInstance ? "destructive" : "default"}
                  className="flex-1"
                  onClick={handleButtonClick}
                  disabled={isLoadingActiveRobots || activateMutation.isPending || deactivateMutation.isPending}
                >
                  {isLoadingActiveRobots ? '...' : activeInstance ? 'Desativar' : 'Ativar'}
                </Button>
              </div>
            </Card>
          )
        })}
      </div>
    );
  };

  return (
    <PageLayout 
      title="Marketplace de Robôs"
      description="Descubra centenas de robôs de trading verificados e escolha o que melhor se adapta ao seu perfil de investimento."
    >
      <div className="container mx-auto px-6 py-12">
        {/* Filters */}
        <div className="mb-8 p-6 bg-card rounded-2xl border border-border/20">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <label className="text-sm font-medium mb-2 block">Pesquisar</label>
              <Input
                placeholder="Nome do robô..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block">Categoria</label>
              <Select value={selectedCategory} onValueChange={setSelectedCategory}>
                <SelectTrigger>
                  <SelectValue placeholder="Selecione..." />
                </SelectTrigger>
                <SelectContent>
                  {categories.map(cat => (
                    <SelectItem key={cat} value={cat.toLowerCase()}>{cat}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block">Nível de Risco</label>
              <Select value={selectedRisk} onValueChange={setSelectedRisk}>
                <SelectTrigger>
                  <SelectValue placeholder="Selecione..." />
                </SelectTrigger>
                <SelectContent>
                  {riskLevels.map(risk => (
                    <SelectItem key={risk} value={risk.toLowerCase()}>{risk}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block">Preço</label>
              <Select value={selectedPrice} onValueChange={setSelectedPrice}>
                <SelectTrigger>
                  <SelectValue placeholder="Todos" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="todos">Todos</SelectItem>
                  <SelectItem value="free">Gratuitos</SelectItem>
                  <SelectItem value="premium">Premium</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-12">
          <Card className="p-6 text-center bg-gradient-card border-border/20">
            <div className="text-2xl font-bold text-primary mb-2">{strategies?.length || 0}</div>
            <p className="text-muted-foreground">Robôs Disponíveis</p>
          </Card>
          <Card className="p-6 text-center bg-gradient-card border-border/20">
            {/* TODO: Add backend endpoint for this */}
            <div className="text-2xl font-bold text-primary mb-2">10K+</div>
            <p className="text-muted-foreground">Usuários Ativos</p>
          </Card>
          <Card className="p-6 text-center bg-gradient-card border-border/20">
            <div className="text-2xl font-bold text-neon mb-2">
              {(() => {
                if (!strategies || strategies.length === 0) return 'N/A';
                const perfValues = strategies
                  .map(s => parseFloat(s.performance))
                  .filter(p => !isNaN(p));
                if (perfValues.length === 0) return 'N/A';
                const avg = perfValues.reduce((a, b) => a + b, 0) / perfValues.length;
                return `${avg > 0 ? '+' : ''}${avg.toFixed(2)}%`;
              })()}
            </div>
            <p className="text-muted-foreground">Performance Média</p>
          </Card>
          <Card className="p-6 text-center bg-gradient-card border-border/20">
            {/* TODO: Add backend endpoint for this */}
            <div className="text-2xl font-bold text-yellow-400 mb-2">99.8%</div>
            <p className="text-muted-foreground">Uptime</p>
          </Card>
        </div>

        {/* Robots Grid */}
        {renderRobotGrid()}

        {/* Load More */}
        <div className="text-center mt-12">
          <Button variant="outline" size="lg">
            Carregar Mais Robôs
          </Button>
        </div>

        {activationTarget && (
          <ActivationDialog
            robot={activationTarget}
            isOpen={!!activationTarget}
            onClose={() => setActivationTarget(null)}
            onConfirm={handleActivateConfirm}
            isActivating={activateMutation.isPending}
          />
        )}
      </div>
    </PageLayout>
  );
};

export default Marketplace;