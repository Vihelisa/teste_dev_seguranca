import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Eye, EyeOff, Loader2, Lock, Mail, Shield, Cpu, Zap, Binary, Activity } from "lucide-react";
import { useState, useEffect, useRef } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { useToast } from "@/hooks/use-toast";

const loginSchema = z.object({
  email: z.string().email("Email inválido"),
  password: z.string().min(6, "Senha deve ter pelo menos 6 caracteres"),
});

type LoginForm = z.infer<typeof loginSchema>;

const LoginPage = () => {
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [isVisible, setIsVisible] = useState(false);
  const [scanAnimation, setScanAnimation] = useState(false);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  const navigate = useNavigate();
  const auth = useAuth();
  const { toast } = useToast();

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginForm>({
    resolver: zodResolver(loginSchema),
  });

  useEffect(() => {
    setIsVisible(true);
    const timer = setTimeout(() => setScanAnimation(true), 1000);

    // Matrix animation (remains the same)
    const canvas = canvasRef.current;
    if (canvas) {
      const ctx = canvas.getContext('2d');
      if (ctx) {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
        const chars = '01アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲン';
        const charArray = chars.split('');
        const fontSize = 14;
        const columns = canvas.width / fontSize;
        const drops: number[] = [];
        for (let i = 0; i < columns; i++) {
          drops[i] = 1;
        }
        const draw = () => {
          ctx.fillStyle = 'rgba(3, 7, 18, 0.05)';
          ctx.fillRect(0, 0, canvas.width, canvas.height);
          ctx.fillStyle = 'hsl(180, 100%, 70%)';
          ctx.font = `${fontSize}px monospace`;
          for (let i = 0; i < drops.length; i++) {
            const text = charArray[Math.floor(Math.random() * charArray.length)];
            ctx.fillText(text, i * fontSize, drops[i] * fontSize);
            if (drops[i] * fontSize > canvas.height && Math.random() > 0.975) {
              drops[i] = 0;
            }
            drops[i]++;
          }
        };
        const interval = setInterval(draw, 35);
        return () => {
          clearInterval(interval);
          clearTimeout(timer);
        };
      }
    }
    return () => clearTimeout(timer);
  }, []);

  const onSubmit = async (data: LoginForm) => {
    setIsLoading(true);
    setScanAnimation(true);
    try {
      await auth.login({ email: data.email, password: data.password });
      toast({
        title: "Conexão Estabelecida",
        description: "Bem-vindo de volta, agente.",
        variant: "default",
      });
      navigate("/dashboard");
    } catch (error: any) {
      const errorMessage = error.response?.data?.error || "Falha na autenticação. Verifique suas credenciais.";
      toast({
        title: "Erro de Conexão",
        description: errorMessage,
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
      setScanAnimation(false);
    }
  };

  return (
    <div className="min-h-screen relative overflow-hidden bg-gradient-hero">
      {/* Matrix canvas background */}
      <canvas
        ref={canvasRef}
        className="absolute inset-0 opacity-20 pointer-events-none"
      />

      {/* ... rest of the JSX ... */}

      <div className="container mx-auto px-6 py-8 relative z-10 min-h-screen flex items-center justify-center">
        <div className="max-w-lg mx-auto w-full">

          {/* ... Status indicators and title ... */}
          <div className={`flex justify-center space-x-8 mb-8 transition-all duration-1000 ${
            isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'
          }`}>
            <div className="flex items-center space-x-2 text-sm">
              <div className="w-2 h-2 bg-electric-green rounded-full animate-pulse" />
              <span className="text-muted-foreground">Sistema Online</span>
            </div>
            <div className="flex items-center space-x-2 text-sm">
              <Activity className="w-4 h-4 text-neon-cyan animate-pulse" />
              <span className="text-muted-foreground">IA Ativa</span>
            </div>
            <div className="flex items-center space-x-2 text-sm">
              <Binary className="w-4 h-4 text-neon-purple animate-pulse" />
              <span className="text-muted-foreground">Blockchain</span>
            </div>
          </div>

          <div className={`text-center mb-12 transition-all duration-1200 ${
            isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-12'
          }`}>
            <div className="relative mb-6">
              <div className="absolute inset-0 bg-gradient-primary rounded-full blur-2xl opacity-50 animate-glow-pulse scale-150" />
              <div className="relative w-20 h-20 bg-gradient-primary rounded-full flex items-center justify-center glow-neon mx-auto border-2 border-primary/50">
                <Cpu className="w-10 h-10 text-primary-foreground animate-pulse" />
              </div>
            </div>
            <h1 className="text-5xl font-black text-gradient animate-neon-pulse mb-4 tracking-wider">
              AURA QUANT
            </h1>
            <div className="text-lg text-muted-foreground space-y-1">
              <div className="flex items-center justify-center gap-2">
                <Zap className="w-5 h-5 text-neon-cyan animate-pulse" />
                <span>Sistema de Trading Inteligente</span>
              </div>
              <p className="text-sm opacity-75">Autenticação biométrica neural</p>
            </div>
          </div>

          <Card className={`border-2 border-primary/30 bg-gradient-card/60 backdrop-blur-2xl relative overflow-hidden transition-all duration-1000 delay-300 shadow-2xl ${
            isVisible ? 'opacity-100 translate-y-0 scale-100' : 'opacity-0 translate-y-16 scale-90'
          }`}>

            <div className="absolute inset-0 bg-gradient-to-r from-primary/20 via-transparent to-accent/20 animate-scan opacity-50" />
            <div className="absolute inset-0 bg-gradient-to-l from-accent/20 via-transparent to-primary/20 animate-scan opacity-50" style={{ animationDelay: '2s' }} />

            <div className="absolute top-2 left-2 w-4 h-4 border-l-2 border-t-2 border-neon-cyan animate-pulse" />
            <div className="absolute top-2 right-2 w-4 h-4 border-r-2 border-t-2 border-neon-purple animate-pulse" style={{ animationDelay: '0.5s' }} />
            <div className="absolute bottom-2 left-2 w-4 h-4 border-l-2 border-b-2 border-accent animate-pulse" style={{ animationDelay: '1s' }} />
            <div className="absolute bottom-2 right-2 w-4 h-4 border-r-2 border-b-2 border-neon-cyan animate-pulse" style={{ animationDelay: '1.5s' }} />

            <CardHeader className="text-center pb-8 relative">
              <div className="absolute top-0 left-1/2 transform -translate-x-1/2 w-12 h-1 bg-gradient-primary rounded-full opacity-50" />

              <CardTitle className="text-3xl font-bold text-gradient flex items-center justify-center gap-3 mb-2">
                <Shield className="w-8 h-8 text-primary animate-float" />
                ACESSO AUTORIZADO
              </CardTitle>
              <CardDescription className="text-base text-muted-foreground">
                Inicialize conexão com a matriz de trading
              </CardDescription>

              <div className="mt-4 flex justify-center">
                <div className="px-4 py-2 bg-electric-green/10 border border-electric-green/30 rounded-full text-xs text-electric-green font-mono">
                  STATUS: AGUARDANDO CREDENCIAIS
                </div>
              </div>
            </CardHeader>

            <CardContent className="relative space-y-8">
              <form onSubmit={handleSubmit(onSubmit)} className="space-y-8">

                <div className={`space-y-3 transition-all duration-700 delay-700 ${
                  isVisible ? 'opacity-100 translate-x-0' : 'opacity-0 -translate-x-8'
                }`}>
                  <Label htmlFor="email" className="text-base font-semibold flex items-center gap-3">
                    <Mail className="w-5 h-5 text-neon-cyan animate-pulse" />
                    ID DO USUÁRIO
                  </Label>
                  <div className="relative group">
                    <div className="absolute inset-0 bg-gradient-to-r from-primary/10 to-accent/10 rounded-lg blur-sm opacity-0 group-focus-within:opacity-100 transition-all duration-500" />
                    <Mail className="absolute left-4 top-4 h-5 w-5 text-muted-foreground group-focus-within:text-primary transition-all duration-300 z-10" />
                    <Input
                      id="email"
                      type="email"
                      placeholder="usuario@sistema.neural"
                      className="relative z-10 pl-12 py-4 text-lg bg-input/20 border-2 border-border/30 focus:border-primary focus:ring-4 focus:ring-primary/20 transition-all duration-500 hover:bg-input/40 focus:bg-input/60 rounded-lg font-mono"
                      {...register("email")}
                    />
                    <div className="absolute right-4 top-4 w-2 h-2 bg-neon-cyan rounded-full animate-pulse opacity-50" />
                  </div>
                  {errors.email && (
                    <p className="text-sm text-destructive animate-fade-in flex items-center gap-2">
                      <Zap className="w-4 h-4" />
                      {errors.email.message}
                    </p>
                  )}
                </div>

                <div className={`space-y-3 transition-all duration-700 delay-900 ${
                  isVisible ? 'opacity-100 translate-x-0' : 'opacity-0 translate-x-8'
                }`}>
                  <Label htmlFor="password" className="text-base font-semibold flex items-center gap-3">
                    <Lock className="w-5 h-5 text-neon-purple animate-pulse" />
                    CÓDIGO DE ACESSO
                  </Label>
                  <div className="relative group">
                    <div className="absolute inset-0 bg-gradient-to-r from-accent/10 to-primary/10 rounded-lg blur-sm opacity-0 group-focus-within:opacity-100 transition-all duration-500" />
                    <Lock className="absolute left-4 top-4 h-5 w-5 text-muted-foreground group-focus-within:text-accent transition-all duration-300 z-10" />
                    <Input
                      id="password"
                      type={showPassword ? "text" : "password"}
                      placeholder="████████████████"
                      className="relative z-10 pl-12 pr-12 py-4 text-lg bg-input/20 border-2 border-border/30 focus:border-accent focus:ring-4 focus:ring-accent/20 transition-all duration-500 hover:bg-input/40 focus:bg-input/60 rounded-lg font-mono tracking-widest"
                      {...register("password")}
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-4 top-4 text-muted-foreground hover:text-accent transition-all duration-300 hover:scale-110 z-10"
                    >
                      {showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                    </button>
                  </div>
                  {errors.password && (
                    <p className="text-sm text-destructive animate-fade-in flex items-center gap-2">
                      <Zap className="w-4 h-4" />
                      {errors.password.message}
                    </p>
                  )}
                </div>

                <Button
                  type="submit"
                  className={`w-full py-6 text-lg font-bold bg-gradient-primary hover:opacity-90 text-primary-foreground relative overflow-hidden group border-2 border-primary/50 hover:border-primary transition-all duration-500 disabled:opacity-50 ${
                    isVisible ? 'animate-scale-in' : ''
                  }`}
                  style={{ animationDelay: '1.2s' }}
                  disabled={isLoading}
                >
                  <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent transform -skew-x-12 -translate-x-full group-hover:translate-x-full transition-transform duration-1000" />
                  <div className="absolute inset-0 bg-gradient-to-r from-primary/50 to-accent/50 opacity-0 group-hover:opacity-100 transition-opacity duration-500" />

                  {isLoading ? (
                    <div className="flex items-center justify-center gap-3 relative z-10">
                      <Loader2 className="h-6 w-6 animate-spin" />
                      <span className="font-mono">AUTENTICANDO...</span>
                      <div className="flex space-x-1">
                        <div className="w-2 h-2 bg-current rounded-full animate-pulse" />
                        <div className="w-2 h-2 bg-current rounded-full animate-pulse" style={{ animationDelay: '0.2s' }} />
                        <div className="w-2 h-2 bg-current rounded-full animate-pulse" style={{ animationDelay: '0.4s' }} />
                      </div>
                    </div>
                  ) : (
                    <div className="flex items-center justify-center gap-3 relative z-10">
                      <Shield className="w-6 h-6" />
                      <span className="font-mono tracking-wider">INICIAR CONEXÃO</span>
                      <Zap className="w-6 h-6 animate-pulse" />
                    </div>
                  )}
                </Button>

                <div className={`pt-4 border-t border-border/30 transition-all duration-500 delay-1400 ${
                  isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'
                }`}>
                  <div className="grid grid-cols-3 gap-4 text-xs text-center">
                    <div className="space-y-2">
                      <div className="w-3 h-3 bg-electric-green rounded-full mx-auto animate-pulse" />
                      <span className="text-muted-foreground">Servidor</span>
                    </div>
                    <div className="space-y-2">
                      <div className="w-3 h-3 bg-neon-cyan rounded-full mx-auto animate-pulse" style={{ animationDelay: '0.5s' }} />
                      <span className="text-muted-foreground">Blockchain</span>
                    </div>
                    <div className="space-y-2">
                      <div className="w-3 h-3 bg-neon-purple rounded-full mx-auto animate-pulse" style={{ animationDelay: '1s' }} />
                      <span className="text-muted-foreground">IA Trading</span>
                    </div>
                  </div>
                </div>

                <p className={`text-center text-sm text-muted-foreground transition-all duration-500 delay-1600 ${
                  isVisible ? 'opacity-100' : 'opacity-0'
                }`}>
                  Novo no sistema?{" "}
                  <Link
                    to="/register"
                    className="text-primary hover:text-primary/80 font-semibold transition-colors underline decoration-primary/50 hover:decoration-primary"
                  >
                    Solicitar acesso premium
                  </Link>
                </p>
              </form>
            </CardContent>
          </Card>

          <div className={`mt-8 text-center space-y-4 transition-all duration-500 delay-1800 ${
            isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'
          }`}>
            <div className="flex justify-center items-center gap-4 text-xs text-muted-foreground">
              <div className="flex items-center gap-1">
                <div className="w-1 h-1 bg-electric-green rounded-full animate-pulse" />
                <span>SSL Ativo</span>
              </div>
              <div className="flex items-center gap-1">
                <div className="w-1 h-1 bg-neon-cyan rounded-full animate-pulse" />
                <span>Criptografia 256-bit</span>
              </div>
              <div className="flex items-center gap-1">
                <div className="w-1 h-1 bg-neon-purple rounded-full animate-pulse" />
                <span>Proteção Quântica</span>
              </div>
            </div>
            <p className="text-xs text-muted-foreground/70 font-mono">
              © 2024 AURA QUANT SYSTEMS • VERSÃO 3.2.1 • BUILD 20241210
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
