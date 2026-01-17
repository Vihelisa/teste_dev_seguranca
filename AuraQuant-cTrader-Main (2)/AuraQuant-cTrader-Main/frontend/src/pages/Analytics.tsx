import { PageLayout } from "@/components/PageLayout";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

const Analytics = () => {
  const performanceMetrics = [
    { name: "Alpha Scalper Pro", roi: 124.7, maxDrawdown: 8.2, sharpeRatio: 2.4, trades: 1247 },
    { name: "Trend Master AI", roi: 98.3, maxDrawdown: 12.1, sharpeRatio: 1.8, trades: 892 },
    { name: "Grid Master 3000", roi: 67.8, maxDrawdown: 5.4, sharpeRatio: 3.1, trades: 2341 },
    { name: "Momentum Hunter", roi: 156.2, maxDrawdown: 15.3, sharpeRatio: 1.6, trades: 567 }
  ];

  const marketReports = [
    {
      title: "Análise Semanal do Mercado",
      date: "15 Jan 2024",
      type: "Relatório Semanal",
      summary: "Mercado apresenta volatilidade crescente com oportunidades em setores defensivos",
      insights: ["Ibovespa: +2.3%", "Dólar: R$ 4.95", "Selic: 11.75%"],
      status: "Novo"
    },
    {
      title: "Performance dos Robôs - Q4 2023",
      date: "10 Jan 2024",
      type: "Relatório Trimestral",
      summary: "Robôs apresentaram performance superior ao benchmark em 89% dos casos",
      insights: ["ROI médio: +18.7%", "Sharpe Ratio: 2.1", "Max Drawdown: 6.8%"],
      status: "Destaque"
    },
    {
      title: "Impacto das Decisões do COPOM",
      date: "08 Jan 2024",
      type: "Análise Especial",
      summary: "Como as mudanças na taxa de juros afetam as estratégias automatizadas",
      insights: ["Setores beneficiados", "Ajustes recomendados", "Cenários 2024"],
      status: "Análise"
    }
  ];

  const alerts = [
    {
      type: "Oportunidade",
      title: "PETR4 - Breakout Técnico",
      description: "Ação rompeu resistência importante com volume alto",
      time: "Há 15 min",
      severity: "high"
    },
    {
      type: "Risco",
      title: "Volatilidade Alta - VALE3",
      description: "Aumento significativo da volatilidade detectado",
      time: "Há 32 min",
      severity: "medium"
    },
    {
      type: "Info",
      title: "Fechamento de Posição",
      description: "Robot Alpha completou ciclo de operações",
      time: "Há 1h",
      severity: "low"
    }
  ];

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'high': return 'border-red-400/20 text-red-400 bg-red-400/10';
      case 'medium': return 'border-yellow-400/20 text-yellow-400 bg-yellow-400/10';
      case 'low': return 'border-blue-400/20 text-blue-400 bg-blue-400/10';
      default: return 'border-gray-400/20 text-gray-400 bg-gray-400/10';
    }
  };

  return (
    <PageLayout 
      title="Centro de Análises" 
      description="Relatórios avançados, análises de mercado e alertas personalizados para otimizar seus investimentos."
    >
      <div className="container mx-auto px-6 py-12">
        <Tabs defaultValue="performance" className="w-full">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="performance">Performance</TabsTrigger>
            <TabsTrigger value="reports">Relatórios</TabsTrigger>
            <TabsTrigger value="alerts">Alertas</TabsTrigger>
            <TabsTrigger value="simulator">Simulador</TabsTrigger>
          </TabsList>
          
          <TabsContent value="performance" className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
              <Card className="p-6 bg-gradient-card border-border/20">
                <h3 className="text-sm font-medium text-muted-foreground mb-2">ROI Médio</h3>
                <div className="text-2xl font-bold text-neon">+18.7%</div>
                <p className="text-xs text-muted-foreground">Últimos 12 meses</p>
              </Card>
              <Card className="p-6 bg-gradient-card border-border/20">
                <h3 className="text-sm font-medium text-muted-foreground mb-2">Sharpe Ratio</h3>
                <div className="text-2xl font-bold">2.47</div>
                <p className="text-xs text-muted-foreground">Risco ajustado</p>
              </Card>
              <Card className="p-6 bg-gradient-card border-border/20">
                <h3 className="text-sm font-medium text-muted-foreground mb-2">Max Drawdown</h3>
                <div className="text-2xl font-bold text-red-400">-8.2%</div>
                <p className="text-xs text-muted-foreground">Menor perda</p>
              </Card>
              <Card className="p-6 bg-gradient-card border-border/20">
                <h3 className="text-sm font-medium text-muted-foreground mb-2">Win Rate</h3>
                <div className="text-2xl font-bold text-yellow-400">67%</div>
                <p className="text-xs text-muted-foreground">Taxa de acerto</p>
              </Card>
            </div>

            <Card className="p-6 bg-gradient-card border-border/20">
              <h3 className="text-xl font-bold mb-4">Performance Detalhada dos Robôs</h3>
              <div className="space-y-4">
                {performanceMetrics.map((robot, index) => (
                  <div key={index} className="p-4 rounded-lg border border-border/20">
                    <div className="flex items-center justify-between mb-3">
                      <h4 className="font-semibold">{robot.name}</h4>
                      <Badge className="bg-green-400/10 text-green-400">
                        ROI: +{robot.roi}%
                      </Badge>
                    </div>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                      <div>
                        <span className="text-muted-foreground">Max Drawdown</span>
                        <div className="font-medium text-red-400">-{robot.maxDrawdown}%</div>
                      </div>
                      <div>
                        <span className="text-muted-foreground">Sharpe Ratio</span>
                        <div className="font-medium">{robot.sharpeRatio}</div>
                      </div>
                      <div>
                        <span className="text-muted-foreground">Trades</span>
                        <div className="font-medium">{robot.trades.toLocaleString()}</div>
                      </div>
                      <div>
                        <span className="text-muted-foreground">Status</span>
                        <div className="font-medium text-green-400">Ativo</div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          </TabsContent>

          <TabsContent value="reports" className="space-y-6">
            <div className="space-y-6">
              {marketReports.map((report, index) => (
                <Card key={index} className="p-6 bg-gradient-card border-border/20">
                  <div className="flex items-start justify-between mb-4">
                    <div>
                      <div className="flex items-center gap-2 mb-2">
                        <h3 className="text-lg font-semibold">{report.title}</h3>
                        <Badge variant="outline">{report.type}</Badge>
                        <Badge 
                          className={
                            report.status === 'Novo' ? 'bg-blue-400/10 text-blue-400' :
                            report.status === 'Destaque' ? 'bg-yellow-400/10 text-yellow-400' :
                            'bg-green-400/10 text-green-400'
                          }
                        >
                          {report.status}
                        </Badge>
                      </div>
                      <p className="text-muted-foreground mb-3">{report.summary}</p>
                      <div className="flex gap-4 text-sm">
                        {report.insights.map((insight, i) => (
                          <span key={i} className="bg-primary/10 text-primary px-2 py-1 rounded">
                            {insight}
                          </span>
                        ))}
                      </div>
                    </div>
                    <div className="text-right text-sm text-muted-foreground">
                      {report.date}
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <Button size="sm">Ler Completo</Button>
                    <Button variant="outline" size="sm">Download PDF</Button>
                  </div>
                </Card>
              ))}
            </div>
          </TabsContent>

          <TabsContent value="alerts" className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
              <Card className="p-6 bg-gradient-card border-border/20">
                <h3 className="text-sm font-medium text-muted-foreground mb-2">Alertas Ativos</h3>
                <div className="text-2xl font-bold">12</div>
                <p className="text-xs text-muted-foreground">Últimas 24h</p>
              </Card>
              <Card className="p-6 bg-gradient-card border-border/20">
                <h3 className="text-sm font-medium text-muted-foreground mb-2">Oportunidades</h3>
                <div className="text-2xl font-bold text-green-400">5</div>
                <p className="text-xs text-muted-foreground">Aguardando ação</p>
              </Card>
              <Card className="p-6 bg-gradient-card border-border/20">
                <h3 className="text-sm font-medium text-muted-foreground mb-2">Riscos</h3>
                <div className="text-2xl font-bold text-red-400">2</div>
                <p className="text-xs text-muted-foreground">Atenção necessária</p>
              </Card>
            </div>

            <div className="space-y-4">
              {alerts.map((alert, index) => (
                <Card key={index} className="p-6 bg-gradient-card border-border/20">
                  <div className="flex items-start justify-between">
                    <div className="flex items-start gap-4">
                      <div className={`w-3 h-3 rounded-full mt-2 ${getSeverityColor(alert.severity).split(' ')[2]}`}></div>
                      <div>
                        <div className="flex items-center gap-2 mb-1">
                          <h3 className="font-semibold">{alert.title}</h3>
                          <Badge className={getSeverityColor(alert.severity)} variant="outline">
                            {alert.type}
                          </Badge>
                        </div>
                        <p className="text-muted-foreground">{alert.description}</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-sm text-muted-foreground">{alert.time}</div>
                      <Button size="sm" variant="outline" className="mt-2">
                        Detalhes
                      </Button>
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          </TabsContent>

          <TabsContent value="simulator" className="space-y-6">
            <Card className="p-8 bg-gradient-card border-border/20 text-center">
              <div className="max-w-2xl mx-auto">
                <h3 className="text-2xl font-bold mb-4">Simulador de Estratégias</h3>
                <p className="text-lg text-muted-foreground mb-6">
                  Teste diferentes configurações de robôs e compare performance 
                  sem riscos reais utilizando dados históricos.
                </p>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                  <div className="p-4 rounded-lg border border-border/20">
                    <h4 className="font-semibold mb-2">Análise de Risco</h4>
                    <p className="text-sm text-muted-foreground">
                      Calcule drawdown máximo e volatilidade
                    </p>
                  </div>
                  <div className="p-4 rounded-lg border border-border/20">
                    <h4 className="font-semibold mb-2">Otimização</h4>
                    <p className="text-sm text-muted-foreground">
                      Encontre os melhores parâmetros automaticamente
                    </p>
                  </div>
                  <div className="p-4 rounded-lg border border-border/20">
                    <h4 className="font-semibold mb-2">Comparação</h4>
                    <p className="text-sm text-muted-foreground">
                      Compare múltiplas estratégias lado a lado
                    </p>
                  </div>
                </div>
                <Button size="lg" className="mr-4">
                  Iniciar Simulação
                </Button>
                <Button variant="outline" size="lg">
                  Ver Tutoriais
                </Button>
              </div>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </PageLayout>
  );
};

export default Analytics;