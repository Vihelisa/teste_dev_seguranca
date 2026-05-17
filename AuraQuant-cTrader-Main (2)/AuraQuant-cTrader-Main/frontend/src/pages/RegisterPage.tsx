import { PageLayout } from "@/components/PageLayout";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Eye, EyeOff, Loader2, Lock, Mail, User, Phone, UserPlus, Rocket } from "lucide-react";
import { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { AnimatedBackground } from "@/components/AnimatedBackground";
import { FloatingParticles } from "@/components/FloatingParticles";
import { useAuth } from "@/contexts/AuthContext";
import { useToast } from "@/hooks/use-toast";

const formatPhone = (value: string): string => {
  const digits = value.replace(/\D/g, '').slice(0, 11);
  if (digits.length <= 2) return digits.length ? `(${digits}` : '';
  if (digits.length <= 6) return `(${digits.slice(0, 2)}) ${digits.slice(2)}`;
  if (digits.length <= 10) return `(${digits.slice(0, 2)}) ${digits.slice(2, 6)}-${digits.slice(6)}`;
  return `(${digits.slice(0, 2)}) ${digits.slice(2, 7)}-${digits.slice(7, 11)}`;
};

const registerSchema = z.object({
  name: z.string().min(2, "Nome deve ter pelo menos 2 caracteres"),
  email: z.string().email("Email inválido"),
  phone: z.union([
    z.string().regex(/^\(\d{2}\) \d{4,5}-\d{4}$/, "Telefone inválido"),
    z.literal(''),
  ]).optional(),
  password: z.string().min(8, "Senha deve ter pelo menos 8 caracteres"),
  confirmPassword: z.string(),
  acceptTerms: z.boolean().refine(val => val === true, {
    message: "Você deve aceitar os termos de uso",
  }),
}).refine((data) => data.password === data.confirmPassword, {
  message: "Senhas não coincidem",
  path: ["confirmPassword"],
});

type RegisterForm = z.infer<typeof registerSchema>;

const RegisterPage = () => {
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [isVisible, setIsVisible] = useState(false);

  const navigate = useNavigate();
  const auth = useAuth();
  const { toast } = useToast();

  useEffect(() => {
    setIsVisible(true);
  }, []);

  const {
    register,
    handleSubmit,
    setValue,
    formState: { errors },
  } = useForm<RegisterForm>({
    resolver: zodResolver(registerSchema),
  });

  const phoneRegister = register("phone");

  const onSubmit = async (data: RegisterForm) => {
    setIsLoading(true);
    try {
      // The auth context's register function now handles the API call
      await auth.register({
        email: data.email,
        password: data.password,
        name: data.name,
        phone: data.phone || '',
      });
      // After successful registration, the backend might automatically log the user in.
      // A more robust flow would be to redirect to a "please verify your email" page
      // or directly to the login page. For now, we'll redirect to login.
      toast({
        title: "Cadastro Realizado!",
        description: "Enviamos um link de confirmação para o seu email. Verifique sua caixa de entrada.",
        variant: "default",
      });
      navigate("/verify-email-sent");
    } catch (error: any) {
      const errorMessage = error.response?.data?.error || "Não foi possível criar sua conta.";
      toast({
        title: "Erro no Cadastro",
        description: errorMessage,
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen relative overflow-hidden">
      <AnimatedBackground />
      <FloatingParticles />

      {/* Dynamic tech grid background */}
      <div className="absolute inset-0 tech-grid opacity-10" />

      {/* Holographic overlay */}
      <div className="absolute inset-0 holographic" />

      <PageLayout title="" description="">
        <div className="container mx-auto px-6 py-8 relative z-10">
          <div className="max-w-md mx-auto">

            {/* Animated header */}
            <div className={`text-center mb-8 transition-all duration-1000 ${
              isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'
            }`}>
              <div className="relative inline-block mb-4">
                <div className="absolute inset-0 bg-gradient-primary rounded-full blur-xl opacity-40 animate-glow-pulse" />
                <div className="relative w-16 h-16 bg-gradient-primary rounded-full flex items-center justify-center glow-purple mx-auto">
                  <Rocket className="w-8 h-8 text-primary-foreground animate-float" />
                </div>
              </div>
              <h1 className="text-4xl font-bold text-gradient animate-neon-pulse mb-2">
                NOVA CONTA
              </h1>
              <p className="text-muted-foreground">
                Junte-se à revolução do trading inteligente
              </p>
            </div>

            {/* Main card with enhanced animations */}
            <Card className={`border-glow bg-gradient-card/70 backdrop-blur-xl relative overflow-hidden transition-all duration-800 delay-200 animated-border holographic ${
              isVisible ? 'opacity-100 translate-y-0 scale-100' : 'opacity-0 translate-y-16 scale-90'
            }`}>

              {/* Multiple scanning lines */}
              <div className="absolute top-0 left-0 w-full h-0.5 bg-gradient-to-r from-transparent via-accent to-transparent animate-scan" />
              <div className="absolute bottom-0 left-0 w-full h-0.5 bg-gradient-to-r from-transparent via-primary to-transparent animate-scan" style={{ animationDelay: '1s', animationDirection: 'reverse' }} />

              <CardHeader className="text-center pb-6 relative">
                <div className="absolute top-4 right-4 w-2 h-2 bg-neon-purple rounded-full animate-pulse" />
                <div className="absolute top-4 left-4 w-1 h-1 bg-neon-cyan rounded-full animate-pulse" style={{ animationDelay: '0.5s' }} />
                <div className="absolute bottom-4 right-8 w-1 h-1 bg-accent rounded-full animate-pulse" style={{ animationDelay: '1s' }} />

                <CardTitle className="text-2xl font-bold text-gradient flex items-center justify-center gap-2">
                  <UserPlus className="w-6 h-6 text-accent animate-pulse" />
                  Iniciar Jornada
                </CardTitle>
                <CardDescription className="text-muted-foreground">
                  Configure sua conta para acessar ferramentas avançadas
                </CardDescription>
              </CardHeader>

            <CardContent className="relative">
              <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
                {/* ... form fields remain the same ... */}
                <div className={`space-y-2 transition-all duration-500 delay-400 ${
                  isVisible ? 'opacity-100 translate-x-0' : 'opacity-0 -translate-x-6'
                }`}>
                  <Label htmlFor="name" className="text-sm font-medium flex items-center gap-2">
                    <User className="w-4 h-4 text-neon-cyan" />
                    Identificação
                  </Label>
                  <div className="relative group">
                    <User className="absolute left-3 top-3 h-4 w-4 text-muted-foreground group-focus-within:text-accent transition-all duration-300" />
                    <Input
                      id="name"
                      type="text"
                      placeholder="Nome completo"
                      className="pl-10 bg-input/20 border-border/30 focus:border-accent focus:ring-2 focus:ring-accent/50 transition-all duration-300 hover:bg-input/40 focus:bg-input/50 focus:shadow-glow-purple"
                      {...register("name")}
                    />
                    <div className="absolute inset-0 bg-gradient-to-r from-accent/5 to-primary/5 rounded-md opacity-0 group-focus-within:opacity-100 transition-opacity duration-300 pointer-events-none" />
                  </div>
                  {errors.name && (
                    <p className="text-sm text-destructive animate-fade-in">{errors.name.message}</p>
                  )}
                </div>

                <div className={`space-y-2 transition-all duration-500 delay-600 ${
                  isVisible ? 'opacity-100 translate-x-0' : 'opacity-0 translate-x-6'
                }`}>
                  <Label htmlFor="email" className="text-sm font-medium flex items-center gap-2">
                    <Mail className="w-4 h-4 text-neon-purple" />
                    Email corporativo
                  </Label>
                  <div className="relative group">
                    <Mail className="absolute left-3 top-3 h-4 w-4 text-muted-foreground group-focus-within:text-primary transition-all duration-300" />
                    <Input
                      id="email"
                      type="email"
                      placeholder="seu@email.com"
                      className="pl-10 bg-input/20 border-border/30 focus:border-primary focus:ring-2 focus:ring-primary/50 transition-all duration-300 hover:bg-input/40 focus:bg-input/50 focus:shadow-glow-neon"
                      {...register("email")}
                    />
                    <div className="absolute inset-0 bg-gradient-to-r from-primary/5 to-accent/5 rounded-md opacity-0 group-focus-within:opacity-100 transition-opacity duration-300 pointer-events-none" />
                  </div>
                  {errors.email && (
                    <p className="text-sm text-destructive animate-fade-in">{errors.email.message}</p>
                  )}
                </div>

                <div className={`grid grid-cols-2 gap-4 transition-all duration-500 delay-800 ${
                  isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'
                }`}>
                  <div className="space-y-2">
                    <Label htmlFor="phone" className="text-sm font-medium flex items-center gap-2">
                      <Phone className="w-4 h-4 text-accent" />
                      Contato
                    </Label>
                    <div className="relative group">
                      <Phone className="absolute left-3 top-3 h-4 w-4 text-muted-foreground group-focus-within:text-accent transition-all duration-300" />
                      <Input
                        id="phone"
                        type="tel"
                        placeholder="(11) 99999-9999"
                        maxLength={15}
                        className="pl-10 bg-input/20 border-border/30 focus:border-accent focus:ring-2 focus:ring-accent/50 transition-all duration-300 hover:bg-input/40 focus:bg-input/50"
                        name={phoneRegister.name}
                        ref={phoneRegister.ref}
                        onBlur={phoneRegister.onBlur}
                        onChange={(e) => {
                          const formatted = formatPhone(e.target.value);
                          e.target.value = formatted;
                          setValue("phone", formatted, { shouldValidate: true });
                        }}
                      />
                    </div>
                    {errors.phone && (
                      <p className="text-sm text-destructive animate-fade-in">{errors.phone.message}</p>
                    )}
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="password" className="text-sm font-medium flex items-center gap-2">
                      <Lock className="w-4 h-4 text-neon-blue" />
                      Segurança
                    </Label>
                    <div className="relative group">
                      <Lock className="absolute left-3 top-3 h-4 w-4 text-muted-foreground group-focus-within:text-primary transition-all duration-300" />
                      <Input
                        id="password"
                        type={showPassword ? "text" : "password"}
                        placeholder="••••••••"
                        className="pl-10 pr-10 bg-input/20 border-border/30 focus:border-primary focus:ring-2 focus:ring-primary/50 transition-all duration-300 hover:bg-input/40 focus:bg-input/50"
                        {...register("password")}
                      />
                      <button
                        type="button"
                        onClick={() => setShowPassword(!showPassword)}
                        className="absolute right-2 top-3 text-muted-foreground hover:text-primary transition-all duration-200 hover:scale-110"
                      >
                        {showPassword ? <EyeOff className="h-3 w-3" /> : <Eye className="h-3 w-3" />}
                      </button>
                    </div>
                    {errors.password && (
                      <p className="text-sm text-destructive animate-fade-in">{errors.password.message}</p>
                    )}
                  </div>
                </div>

                <div className={`space-y-2 transition-all duration-500 delay-1000 ${
                  isVisible ? 'opacity-100 translate-x-0' : 'opacity-0 -translate-x-4'
                }`}>
                  <Label htmlFor="confirmPassword" className="text-sm font-medium flex items-center gap-2">
                    <Lock className="w-4 h-4 text-destructive" />
                    Confirmação de segurança
                  </Label>
                  <div className="relative group">
                    <Lock className="absolute left-3 top-3 h-4 w-4 text-muted-foreground group-focus-within:text-destructive transition-all duration-300" />
                    <Input
                      id="confirmPassword"
                      type={showConfirmPassword ? "text" : "password"}
                      placeholder="••••••••••••"
                      className="pl-10 pr-10 bg-input/20 border-border/30 focus:border-destructive focus:ring-2 focus:ring-destructive/50 transition-all duration-300 hover:bg-input/40 focus:bg-input/50"
                      {...register("confirmPassword")}
                    />
                    <button
                      type="button"
                      onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                      className="absolute right-3 top-3 text-muted-foreground hover:text-destructive transition-all duration-200 hover:scale-110"
                    >
                      {showConfirmPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </button>
                    <div className="absolute inset-0 bg-gradient-to-r from-destructive/5 to-accent/5 rounded-md opacity-0 group-focus-within:opacity-100 transition-opacity duration-300 pointer-events-none" />
                  </div>
                  {errors.confirmPassword && (
                    <p className="text-sm text-destructive animate-fade-in">{errors.confirmPassword.message}</p>
                  )}
                </div>

                <div className="flex items-start space-x-2">
                  <input
                    id="acceptTerms"
                    type="checkbox"
                    className="w-4 h-4 mt-1 rounded border-border bg-input text-primary focus:ring-primary focus:ring-2"
                    {...register("acceptTerms")}
                  />
                  <Label htmlFor="acceptTerms" className="text-sm text-muted-foreground leading-relaxed">
                    Aceito os{" "}
                    <Link to="/terms" className="text-primary hover:text-primary/80 transition-colors">
                      termos de uso
                    </Link>{" "}
                    e{" "}
                    <Link to="/privacy" className="text-primary hover:text-primary/80 transition-colors">
                      política de privacidade
                    </Link>
                  </Label>
                </div>
                {errors.acceptTerms && (
                  <p className="text-sm text-destructive">{errors.acceptTerms.message}</p>
                )}

                <Button
                  type="submit"
                  className={`w-full bg-gradient-primary hover:opacity-90 text-primary-foreground font-bold py-4 glow-modern transition-all duration-300 disabled:opacity-50 relative overflow-hidden group ${
                    isVisible ? 'animate-scale-in' : ''
                  }`}
                  style={{ animationDelay: '1.4s' }}
                  disabled={isLoading}
                >
                  <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent transform -skew-x-12 -translate-x-full group-hover:translate-x-full transition-transform duration-1000" />
                  {isLoading ? (
                    <>
                      <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                      PROCESSANDO DADOS...
                    </>
                  ) : (
                    <span className="flex items-center gap-2">
                      <Rocket className="w-5 h-5" />
                      CRIAR CONTA PREMIUM
                    </span>
                  )}
                </Button>

                {/* ... rest of JSX ... */}
              </form>
            </CardContent>
          </Card>
          </div>
        </div>
      </PageLayout>
    </div>
  );
};

export default RegisterPage;
