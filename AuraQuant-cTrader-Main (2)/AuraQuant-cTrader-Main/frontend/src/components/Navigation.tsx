import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { User as UserIcon, LogOut } from "lucide-react";

export const Navigation = () => {
  const auth = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    auth.logout();
    navigate('/'); // Redirect to home after logout
  };

  const renderAuthSection = () => {
    if (!auth.isInitialized) {
      // Render a placeholder or nothing while auth state is being determined
      return <div className="hidden md:flex items-center gap-4 h-9 w-48 animate-pulse"><div className="bg-muted/50 rounded-md w-full h-full" /></div>;
    }

    if (auth.isAuthenticated && auth.user) {
      return (
        <div className="hidden md:flex items-center gap-4">
          <Link to="/support" className="text-sm font-medium hover:text-primary transition-colors">
            Suporte
          </Link>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" className="relative h-10 w-10 rounded-full">
                <Avatar>
                  <AvatarImage src={`https://api.dicebear.com/8.x/bottts-neutral/svg?seed=${auth.user.email}`} alt="User Avatar" />
                  <AvatarFallback>
                    <UserIcon />
                  </AvatarFallback>
                </Avatar>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent className="w-56" align="end" forceMount>
              <DropdownMenuLabel className="font-normal">
                <div className="flex flex-col space-y-1">
                  <p className="text-sm font-medium leading-none">
                    {auth.user.first_name || auth.user.username}
                  </p>
                  <p className="text-xs leading-none text-muted-foreground">
                    {auth.user.email}
                  </p>
                </div>
              </DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={() => navigate('/my-accounts')}>
                <UserIcon className="mr-2 h-4 w-4" />
                <span>Minha Conta</span>
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={handleLogout}>
                <LogOut className="mr-2 h-4 w-4" />
                <span>Sair</span>
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      );
    }

    return (
      <div className="hidden md:flex items-center gap-4">
        <Link to="/support" className="text-sm font-medium hover:text-primary transition-colors">
          Suporte
        </Link>
        <Link to="/login" className="text-sm font-medium hover:text-primary transition-colors">
          Entrar
        </Link>
        <Button asChild variant="outline" size="sm" className="border-primary/20 hover:bg-primary/10">
          <Link to="/register">Cadastrar</Link>
        </Button>
      </div>
    );
  };

  return (
    <nav className="fixed top-0 w-full z-50 border-b border-border/50 backdrop-blur-xl bg-background/80">
      <div className="container mx-auto px-6 py-4">
        <div className="flex items-center justify-between">
          {/* Logo */}
          <div className="flex items-center gap-3">
            <Link to="/" className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-primary rounded-xl flex items-center justify-center">
                <span className="text-lg font-bold text-black">AQ</span>
              </div>
              <div className="flex items-center gap-2">
                <h1 className="text-xl font-bold">Aura Quant</h1>
                <Badge variant="secondary" className="bg-primary/10 text-primary border-primary/20">
                  Institutional
                </Badge>
              </div>
            </Link>
          </div>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center gap-8">
            {!auth.isAuthenticated && (
              <Link to="/" className="text-sm font-medium hover:text-primary transition-colors">
                Início
              </Link>
            )}
            <Link to="/dashboard" className="text-sm font-medium hover:text-primary transition-colors">
              Dashboard
            </Link>
            <Link to="/marketplace" className="text-sm font-medium hover:text-primary transition-colors">
              Estratégias
            </Link>
            <Link to="/analytics" className="text-sm font-medium hover:text-primary transition-colors">
              Análises
            </Link>
            <Link to="/academy" className="text-sm font-medium hover:text-primary transition-colors">
              Academia
            </Link>
            <Link to="/partners" className="text-sm font-medium hover:text-primary transition-colors">
              Parcerias
            </Link>

            {/* Mais Dropdown */}
            <div className="relative group">
              <span className="text-sm font-medium hover:text-primary transition-colors cursor-pointer">
                Mais
              </span>
              <div className="absolute top-full right-0 mt-2 w-56 bg-background/95 backdrop-blur-sm border border-border/20 rounded-lg shadow-xl opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-300 z-50">
                <Link to="/my-accounts" className="block px-4 py-3 text-sm hover:bg-muted/50 transition-colors">Minhas Contas</Link>
                <Link to="/trading-history" className="block px-4 py-3 text-sm hover:bg-muted/50 transition-colors">Histórico de Operações</Link>
                <Link to="/products" className="block px-4 py-3 text-sm hover:bg-muted/50 transition-colors">Produtos</Link>
                <hr className="border-border/20 mx-2" />
                <Link to="/community" className="block px-4 py-3 text-sm hover:bg-muted/50 transition-colors">Comunidade</Link>
                <Link to="/downloads" className="block px-4 py-3 text-sm hover:bg-muted/50 transition-colors">Downloads</Link>
                <Link to="/status" className="block px-4 py-3 text-sm hover:bg-muted/50 transition-colors">Status do Sistema</Link>
              </div>
            </div>
          </div>

          {/* Auth Buttons */}
          {renderAuthSection()}

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