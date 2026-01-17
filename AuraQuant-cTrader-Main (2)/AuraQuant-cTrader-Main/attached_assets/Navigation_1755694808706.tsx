import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

export const Navigation = () => {
  return (
    <nav className="fixed top-0 w-full z-50 border-b border-border/50 backdrop-blur-xl bg-background/80">
      <div className="container mx-auto px-6 py-4">
        <div className="flex items-center justify-between">
          {/* Logo */}
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-primary rounded-xl flex items-center justify-center">
              <span className="text-lg font-bold text-black">AQ</span>
            </div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold">Aura Quant</h1>
              <span className="text-sm text-muted-foreground">by birdstone</span>
              <Badge variant="secondary" className="bg-primary/10 text-primary border-primary/20">
                Beta
              </Badge>
            </div>
          </div>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center gap-8">
            <a href="/" className="text-sm font-medium hover:text-primary transition-colors">
              Início
            </a>
            <a href="/marketplace" className="text-sm font-medium hover:text-primary transition-colors">
              Marketplace
            </a>
            <a href="/dashboard" className="text-sm font-medium hover:text-primary transition-colors">
              Dashboard
            </a>
            <a href="/products" className="text-sm font-medium hover:text-primary transition-colors">
              Produtos
            </a>
            <a href="/academy" className="text-sm font-medium hover:text-primary transition-colors">
              Academia
            </a>
          </div>

          {/* Auth Buttons */}
          <div className="hidden md:flex items-center gap-4">
            <a href="/support" className="text-sm font-medium hover:text-primary transition-colors">
              Suporte
            </a>
            <a href="/login" className="text-sm font-medium hover:text-primary transition-colors">
              Entrar
            </a>
            <Button asChild variant="outline" size="sm" className="border-primary/20 hover:bg-primary/10">
              <a href="/register">Cadastrar</a>
            </Button>
          </div>

          {/* Mobile Menu Button */}
          <Button variant="ghost" size="sm" className="md:hidden">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </Button>
        </div>
      </div>
    </nav>
  );
};