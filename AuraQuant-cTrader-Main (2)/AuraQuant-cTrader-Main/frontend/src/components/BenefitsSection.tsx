export const BenefitsSection = () => {
  const benefits = [
    "Robôs gratuitos para todos os usuários",
    "Controle total - inicie e pare quando quiser",
    "Suporte 24/7 especializado",
    "Atualizações automáticas dos algoritmos",
    "Interface intuitiva e fácil de usar",
    "Compatível com principais corretoras"
  ];

  return (
    <section className="py-24 bg-gradient-to-b from-background to-muted/10">
      <div className="container mx-auto px-6">
        <div className="max-w-4xl mx-auto">
          {/* Section Header */}
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold mb-4">
              Vantagens exclusivas
            </h2>
            <p className="text-lg text-muted-foreground">
              Tudo que você precisa para ter sucesso no trading automatizado
            </p>
          </div>

          {/* Benefits Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {benefits.map((benefit, index) => (
              <div 
                key={index}
                className="flex items-center p-6 rounded-xl bg-card border border-border/50 hover:border-primary/20 transition-all duration-300 hover:scale-[1.02] group"
              >
                <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center mr-4 group-hover:bg-primary/20 transition-colors">
                  <svg className="w-5 h-5 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                </div>
                <p className="font-medium">{benefit}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
};