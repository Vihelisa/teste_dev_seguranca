import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import heroImage from "@/assets/hero-ai-trading.jpg";

export const HeroSection = () => {
  return (
    <section className="relative min-h-screen flex items-center justify-center overflow-hidden tech-grid">
      {/* Background Image */}
      <div 
        className="absolute inset-0 bg-cover bg-center bg-no-repeat opacity-20"
        style={{ backgroundImage: `url(${heroImage})` }}
      />
      
      {/* Futuristic Overlay */}
      <div className="absolute inset-0 bg-gradient-hero" />
      <div className="absolute inset-0 bg-gradient-matrix opacity-5" />
      
      {/* Animated Background Elements */}
      <div className="absolute top-20 left-10 w-64 h-64 bg-neon-cyan/10 rounded-full blur-3xl animate-pulse" />
      <div className="absolute bottom-20 right-10 w-96 h-96 bg-neon-purple/10 rounded-full blur-3xl animate-pulse delay-1000" />
      
      {/* Content */}
      <div className="relative z-10 container mx-auto px-6 py-32 text-center">
        {/* Beta Badge */}
        <Badge className="mb-8 bg-neon-cyan/20 text-neon-cyan border border-neon-cyan/30 glow-neon hover:bg-neon-cyan/30 transition-all duration-300">
          🚀 PLATAFORMA QUANT BETA - ACESSO LIVRE
        </Badge>

        {/* Main Headline */}
        <h1 className="text-4xl md:text-6xl lg:text-7xl font-bold mb-6 leading-tight">
          <span className="text-matrix">ALGORITMOS</span> QUANTITATIVOS
          <br />
          <span className="text-gradient">POWERED BY IA</span>
        </h1>

        {/* Subtitle */}
        <p className="text-lg md:text-xl text-muted-foreground mb-8 max-w-3xl mx-auto leading-relaxed">
          Tecnologia de ponta em <span className="text-neon-cyan font-semibold">trading quantitativo</span>. Execute estratégias algorítmicas avançadas com controle total - <strong className="text-electric-green">100% gratuito</strong>.
        </p>

        {/* CTA Buttons */}
        <div className="flex flex-col sm:flex-row gap-4 justify-center mb-16">
          <Button asChild size="lg" className="bg-gradient-neon text-background font-bold hover:scale-105 transition-all duration-300 glow-neon border-0">
            <a href="/marketplace">INICIAR TRADING</a>
          </Button>
          <Button asChild variant="outline" size="lg" className="border-glow text-neon-cyan hover:bg-neon-cyan/10 hover:glow-neon transition-all duration-300">
            <a href="/products">DEMO LIVE</a>
          </Button>
        </div>

        {/* Quant Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-4xl mx-auto">
          <div className="text-center p-6 rounded-xl bg-card/50 backdrop-blur-sm border-glow">
            <div className="flex items-center justify-center mb-2">
              <svg className="w-6 h-6 text-electric-green mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
              </svg>
              <span className="text-3xl md:text-4xl font-bold text-electric-green">+247%</span>
            </div>
            <p className="text-muted-foreground font-medium">RETORNO ANUALIZADO</p>
          </div>
          
          <div className="text-center p-6 rounded-xl bg-card/50 backdrop-blur-sm border-glow">
            <div className="flex items-center justify-center mb-2">
              <svg className="w-6 h-6 text-neon-purple mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
              <span className="text-3xl md:text-4xl font-bold text-neon-purple">1.2K+</span>
            </div>
            <p className="text-muted-foreground font-medium">ALGORITMOS ATIVOS</p>
          </div>
          
          <div className="text-center p-6 rounded-xl bg-card/50 backdrop-blur-sm border-glow">
            <div className="flex items-center justify-center mb-2">
              <svg className="w-6 h-6 text-neon-cyan mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z" />
              </svg>
              <span className="text-3xl md:text-4xl font-bold text-neon-cyan">50K+</span>
            </div>
            <p className="text-muted-foreground font-medium">QUANTS CONECTADOS</p>
          </div>
        </div>
      </div>
    </section>
  );
};