import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import heroImage from "@/assets/hero-trading.jpg";

export const HeroSection = () => {
  return (
    <section className="relative min-h-screen flex items-center justify-center overflow-hidden">
      {/* Background Image */}
      <div 
        className="absolute inset-0 bg-cover bg-center bg-no-repeat opacity-40"
        style={{ backgroundImage: `url(${heroImage})` }}
      />
      
      {/* Gradient Overlay */}
      <div className="absolute inset-0 bg-gradient-to-b from-background/50 via-background/70 to-background" />
      
      {/* Content */}
      <div className="relative z-10 container mx-auto px-6 py-32 text-center">
        {/* Beta Badge */}
        <Badge className="mb-8 bg-primary/10 text-primary border-primary/20 hover:bg-primary/20 transition-all duration-300">
          🚀 Plataforma em Beta - Acesso Gratuito
        </Badge>

        {/* Main Headline */}
        <h1 className="text-4xl md:text-6xl lg:text-7xl font-bold mb-6 leading-tight">
          Trading Automatizado
          <br />
          <span className="text-gradient">com IA Avançada</span>
        </h1>

        {/* Subtitle */}
        <p className="text-lg md:text-xl text-muted-foreground mb-8 max-w-3xl mx-auto leading-relaxed">
          Descubra o poder dos robôs de trading automatizados. Inicie, pare e controle seus algoritmos com total liberdade - <strong className="text-foreground">completamente gratuito</strong>.
        </p>

        {/* CTA Buttons */}
        <div className="flex flex-col sm:flex-row gap-4 justify-center mb-16">
          <Button asChild size="lg" className="bg-gradient-primary hover:scale-105 transition-all duration-300 glow-neon">
            <a href="/marketplace">Começar Agora</a>
          </Button>
          <Button asChild variant="outline" size="lg" className="border-primary/20 hover:bg-primary/10">
            <a href="/products">Ver Demonstração</a>
          </Button>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-4xl mx-auto">
          <div className="text-center">
            <div className="flex items-center justify-center mb-2">
              <svg className="w-6 h-6 text-primary mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
              </svg>
              <span className="text-3xl md:text-4xl font-bold text-neon">+127%</span>
            </div>
            <p className="text-muted-foreground">Rentabilidade Média</p>
          </div>
          
          <div className="text-center">
            <div className="flex items-center justify-center mb-2">
              <svg className="w-6 h-6 text-yellow-400 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
              <span className="text-3xl md:text-4xl font-bold text-yellow-400">500+</span>
            </div>
            <p className="text-muted-foreground">Robôs Verificados</p>
          </div>
          
          <div className="text-center">
            <div className="flex items-center justify-center mb-2">
              <svg className="w-6 h-6 text-primary mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z" />
              </svg>
              <span className="text-3xl md:text-4xl font-bold text-neon">10K+</span>
            </div>
            <p className="text-muted-foreground">Usuários Ativos</p>
          </div>
        </div>
      </div>
    </section>
  );
};