import { PageLayout } from "@/components/PageLayout";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

const Partners = () => {
  const brokers = [
    {
      name: "FP Markets",
      type: "Corretora",
      status: "Integração Completa",
      features: ["Spreads from 0.0 pips", "ECN Execution", "MetaTrader 5", "ASIC Regulated"],
      logo: "🏛️",
      description: "Leading global forex and CFD broker with institutional-grade execution"
    }
  ];

  const dataProviders = [
    {
      name: "Bloomberg Terminal",
      type: "Dados Financeiros",
      status: "Parceiro Premium",
      features: ["Dados Globais", "Análise Fundamental", "News Feed"],
      logo: "📊",
      description: "Líder mundial em dados financeiros"
    },
    {
      name: "Refinitiv Eikon",
      type: "Dados Financeiros", 
      status: "Parceiro Premium",
      features: ["Real-time Data", "Analytics", "Research"],
      logo: "📡",
      description: "Plataforma completa de dados e analytics"
    },
    {
      name: "Yahoo Finance API",
      type: "Dados Gratuitos",
      status: "Integração Ativa",
      features: ["Cotações", "Histórico", "Indicadores"],
      logo: "🌐",
      description: "Dados financeiros acessíveis e confiáveis"
    }
  ];

  const certifications = [
    {
      title: "CVM - Comissão de Valores Mobiliários",
      type: "Regulamentação",
      status: "Certificado",
      description: "Autorização para operar no mercado brasileiro",
      icon: "🏛️"
    },
    {
      title: "ANBIMA",
      type: "Certificação",
      status: "Membro",
      description: "Associação Brasileira das Entidades dos Mercados Financeiro",
      icon: "🎖️"
    },
    {
      title: "ISO 27001",
      type: "Segurança",
      status: "Certificado",
      description: "Padrão internacional de segurança da informação",
      icon: "🔒"
    },
    {
      title: "SOC 2 Type II",
      type: "Auditoria",
      status: "Auditado",
      description: "Controles de segurança e disponibilidade auditados",
      icon: "🛡️"
    }
  ];

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'Integração Completa':
      case 'Parceiro Premium':
      case 'Certificado':
      case 'Membro':
      case 'Auditado':
        return 'bg-green-400/10 text-green-400 border-green-400/20';
      case 'Em Desenvolvimento':
        return 'bg-yellow-400/10 text-yellow-400 border-yellow-400/20';
      case 'Integração Ativa':
        return 'bg-blue-400/10 text-blue-400 border-blue-400/20';
      default:
        return 'bg-gray-400/10 text-gray-400 border-gray-400/20';
    }
  };

  return (
    <PageLayout 
      title="Parcerias e Integrações" 
      description="Conheça nossos parceiros estratégicos, integrações disponíveis e certificações de segurança."
    >
      <div className="container mx-auto px-6 py-12">
        {/* Corretoras */}
        <div className="mb-12">
          <div className="text-center mb-8">
            <h2 className="text-3xl font-bold mb-4">Corretoras Integradas</h2>
            <p className="text-lg text-muted-foreground">
              Conecte-se diretamente com as principais corretoras do mercado
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {brokers.map((broker, index) => (
              <Card key={index} className="p-6 bg-gradient-card border-border/20">
                <div className="flex items-start gap-4">
                  <div className="text-4xl">{broker.logo}</div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <h3 className="text-lg font-semibold">{broker.name}</h3>
                      <Badge variant="outline">{broker.type}</Badge>
                    </div>
                    <Badge className={getStatusColor(broker.status)} variant="outline">
                      {broker.status}
                    </Badge>
                    <p className="text-sm text-muted-foreground mt-2 mb-3">{broker.description}</p>
                    <ul className="space-y-1">
                      {broker.features.map((feature, i) => (
                        <li key={i} className="text-sm flex items-center gap-2">
                          <div className="w-1 h-1 bg-primary rounded-full"></div>
                          {feature}
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        </div>

        {/* Provedores de Dados */}
        <div className="mb-12">
          <div className="text-center mb-8">
            <h2 className="text-3xl font-bold mb-4">Provedores de Dados</h2>
            <p className="text-lg text-muted-foreground">
              Dados de mercado em tempo real das fontes mais confiáveis
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {dataProviders.map((provider, index) => (
              <Card key={index} className="p-6 bg-gradient-card border-border/20">
                <div className="text-center">
                  <div className="text-4xl mb-3">{provider.logo}</div>
                  <h3 className="text-lg font-semibold mb-2">{provider.name}</h3>
                  <Badge className={getStatusColor(provider.status)} variant="outline">
                    {provider.status}
                  </Badge>
                  <p className="text-sm text-muted-foreground mt-2 mb-3">{provider.description}</p>
                  <ul className="space-y-1 text-sm">
                    {provider.features.map((feature, i) => (
                      <li key={i} className="flex items-center justify-center gap-2">
                        <div className="w-1 h-1 bg-primary rounded-full"></div>
                        {feature}
                      </li>
                    ))}
                  </ul>
                </div>
              </Card>
            ))}
          </div>
        </div>


        {/* Torne-se um Parceiro */}
        <Card className="p-8 bg-gradient-card border-border/20 text-center">
          <h2 className="text-2xl font-bold mb-4">Torne-se um Parceiro</h2>
          <p className="text-lg text-muted-foreground mb-6 max-w-2xl mx-auto">
            Junte-se ao nosso ecossistema de parceiros e ofereça soluções de trading automatizado 
            aos seus clientes com nossa tecnologia de ponta.
          </p>
          <div className="flex gap-4 justify-center">
            <Button size="lg">
              Seja um Parceiro
            </Button>
            <Button variant="outline" size="lg">
              Programa de Afiliados
            </Button>
          </div>
        </Card>
      </div>
    </PageLayout>
  );
};

export default Partners;