import aiAutomationImage from "@/assets/ai-automation.jpg";
import marketDataImage from "@/assets/market-data.jpg";
import tradingAutomationImage from "@/assets/trading-automation.jpg";

export const FeaturesSection = () => {
  const features = [
    {
      icon: (
        <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
        </svg>
      ),
      title: "IA Avançada",
      description: "Algoritmos de última geração com aprendizado contínuo"
    },
    {
      icon: (
        <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
        </svg>
      ),
      title: "100% Seguro",
      description: "Robôs verificados e auditados por especialistas"
    },
    {
      icon: (
        <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
        </svg>
      ),
      title: "Execução Rápida",
      description: "Latência ultra-baixa para máxima eficiência"
    },
    {
      icon: (
        <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
        </svg>
      ),
      title: "Análise Completa",
      description: "Relatórios detalhados e métricas em tempo real"
    }
  ];

  return (
    <section className="py-24">
      <div className="container mx-auto px-6">
        {/* Section Header */}
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold mb-4">
            <span className="text-matrix">TECNOLOGIA</span> QUANTITATIVA
            <br />
            <span className="text-gradient">DE ÚLTIMA GERAÇÃO</span>
          </h2>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            Arquitetura avançada desenvolvida por <span className="text-neon-cyan">quants especialistas</span> e engenheiros de IA
          </p>
        </div>

        {/* Features Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
          {features.map((feature, index) => (
            <div 
              key={index}
              className="text-center p-8 rounded-xl bg-card/50 backdrop-blur-sm border-glow hover:glow-neon transition-all duration-300 hover:scale-105 group"
            >
              <div className="w-16 h-16 mx-auto mb-6 rounded-xl bg-primary/20 flex items-center justify-center text-primary group-hover:glow-neon transition-all duration-300">
                {feature.icon}
              </div>
              <h3 className="text-xl font-bold mb-3 text-neon-cyan">{feature.title}</h3>
              <p className="text-muted-foreground leading-relaxed">
                {feature.description}
              </p>
            </div>
          ))}
        </div>

        {/* Visual Features with Images */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mt-16">
          <div className="relative group overflow-hidden rounded-2xl">
            <img 
              src={aiAutomationImage} 
              alt="IA e Automação em Trading"
              className="w-full h-64 object-cover transition-transform duration-300 group-hover:scale-110"
            />
            <div className="absolute inset-0 bg-gradient-to-t from-background/95 via-background/30 to-transparent" />
            <div className="absolute bottom-6 left-6 right-6">
              <h3 className="text-xl font-bold mb-2 text-electric-green">IA NEURAL</h3>
              <p className="text-sm text-muted-foreground">Redes neurais avançadas com aprendizado contínuo de mercado</p>
            </div>
          </div>

          <div className="relative group overflow-hidden rounded-2xl">
            <img 
              src={marketDataImage} 
              alt="Análise de Dados do Mercado"
              className="w-full h-64 object-cover transition-transform duration-300 group-hover:scale-110"
            />
            <div className="absolute inset-0 bg-gradient-to-t from-background/95 via-background/30 to-transparent" />
            <div className="absolute bottom-6 left-6 right-6">
              <h3 className="text-xl font-bold mb-2 text-neon-purple">BIG DATA ANALYTICS</h3>
              <p className="text-sm text-muted-foreground">Processamento quântico de terabytes de dados em microssegundos</p>
            </div>
          </div>

          <div className="relative group overflow-hidden rounded-2xl">
            <img 
              src={tradingAutomationImage} 
              alt="Automação de Trading"
              className="w-full h-64 object-cover transition-transform duration-300 group-hover:scale-110"
            />
            <div className="absolute inset-0 bg-gradient-to-t from-background/95 via-background/30 to-transparent" />
            <div className="absolute bottom-6 left-6 right-6">
              <h3 className="text-xl font-bold mb-2 text-neon-cyan">QUANTUM EXECUTION</h3>
              <p className="text-sm text-muted-foreground">Execução autônoma 24/7 com latência sub-milissegundo</p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};