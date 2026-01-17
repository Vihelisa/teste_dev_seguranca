import { Button } from "@/components/ui/button";

export const CtaSection = () => {
  return (
    <section className="py-24">
      <div className="container mx-auto px-6">
        <div className="max-w-3xl mx-auto text-center">
          {/* Main CTA */}
          <h2 className="text-3xl md:text-5xl font-bold mb-6">
            Pronto para começar?
          </h2>
          <p className="text-lg md:text-xl text-muted-foreground mb-8 leading-relaxed">
            Junte-se a milhares de traders que já automatizaram seus investimentos
          </p>
          
          <Button 
            asChild
            size="lg" 
            className="bg-gradient-primary hover:scale-105 transition-all duration-300 glow-neon text-lg px-8 py-6"
          >
            <a href="/marketplace">Explorar Robôs</a>
          </Button>
        </div>
      </div>
    </section>
  );
};