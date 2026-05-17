import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { Mail, ArrowLeft } from "lucide-react";
import { PageLayout } from "@/components/PageLayout";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { AnimatedBackground } from "@/components/AnimatedBackground";
import { FloatingParticles } from "@/components/FloatingParticles";

const VerifyEmailSentPage = () => {
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    setIsVisible(true);
  }, []);

  return (
    <div className="min-h-screen relative overflow-hidden">
      <AnimatedBackground />
      <FloatingParticles />
      <div className="absolute inset-0 tech-grid opacity-10" />
      <div className="absolute inset-0 holographic" />

      <PageLayout title="" description="">
        <div className="container mx-auto px-6 py-8 relative z-10">
          <div className="max-w-md mx-auto">

            <div className={`text-center mb-8 transition-all duration-1000 ${
              isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'
            }`}>
              <div className="relative inline-block mb-4">
                <div className="absolute inset-0 bg-gradient-primary rounded-full blur-xl opacity-40 animate-glow-pulse" />
                <div className="relative w-16 h-16 bg-gradient-primary rounded-full flex items-center justify-center glow-purple mx-auto">
                  <Mail className="w-8 h-8 text-primary-foreground animate-float" />
                </div>
              </div>
              <h1 className="text-4xl font-bold text-gradient animate-neon-pulse mb-2">
                VERIFIQUE SEU EMAIL
              </h1>
              <p className="text-muted-foreground">
                Um link de confirmação foi enviado para você
              </p>
            </div>

            <Card className={`border-glow bg-gradient-card/70 backdrop-blur-xl relative overflow-hidden transition-all duration-800 delay-200 animated-border holographic ${
              isVisible ? 'opacity-100 translate-y-0 scale-100' : 'opacity-0 translate-y-16 scale-90'
            }`}>
              <div className="absolute top-0 left-0 w-full h-0.5 bg-gradient-to-r from-transparent via-accent to-transparent animate-scan" />

              <CardHeader className="text-center pb-4">
                <CardTitle className="text-xl font-bold text-gradient flex items-center justify-center gap-2">
                  <Mail className="w-5 h-5 text-accent" />
                  Quase lá!
                </CardTitle>
                <CardDescription className="text-muted-foreground">
                  Acesse seu email e clique no link de confirmação para ativar sua conta.
                </CardDescription>
              </CardHeader>

              <CardContent className="space-y-4 text-center">
                <div className="bg-accent/10 border border-accent/20 rounded-lg p-4 text-sm text-muted-foreground">
                  <p>
                    O link expira em{" "}
                    <span className="text-accent font-semibold">3 dias</span>.
                  </p>
                  <p className="mt-1">
                    Não encontrou? Verifique sua caixa de <span className="text-accent font-semibold">spam</span>.
                  </p>
                </div>

                <Link to="/login">
                  <Button
                    variant="outline"
                    className="w-full border-border/30 hover:border-accent transition-all duration-300 mt-2"
                  >
                    <ArrowLeft className="w-4 h-4 mr-2" />
                    Voltar para o Login
                  </Button>
                </Link>
              </CardContent>
            </Card>

          </div>
        </div>
      </PageLayout>
    </div>
  );
};

export default VerifyEmailSentPage;
