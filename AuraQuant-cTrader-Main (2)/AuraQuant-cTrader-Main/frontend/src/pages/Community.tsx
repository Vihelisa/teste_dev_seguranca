import { PageLayout } from "@/components/PageLayout";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarImage, AvatarFallback } from "@/components/ui/avatar";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

const Community = () => {
  const forumPosts = [
    {
      id: 1,
      title: "Estratégia de Grid Trading em mercados laterais",
      author: "TradingPro",
      authorLevel: "Especialista",
      replies: 23,
      likes: 45,
      category: "Estratégias",
      timeAgo: "2 horas atrás",
      preview: "Compartilho minha experiência com grid trading em PETR4 durante os últimos 3 meses..."
    },
    {
      id: 2,
      title: "Como configurar stop loss inteligente?",
      author: "NovatoTrader",
      authorLevel: "Iniciante",
      replies: 12,
      likes: 18,
      category: "Dúvidas",
      timeAgo: "4 horas atrás",
      preview: "Tenho dificuldade em configurar stops que não sejam acionados por volatilidade normal..."
    },
    {
      id: 3,
      title: "Robô Alpha Scalper - Resultados Janeiro 2024",
      author: "DataAnalyst",
      authorLevel: "Pro",
      replies: 34,
      likes: 67,
      category: "Resultados",
      timeAgo: "1 dia atrás",
      preview: "Fechei janeiro com +12.4% usando o Alpha Scalper. Aqui estão os detalhes..."
    }
  ];

  const topTraders = [
    {
      rank: 1,
      name: "QuantMaster",
      roi: "+187.3%",
      followers: 2847,
      strategies: 12,
      level: "Legend",
      avatar: "/avatars/trader1.jpg"
    },
    {
      rank: 2,
      name: "AlgoWizard",
      roi: "+156.8%",
      followers: 1923,
      strategies: 8,
      level: "Expert",
      avatar: "/avatars/trader2.jpg"
    },
    {
      rank: 3,
      name: "TrendHunter",
      roi: "+142.1%",
      followers: 1456,
      strategies: 15,
      level: "Expert",
      avatar: "/avatars/trader3.jpg"
    },
    {
      rank: 4,
      name: "GridMaster",
      roi: "+128.9%",
      followers: 1234,
      strategies: 6,
      level: "Pro",
      avatar: "/avatars/trader4.jpg"
    }
  ];

  const sharedStrategies = [
    {
      name: "Scalping Inteligente",
      author: "QuantMaster",
      rating: 4.8,
      downloads: 1247,
      roi: "+23.4%",
      description: "Estratégia de scalping com filtros adaptativos para redução de ruído",
      tags: ["Scalping", "Intraday", "Baixo Risco"]
    },
    {
      name: "Momentum Breakout",
      author: "TrendHunter", 
      rating: 4.6,
      downloads: 892,
      roi: "+18.7%",
      description: "Captura breakouts com confirmação de volume e momentum",
      tags: ["Breakout", "Swing", "Médio Risco"]
    },
    {
      name: "Grid Adaptativo",
      author: "GridMaster",
      rating: 4.9,
      downloads: 2145,
      roi: "+15.2%",
      description: "Grid trading com ajuste automático baseado em volatilidade",
      tags: ["Grid", "Lateral", "Conservador"]
    }
  ];

  const getLevelColor = (level: string) => {
    switch (level) {
      case 'Legend': return 'bg-purple-400/10 text-purple-400 border-purple-400/20';
      case 'Expert': return 'bg-yellow-400/10 text-yellow-400 border-yellow-400/20';
      case 'Pro': return 'bg-blue-400/10 text-blue-400 border-blue-400/20';
      case 'Especialista': return 'bg-green-400/10 text-green-400 border-green-400/20';
      default: return 'bg-gray-400/10 text-gray-400 border-gray-400/20';
    }
  };

  return (
    <PageLayout 
      title="Comunidade" 
      description="Conecte-se com traders, compartilhe estratégias e aprenda com os melhores da comunidade."
    >
      <div className="container mx-auto px-6 py-12">
        <Tabs defaultValue="forum" className="w-full">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="forum">Fórum</TabsTrigger>
            <TabsTrigger value="ranking">Ranking</TabsTrigger>
            <TabsTrigger value="strategies">Estratégias</TabsTrigger>
          </TabsList>
          
          <TabsContent value="forum" className="space-y-6">
            <div className="flex justify-between items-center">
              <h2 className="text-2xl font-bold">Discussões Recentes</h2>
              <Button>Nova Discussão</Button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
              <Card className="p-4 bg-gradient-card border-border/20">
                <h3 className="text-sm font-medium text-muted-foreground mb-1">Total de Posts</h3>
                <div className="text-2xl font-bold">12,847</div>
              </Card>
              <Card className="p-4 bg-gradient-card border-border/20">
                <h3 className="text-sm font-medium text-muted-foreground mb-1">Membros Ativos</h3>
                <div className="text-2xl font-bold">3,241</div>
              </Card>
              <Card className="p-4 bg-gradient-card border-border/20">
                <h3 className="text-sm font-medium text-muted-foreground mb-1">Discussões Hoje</h3>
                <div className="text-2xl font-bold">156</div>
              </Card>
              <Card className="p-4 bg-gradient-card border-border/20">
                <h3 className="text-sm font-medium text-muted-foreground mb-1">Online Agora</h3>
                <div className="text-2xl font-bold text-green-400">487</div>
              </Card>
            </div>
            
            <div className="space-y-4">
              {forumPosts.map((post) => (
                <Card key={post.id} className="p-6 bg-gradient-card border-border/20">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <Badge variant="outline">{post.category}</Badge>
                        <h3 className="text-lg font-semibold hover:text-primary cursor-pointer">
                          {post.title}
                        </h3>
                      </div>
                      <p className="text-muted-foreground mb-3">{post.preview}</p>
                      <div className="flex items-center gap-4 text-sm text-muted-foreground">
                        <div className="flex items-center gap-1">
                          <Avatar className="w-6 h-6">
                            <AvatarFallback className="text-xs">
                              {post.author.slice(0, 2)}
                            </AvatarFallback>
                          </Avatar>
                          <span>{post.author}</span>
                          <Badge className={getLevelColor(post.authorLevel)} variant="outline">
                            {post.authorLevel}
                          </Badge>
                        </div>
                        <span>{post.timeAgo}</span>
                      </div>
                    </div>
                    <div className="flex items-center gap-4 text-sm text-muted-foreground">
                      <div className="text-center">
                        <div className="font-medium">{post.replies}</div>
                        <div>respostas</div>
                      </div>
                      <div className="text-center">
                        <div className="font-medium text-red-400">{post.likes}</div>
                        <div>likes</div>
                      </div>
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          </TabsContent>

          <TabsContent value="ranking" className="space-y-6">
            <h2 className="text-2xl font-bold mb-6">Ranking de Traders</h2>
            
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              <div>
                <h3 className="text-xl font-semibold mb-4">Top Performers</h3>
                <div className="space-y-4">
                  {topTraders.map((trader) => (
                    <Card key={trader.rank} className="p-6 bg-gradient-card border-border/20">
                      <div className="flex items-center gap-4">
                        <div className="text-2xl font-bold text-primary">#{trader.rank}</div>
                        <Avatar className="w-12 h-12">
                          <AvatarFallback>{trader.name.slice(0, 2)}</AvatarFallback>
                        </Avatar>
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <h4 className="font-semibold">{trader.name}</h4>
                            <Badge className={getLevelColor(trader.level)} variant="outline">
                              {trader.level}
                            </Badge>
                          </div>
                          <div className="flex gap-4 text-sm text-muted-foreground">
                            <span>ROI: <span className="text-neon font-medium">{trader.roi}</span></span>
                            <span>{trader.followers} seguidores</span>
                            <span>{trader.strategies} estratégias</span>
                          </div>
                        </div>
                        <Button variant="outline" size="sm">Seguir</Button>
                      </div>
                    </Card>
                  ))}
                </div>
              </div>
              
              <div>
                <h3 className="text-xl font-semibold mb-4">Suas Estatísticas</h3>
                <Card className="p-6 bg-gradient-card border-border/20">
                  <div className="text-center mb-6">
                    <Avatar className="w-20 h-20 mx-auto mb-3">
                      <AvatarFallback className="text-xl">EU</AvatarFallback>
                    </Avatar>
                    <h3 className="text-xl font-semibold">Seu Username</h3>
                    <Badge className={getLevelColor('Iniciante')} variant="outline">
                      Iniciante
                    </Badge>
                  </div>
                  <div className="grid grid-cols-2 gap-4 mb-6">
                    <div className="text-center">
                      <div className="text-2xl font-bold text-neon">+8.7%</div>
                      <div className="text-sm text-muted-foreground">ROI Total</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold">#247</div>
                      <div className="text-sm text-muted-foreground">Ranking</div>
                    </div>
                  </div>
                  <Button className="w-full">Ver Perfil Completo</Button>
                </Card>
              </div>
            </div>
          </TabsContent>

          <TabsContent value="strategies" className="space-y-6">
            <div className="flex justify-between items-center">
              <h2 className="text-2xl font-bold">Estratégias Compartilhadas</h2>
              <Button>Compartilhar Estratégia</Button>
            </div>

            <div className="space-y-6">
              {sharedStrategies.map((strategy, index) => (
                <Card key={index} className="p-6 bg-gradient-card border-border/20">
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <h3 className="text-xl font-semibold">{strategy.name}</h3>
                        <div className="flex items-center gap-1">
                          {Array.from({ length: 5 }, (_, i) => (
                            <span key={i} className={`text-sm ${i < Math.floor(strategy.rating) ? 'text-yellow-400' : 'text-gray-400'}`}>
                              ★
                            </span>
                          ))}
                          <span className="text-sm text-muted-foreground ml-1">({strategy.rating})</span>
                        </div>
                      </div>
                      <div className="flex items-center gap-2 mb-3">
                        <span className="text-sm text-muted-foreground">por</span>
                        <span className="font-medium">{strategy.author}</span>
                        <Badge className="bg-green-400/10 text-green-400">
                          ROI: {strategy.roi}
                        </Badge>
                      </div>
                      <p className="text-muted-foreground mb-3">{strategy.description}</p>
                      <div className="flex gap-2">
                        {strategy.tags.map((tag, i) => (
                          <Badge key={i} variant="outline">{tag}</Badge>
                        ))}
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-sm text-muted-foreground mb-2">
                        {strategy.downloads.toLocaleString()} downloads
                      </div>
                      <Button size="sm">Baixar</Button>
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </PageLayout>
  );
};

export default Community;