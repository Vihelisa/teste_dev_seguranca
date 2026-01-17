export const StatsSection = () => {
  const stats = [
    {
      number: "500+",
      label: "Robôs Ativos",
      description: "Algoritmos verificados e testados"
    },
    {
      number: "10K+",
      label: "Usuários",
      description: "Traders em todo o Brasil"
    },
    {
      number: "+127%",
      label: "Performance",
      description: "Rentabilidade média anual"
    },
    {
      number: "99.9%",
      label: "Uptime",
      description: "Disponibilidade garantida"
    }
  ];

  return (
    <section className="py-16 bg-gradient-to-r from-background via-muted/5 to-background">
      <div className="container mx-auto px-6">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
          {stats.map((stat, index) => (
            <div key={index} className="text-center">
              <div className="text-3xl md:text-4xl font-bold text-primary mb-2">
                {stat.number}
              </div>
              <div className="text-lg font-semibold mb-1">
                {stat.label}
              </div>
              <div className="text-sm text-muted-foreground">
                {stat.description}
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};