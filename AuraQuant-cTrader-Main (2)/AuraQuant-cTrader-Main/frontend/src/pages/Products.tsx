import { PageLayout } from "@/components/PageLayout";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

const Products = () => {
  const products = [
    {
      name: "Aura Quant Pro",
      description: "Plataforma completa de trading automatizado com IA avançada",
      features: [
        "Interface intuitiva e responsiva",
        "Mais de 500 robôs verificados",
        "Dashboard em tempo real",
        "Análise de risco automatizada",
        "Backtesting histórico",
        "Integração com 15+ corretoras"
      ],
      image: "/api/placeholder/600/400",
      category: "Plataforma Principal"
    },
    {
      name: "Aura Mobile",
      description: "Monitore e controle seus robôs direto do seu smartphone",
      features: [
        "App nativo iOS e Android",
        "Notificações push em tempo real",
        "Controle total dos robôs",
        "Gráficos interativos",
        "Touch ID / Face ID",
        "Modo offline para consultas"
      ],
      image: "/api/placeholder/600/400",
      category: "Mobile"
    },
    {
      name: "Aura API",
      description: "Desenvolva suas próprias soluções com nossa API robusta",
      features: [
        "REST API completa",
        "WebSocket para dados em tempo real",
        "SDKs em Python, JavaScript, Java",
        "Rate limiting inteligente",
        "Documentação interativa",
        "Sandbox para testes"
      ],
      image: "/api/placeholder/600/400",
      category: "Developers"
    }
  ];

  const integrations = [
    { name: "XP Investimentos", logo: "XP", status: "Ativo" },
    { name: "Clear Corretora", logo: "Clear", status: "Ativo" },
    { name: "Rico Investimentos", logo: "Rico", status: "Ativo" },
    { name: "BTG Pactual", logo: "BTG", status: "Ativo" },
    { name: "Inter Investimentos", logo: "Inter", status: "Ativo" },
    { name: "Nu Invest", logo: "Nu", status: "Ativo" },
    { name: "Toro Investimentos", logo: "Toro", status: "Ativo" },
    { name: "Ativa Investimentos", logo: "Ativa", status: "Ativo" },
  ];

  return (
    <PageLayout 
      title="Nossos Produtos"
      description="Conheça nossa suíte completa de soluções para trading automatizado, desde a plataforma web até APIs para desenvolvedores."
    >
      <div className="container mx-auto px-6 py-12">
        <Tabs defaultValue="overview" className="mb-16">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="overview">Visão Geral</TabsTrigger>
            <TabsTrigger value="features">Recursos</TabsTrigger>
            <TabsTrigger value="integrations">Integrações</TabsTrigger>
            <TabsTrigger value="api">API</TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="mt-8">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-12">
              {products.map((product, index) => (
                <Card key={index} className="p-8 bg-gradient-card border-border/20 hover:border-primary/20 transition-all duration-300">
                  <Badge className="mb-4 bg-primary/10 text-primary border-primary/20">
                    {product.category}
                  </Badge>
                  
                  <h3 className="text-2xl font-bold mb-4">{product.name}</h3>
                  <p className="text-muted-foreground mb-6">{product.description}</p>
                  
                  {(product.name === 'Aura Mobile' || product.name === 'Aura API') && (
                    <div className="mb-6">
                      <Badge variant="outline" className="border-yellow-400/20 text-yellow-400">
                        Em Breve
                      </Badge>
                    </div>
                  )}

                  <ul className="space-y-2 mb-8">
                    {product.features.map((feature, featureIndex) => (
                      <li key={featureIndex} className="flex items-center gap-2">
                        <svg className="w-4 h-4 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                        <span className="text-sm">{feature}</span>
                      </li>
                    ))}
                  </ul>
                  
                  <div className="flex gap-3">
              <Button asChild className="bg-gradient-primary">
                <a href="/register">Testar Grátis</a>
              </Button>
                    <Button variant="outline">
                      Saiba Mais
                    </Button>
                  </div>
                </Card>
              ))}
            </div>
          </TabsContent>

          <TabsContent value="features" className="mt-8">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
              <Card className="p-6 bg-gradient-card border-border/20 text-center">
                <div className="w-12 h-12 bg-primary/10 rounded-xl flex items-center justify-center mx-auto mb-4">
                  <svg className="w-6 h-6 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                  </svg>
                </div>
                <h3 className="font-semibold mb-2">Inteligência Artificial</h3>
                <p className="text-muted-foreground text-sm">Algoritmos de machine learning que se adaptam às condições do mercado</p>
              </Card>

              <Card className="p-6 bg-gradient-card border-border/20 text-center">
                <div className="w-12 h-12 bg-primary/10 rounded-xl flex items-center justify-center mx-auto mb-4">
                  <svg className="w-6 h-6 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                </div>
                <h3 className="font-semibold mb-2">Execução Ultra-Rápida</h3>
                <p className="text-muted-foreground text-sm">Latência menor que 1ms para não perder oportunidades</p>
              </Card>

              <Card className="p-6 bg-gradient-card border-border/20 text-center">
                <div className="w-12 h-12 bg-primary/10 rounded-xl flex items-center justify-center mx-auto mb-4">
                  <svg className="w-6 h-6 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                  </svg>
                </div>
                <h3 className="font-semibold mb-2">Segurança Máxima</h3>
                <p className="text-muted-foreground text-sm">Criptografia de nível bancário e auditoria contínua</p>
              </Card>

              <Card className="p-6 bg-gradient-card border-border/20 text-center">
                <div className="w-12 h-12 bg-primary/10 rounded-xl flex items-center justify-center mx-auto mb-4">
                  <svg className="w-6 h-6 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                </div>
                <h3 className="font-semibold mb-2">Análise Avançada</h3>
                <p className="text-muted-foreground text-sm">Mais de 200 indicadores técnicos e fundamentalistas</p>
              </Card>

              <Card className="p-6 bg-gradient-card border-border/20 text-center">
                <div className="w-12 h-12 bg-primary/10 rounded-xl flex items-center justify-center mx-auto mb-4">
                  <svg className="w-6 h-6 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 18h.01M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z" />
                  </svg>
                </div>
                <h3 className="font-semibold mb-2">Multiplataforma</h3>
                <p className="text-muted-foreground text-sm">Web, mobile e desktop em perfeita sincronização</p>
              </Card>

              <Card className="p-6 bg-gradient-card border-border/20 text-center">
                <div className="w-12 h-12 bg-primary/10 rounded-xl flex items-center justify-center mx-auto mb-4">
                  <svg className="w-6 h-6 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 4V2a1 1 0 011-1h8a1 1 0 011 1v2m-9 4v10a2 2 0 002 2h6a2 2 0 002-2V8M7 8h10" />
                  </svg>
                </div>
                <h3 className="font-semibold mb-2">Backtesting</h3>
                <p className="text-muted-foreground text-sm">Teste estratégias com 10 anos de dados históricos</p>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="integrations" className="mt-8">
            <div className="mb-8">
              <h2 className="text-2xl font-bold mb-4">Corretoras Integradas</h2>
              <p className="text-muted-foreground mb-8">
                Conecte-se facilmente com as principais corretoras do Brasil. Todas as integrações são seguras e auditadas.
              </p>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mb-12">
              {integrations.map((integration, index) => (
                <Card key={index} className="p-6 bg-gradient-card border-border/20 text-center hover:border-primary/20 transition-all duration-300">
                  <div className="w-16 h-16 bg-primary/10 rounded-xl flex items-center justify-center mx-auto mb-4">
                    <span className="font-bold text-primary">{integration.logo}</span>
                  </div>
                  <h3 className="font-medium text-sm mb-2">{integration.name}</h3>
                  <Badge 
                    variant="secondary" 
                    className="text-xs bg-primary/10 text-primary border-primary/20"
                  >
                    {integration.status}
                  </Badge>
                </Card>
              ))}
            </div>

            <Card className="p-8 bg-gradient-card border-border/20">
              <h3 className="text-xl font-bold mb-4">Sua corretora não está listada?</h3>
              <p className="text-muted-foreground mb-6">
                Trabalhamos constantemente para adicionar novas integrações. Entre em contato e faremos o possível para incluir sua corretora preferida.
              </p>
              <Button className="bg-gradient-primary">
                Solicitar Integração
              </Button>
            </Card>
          </TabsContent>

          <TabsContent value="api" className="mt-8">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-12">
              <div>
                <h2 className="text-2xl font-bold mb-6">Aura Quant API</h2>
                <p className="text-muted-foreground mb-8">
                  Desenvolva soluções personalizadas com nossa API REST e WebSocket. 
                  Acesse dados em tempo real, gerencie robôs e crie suas próprias interfaces.
                </p>

                <div className="space-y-6">
                  <div>
                    <h3 className="font-semibold mb-2">Endpoints Principais</h3>
                    <ul className="space-y-2 text-sm text-muted-foreground">
                      <li>• GET /api/v1/robots - Listar robôs</li>
                      <li>• POST /api/v1/robots/&#123;id&#125;/start - Iniciar robô</li>
                      <li>• GET /api/v1/portfolio - Portfolio atual</li>
                      <li>• GET /api/v1/trades - Histórico de trades</li>
                      <li>• WebSocket /ws/real-time - Dados em tempo real</li>
                    </ul>
                  </div>

                  <div>
                    <h3 className="font-semibold mb-2">Rate Limits</h3>
                    <ul className="space-y-2 text-sm text-muted-foreground">
                      <li>• Starter: 1,000 req/hora</li>
                      <li>• Professional: 10,000 req/hora</li>
                      <li>• Enterprise: Ilimitado</li>
                    </ul>
                  </div>
                </div>
              </div>

              <Card className="p-6 bg-muted/5 border-border/20">
                <h3 className="font-semibold mb-4">Exemplo de Código</h3>
                <pre className="text-sm overflow-x-auto">
                  <code>{`import AuraQuantAPI from 'aura-quant-sdk';

const client = new AuraQuantAPI({
  apiKey: 'your-api-key',
  environment: 'production'
});

// Listar robôs ativos
const robots = await client.robots.list({
  status: 'active'
});

// Iniciar um robô
await client.robots.start('robot-id', {
  balance: 10000,
  risk_level: 'medium'
});

// Escutar updates em tempo real
client.websocket.on('trade', (trade) => {
  console.log('Nova operação:', trade);
});`}</code>
                </pre>
              </Card>
            </div>

            <div className="mt-12">
              <Card className="p-8 bg-gradient-card border-border/20">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div className="text-center">
                    <h3 className="font-semibold mb-2">Documentação</h3>
                    <p className="text-sm text-muted-foreground mb-4">
                      Guias completos e exemplos práticos
                    </p>
                    <Button variant="outline" size="sm">
                      Ver Docs
                    </Button>
                  </div>
                  
                  <div className="text-center">
                    <h3 className="font-semibold mb-2">SDKs</h3>
                    <p className="text-sm text-muted-foreground mb-4">
                      Python, JavaScript, Java e mais
                    </p>
                    <Button variant="outline" size="sm">
                      Download
                    </Button>
                  </div>
                  
                  <div className="text-center">
                    <h3 className="font-semibold mb-2">Sandbox</h3>
                    <p className="text-sm text-muted-foreground mb-4">
                      Teste suas integrações sem risco
                    </p>
                    <Button variant="outline" size="sm">
                      Acessar
                    </Button>
                  </div>
                </div>
              </Card>
            </div>
          </TabsContent>
        </Tabs>

        {/* CTA Section */}
        <div className="text-center">
          <h2 className="text-3xl font-bold mb-4">Pronto para começar?</h2>
          <p className="text-lg text-muted-foreground mb-8 max-w-2xl mx-auto">
            Teste nossa plataforma gratuitamente por 30 dias e veja como a automação pode transformar seus investimentos.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button size="lg" className="bg-gradient-primary hover:scale-105 transition-all duration-300 glow-neon">
              Começar Teste Gratuito
            </Button>
            <Button variant="outline" size="lg">
              Agendar Demonstração
            </Button>
          </div>
        </div>
      </div>
    </PageLayout>
  );
};

export default Products;