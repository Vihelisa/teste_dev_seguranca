import { PageLayout } from "@/components/PageLayout";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Calendar } from "@/components/ui/calendar";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { CalendarIcon, ArrowUpIcon, ArrowDownIcon, MoreHorizontal, Filter } from "lucide-react";
import { useState, useMemo } from "react";
import { format } from "date-fns";
import { ptBR } from "date-fns/locale";
import { useQuery } from "@tanstack/react-query";
import { getAccounts, getTradeHistory } from "@/api";
import { Skeleton } from "@/components/ui/skeleton";

const ITEMS_PER_PAGE = 10;

const TradingHistory = () => {
  const [filters, setFilters] = useState({
    strategy: 'todos',
    symbol: 'todos',
    direction: 'todos',
    dateFrom: undefined as Date | undefined,
    dateTo: undefined as Date | undefined,
  });

  const [appliedFilters, setAppliedFilters] = useState(filters);
  const [currentPage, setCurrentPage] = useState(1);

  // Data Fetching
  const { data: accounts, isLoading: isLoadingAccounts } = useQuery({
    queryKey: ['accounts'],
    queryFn: getAccounts,
  });

  const primaryAccountId = accounts?.[0]?.id;

  const { data: trades, isLoading: isLoadingHistory } = useQuery({
    queryKey: ['tradeHistory', primaryAccountId],
    queryFn: () => getTradeHistory(primaryAccountId!),
    enabled: !!primaryAccountId,
  });

  // Derived data for filters
  const availableSymbols = useMemo(() => {
    if (!trades) return [];
    return ['Todos', ...new Set(trades.map(t => t.symbol))];
  }, [trades]);

  const availableStrategies = useMemo(() => {
    if (!trades) return [];
    return ['Todos', ...new Set(trades.map(t => t.strategyName))];
  }, [trades]);

  // Filtering logic
  const filteredTrades = useMemo(() => {
    if (!trades) return [];
    return trades.filter(trade => {
      const tradeDate = new Date(trade.openTime);
      const dateFromMatch = !appliedFilters.dateFrom || tradeDate >= appliedFilters.dateFrom;
      const dateToMatch = !appliedFilters.dateTo || tradeDate <= appliedFilters.dateTo;
      const symbolMatch = appliedFilters.symbol === 'todos' || trade.symbol.toLowerCase() === appliedFilters.symbol;
      const directionMatch = appliedFilters.direction === 'todos' || trade.type === appliedFilters.direction;
      const strategyMatch = appliedFilters.strategy === 'todos' || trade.strategyName.toLowerCase() === appliedFilters.strategy;

      return dateFromMatch && dateToMatch && symbolMatch && directionMatch && strategyMatch;
    });
  }, [trades, appliedFilters]);

  // Pagination logic
  const paginatedTrades = useMemo(() => {
    return filteredTrades.slice((currentPage - 1) * ITEMS_PER_PAGE, currentPage * ITEMS_PER_PAGE);
  }, [filteredTrades, currentPage]);

  const totalPages = Math.ceil(filteredTrades.length / ITEMS_PER_PAGE);

  // Summary stats logic
  const summaryStats = useMemo(() => {
    const data = filteredTrades || [];
    const totalTrades = data.length;
    const totalPnl = data.reduce((acc, trade) => acc + (trade.profit || 0), 0);
    const winningTrades = data.filter(trade => trade.profit !== null && trade.profit >= 0).length;
    const winRate = totalTrades > 0 ? (winningTrades / totalTrades) * 100 : 0;

    return { totalTrades, totalPnl, winRate };
  }, [filteredTrades]);

  const handleFilterChange = (key: keyof typeof filters, value: any) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  };

  const handleApplyFilters = () => {
    setCurrentPage(1);
    setAppliedFilters(filters);
  };

  const isLoading = isLoadingHistory || isLoadingAccounts;

  return (
    <PageLayout 
      title="Histórico de Operações"
      description="Visualize e analise todas as suas operações de trading com filtros avançados e métricas detalhadas."
      showFooter={false}
    >
      <div className="container mx-auto px-6 py-12">
        {/* Filters */}
        <Card className="p-6 bg-gradient-card border-border/20 mb-8">
          <div className="flex items-center gap-2 mb-4">
            <Filter className="w-4 h-4" />
            <h3 className="font-semibold">Filtros</h3>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-4">
            <div>
              <Label htmlFor="strategy">Estratégia</Label>
              <Select value={filters.strategy} onValueChange={(v) => handleFilterChange('strategy', v)}>
                <SelectTrigger>
                  <SelectValue placeholder="Selecione..." />
                </SelectTrigger>
                <SelectContent>
                  {availableStrategies.map(strategy => (
                    <SelectItem key={strategy} value={strategy.toLowerCase()}>{strategy}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label htmlFor="symbol">Ativo</Label>
              <Select value={filters.symbol} onValueChange={(v) => handleFilterChange('symbol', v)}>
                <SelectTrigger>
                  <SelectValue placeholder="Selecione..." />
                </SelectTrigger>
                <SelectContent>
                  {availableSymbols.map(symbol => (
                    <SelectItem key={symbol} value={symbol.toLowerCase()}>{symbol}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label htmlFor="direction">Direção</Label>
              <Select value={filters.direction} onValueChange={(v) => handleFilterChange('direction', v)}>
                <SelectTrigger>
                  <SelectValue placeholder="Selecione..." />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="todos">Todas</SelectItem>
                  <SelectItem value="buy">Compra</SelectItem>
                  <SelectItem value="sell">Venda</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label>Data Inicial</Label>
              <Popover>
                <PopoverTrigger asChild>
                  <Button variant="outline" className="w-full justify-start text-left font-normal">
                    <CalendarIcon className="mr-2 h-4 w-4" />
                    {filters.dateFrom ? format(filters.dateFrom, "dd/MM/yyyy", { locale: ptBR }) : "Selecionar"}
                  </Button>
                </PopoverTrigger>
                <PopoverContent className="w-auto p-0" align="start">
                  <Calendar
                    mode="single"
                    selected={filters.dateFrom}
                    onSelect={(d) => handleFilterChange('dateFrom', d)}
                    initialFocus
                  />
                </PopoverContent>
              </Popover>
            </div>

            <div>
              <Label>Data Final</Label>
              <Popover>
                <PopoverTrigger asChild>
                  <Button variant="outline" className="w-full justify-start text-left font-normal">
                    <CalendarIcon className="mr-2 h-4 w-4" />
                    {filters.dateTo ? format(filters.dateTo, "dd/MM/yyyy", { locale: ptBR }) : "Selecionar"}
                  </Button>
                </PopoverTrigger>
                <PopoverContent className="w-auto p-0" align="start">
                  <Calendar
                    mode="single"
                    selected={filters.dateTo}
                    onSelect={(d) => handleFilterChange('dateTo', d)}
                    initialFocus
                  />
                </PopoverContent>
              </Popover>
            </div>

            <div className="flex items-end">
              <Button className="w-full bg-gradient-primary" onClick={handleApplyFilters}>
                Aplicar Filtros
              </Button>
            </div>
          </div>
        </Card>

        {/* Summary Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          {isLoading ? (
            Array.from({ length: 4 }).map((_, i) => (
              <Card key={i} className="p-6 text-center bg-gradient-card border-border/20">
                <Skeleton className="h-8 w-1/2 mx-auto mb-2" />
                <Skeleton className="h-4 w-3/4 mx-auto" />
              </Card>
            ))
          ) : (
            <>
              <Card className="p-6 text-center bg-gradient-card border-border/20">
                <div className="text-2xl font-bold text-primary mb-2">{summaryStats.totalTrades}</div>
                <p className="text-muted-foreground">Total de Operações</p>
              </Card>
              <Card className="p-6 text-center bg-gradient-card border-border/20">
                <div className={`text-2xl font-bold mb-2 ${summaryStats.totalPnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                  {summaryStats.totalPnl >= 0 ? '+' : ''}US$ {summaryStats.totalPnl.toFixed(2)}
                </div>
                <p className="text-muted-foreground">P&L Total</p>
              </Card>
              <Card className="p-6 text-center bg-gradient-card border-border/20">
                <div className="text-2xl font-bold text-yellow-400 mb-2">{summaryStats.winRate.toFixed(1)}%</div>
                <p className="text-muted-foreground">Taxa de Acerto</p>
              </Card>
              <Card className="p-6 text-center bg-gradient-card border-border/20">
                <div className="text-2xl font-bold mb-2">N/A</div>
                <p className="text-muted-foreground">Duração Média</p>
                {/* TODO: Average duration requires more data from API */}
              </Card>
            </>
          )}
        </div>

        {/* Trading Table */}
        <Card className="bg-gradient-card border-border/20">
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Data/Hora</TableHead>
                  <TableHead>Estratégia</TableHead>
                  <TableHead>Ativo</TableHead>
                  <TableHead>Direção</TableHead>
                  <TableHead>Lote</TableHead>
                  <TableHead>Entrada</TableHead>
                  <TableHead>Saída</TableHead>
                  <TableHead>Resultado</TableHead>
                  <TableHead>Ações</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {isLoading ? (
                  Array.from({ length: ITEMS_PER_PAGE }).map((_, i) => (
                    <TableRow key={i}>
                      <TableCell colSpan={9}>
                        <Skeleton className="h-5 w-full" />
                      </TableCell>
                    </TableRow>
                  ))
                ) : (
                  paginatedTrades?.map((trade) => (
                    <TableRow key={trade.id}>
                      <TableCell className="font-mono text-sm">
                        {format(new Date(trade.openTime), "dd/MM/yy HH:mm:ss", { locale: ptBR })}
                      </TableCell>
                      <TableCell>{trade.strategyName}</TableCell>
                      <TableCell>
                        <Badge variant="outline">{trade.symbol}</Badge>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          {trade.type === "buy" ? (
                            <ArrowUpIcon className="w-4 h-4 text-green-400" />
                          ) : (
                            <ArrowDownIcon className="w-4 h-4 text-red-400" />
                          )}
                          <span className="capitalize">
                            {trade.type === "buy" ? "Compra" : "Venda"}
                          </span>
                        </div>
                      </TableCell>
                      <TableCell className="font-mono">{trade.volume !== null ? trade.volume.toFixed(2) : 'N/A'}</TableCell>
                      <TableCell className="font-mono">{trade.openPrice !== null ? trade.openPrice.toFixed(2) : 'N/A'}</TableCell>
                      <TableCell className="font-mono">{/* Exit Price not in adapter */ 'N/A'}</TableCell>
                      <TableCell>
                        {trade.profit !== null ? (
                          <span className={`font-semibold ${
                            trade.profit >= 0 ? 'text-green-400' : 'text-red-400'
                          }`}>
                            US$ {trade.profit.toFixed(2)}
                          </span>
                        ) : (
                          <span className="text-muted-foreground italic">Em andamento</span>
                        )}
                      </TableCell>
                      <TableCell>
                        <Button variant="ghost" size="sm">
                          <MoreHorizontal className="w-4 h-4" />
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>
        </Card>

        {/* Pagination */}
        <div className="flex items-center justify-between mt-6">
          <p className="text-sm text-muted-foreground">
            Mostrando {paginatedTrades.length > 0 ? (currentPage - 1) * ITEMS_PER_PAGE + 1 : 0}-
            {Math.min(currentPage * ITEMS_PER_PAGE, filteredTrades.length)} de {filteredTrades.length} operações
          </p>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
              disabled={currentPage === 1}
            >
              Anterior
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
              disabled={currentPage === totalPages || totalPages === 0}
            >
              Próximo
            </Button>
          </div>
        </div>
      </div>
    </PageLayout>
  );
};

export default TradingHistory;