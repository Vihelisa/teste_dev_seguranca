import { PageLayout } from "@/components/PageLayout";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

const Downloads = () => {
  const mobileApps = [
    {
      name: "Aura Quant Mobile",
      platform: "iOS",
      version: "2.1.3",
      size: "45.2 MB",
      description: "Monitore seus robôs e operações diretamente do seu iPhone",
      features: ["Notificações em tempo real", "Dashboard móvel", "Controle de robôs"],
      icon: "📱",
      downloadUrl: "#"
    },
    {
      name: "Aura Quant Mobile",
      platform: "Android",
      version: "2.1.1",
      size: "38.7 MB",
      description: "Acesse sua conta e monitore trades no Android",
      features: ["Notificações push", "Interface otimizada", "Sincronização automática"],
      icon: "🤖",
      downloadUrl: "#"
    }
  ];

  const tools = [
    {
      name: "Aura Desktop Pro",
      type: "Desktop",
      version: "1.4.2",
      size: "156 MB",
      description: "Aplicativo desktop completo com recursos avançados de análise",
      features: ["Gráficos avançados", "Backtesting", "Multi-monitor", "API completa"],
      icon: "💻",
      platforms: ["Windows", "macOS", "Linux"]
    },
    {
      name: "Plugin MT5",
      type: "Plugin",
      version: "3.2.1",
      size: "12.4 MB",
      description: "Integração completa com MetaTrader 5",
      features: ["Sincronização automática", "Execução de ordens", "Análise de risco"],
      icon: "🔌",
      platforms: ["MT5"]
    },
    {
      name: "API Client SDK",
      type: "SDK",
      version: "2.0.0",
      size: "2.1 MB",
      description: "SDK para desenvolvedores integrarem com nossa API",
      features: ["Python", "JavaScript", "C#", "Documentação completa"],
      icon: "⚙️",
      platforms: ["Multi-linguagem"]
    }
  ];

  const documentation = [
    {
      title: "Guia de Instalação",
      type: "PDF",
      size: "2.3 MB",
      description: "Passo a passo para configurar todos os produtos"
    },
    {
      title: "Manual da API",
      type: "PDF",
      size: "8.7 MB",
      description: "Documentação completa da API REST"
    },
    {
      title: "Estratégias de Trading",
      type: "PDF",
      size: "12.1 MB",
      description: "Guia completo de estratégias automatizadas"
    },
    {
      title: "Guia de Integração",
      type: "PDF",
      size: "4.2 MB",
      description: "Como integrar com corretoras e plataformas"
    }
  ];

  return (
    <PageLayout 
      title="Centro de Downloads" 
      description="Baixe nossos aplicativos, ferramentas e documentação para maximizar sua experiência."
    >
      <div className="container mx-auto px-6 py-12">
        {/* Mobile Apps */}
        <div className="mb-12">
          <h2 className="text-2xl font-bold mb-6">Aplicativos Mobile</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {mobileApps.map((app, index) => (
              <Card key={index} className="p-6 bg-gradient-card border-border/20">
                <div className="flex items-start gap-4">
                  <div className="text-4xl">{app.icon}</div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <h3 className="text-lg font-semibold">{app.name}</h3>
                      <Badge variant="outline">{app.platform}</Badge>
                    </div>
                    <p className="text-sm text-muted-foreground mb-3">{app.description}</p>
                    <div className="flex items-center gap-4 text-xs text-muted-foreground mb-4">
                      <span>v{app.version}</span>
                      <span>{app.size}</span>
                    </div>
                    <ul className="space-y-1 mb-4">
                      {app.features.map((feature, i) => (
                        <li key={i} className="text-sm flex items-center gap-2">
                          <div className="w-1 h-1 bg-primary rounded-full"></div>
                          {feature}
                        </li>
                      ))}
                    </ul>
                    <div className="flex gap-2">
                      <Button size="sm" className="flex-1">
                        {app.platform === 'iOS' ? 'App Store' : 'Google Play'}
                      </Button>
                      <Button variant="outline" size="sm">
                        Download Direto
                      </Button>
                    </div>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        </div>

        {/* Tools and Software */}
        <div className="mb-12">
          <h2 className="text-2xl font-bold mb-6">Ferramentas e Software</h2>
          <div className="space-y-6">
            {tools.map((tool, index) => (
              <Card key={index} className="p-6 bg-gradient-card border-border/20">
                <div className="flex items-start gap-4">
                  <div className="text-4xl">{tool.icon}</div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <h3 className="text-xl font-semibold">{tool.name}</h3>
                      <Badge variant="secondary">{tool.type}</Badge>
                      <Badge variant="outline">v{tool.version}</Badge>
                    </div>
                    <p className="text-muted-foreground mb-3">{tool.description}</p>
                    <div className="flex items-center gap-4 text-sm text-muted-foreground mb-4">
                      <span>Tamanho: {tool.size}</span>
                      <span>Plataformas: {tool.platforms.join(", ")}</span>
                    </div>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-2 mb-4">
                      {tool.features.map((feature, i) => (
                        <div key={i} className="text-sm flex items-center gap-2">
                          <div className="w-1 h-1 bg-primary rounded-full"></div>
                          {feature}
                        </div>
                      ))}
                    </div>
                    <div className="flex gap-2">
                      <Button>Download</Button>
                      <Button variant="outline">Notas da Versão</Button>
                      <Button variant="ghost">Documentação</Button>
                    </div>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        </div>

        {/* Documentation */}
        <div>
          <h2 className="text-2xl font-bold mb-6">Documentação Técnica</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {documentation.map((doc, index) => (
              <Card key={index} className="p-6 bg-gradient-card border-border/20">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center">
                    <svg className="w-6 h-6 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <h3 className="font-semibold">{doc.title}</h3>
                      <Badge variant="outline" className="text-xs">{doc.type}</Badge>
                    </div>
                    <p className="text-sm text-muted-foreground mb-2">{doc.description}</p>
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-muted-foreground">{doc.size}</span>
                      <Button size="sm" variant="outline">
                        Download
                      </Button>
                    </div>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        </div>
      </div>
    </PageLayout>
  );
};

export default Downloads;