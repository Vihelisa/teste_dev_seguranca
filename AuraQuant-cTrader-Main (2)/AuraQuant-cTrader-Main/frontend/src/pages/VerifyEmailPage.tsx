import { useEffect, useState } from "react";
import { useSearchParams, Link } from "react-router-dom";
import { CheckCircle, XCircle, Loader2, LogIn } from "lucide-react";
import { PageLayout } from "@/components/PageLayout";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { AnimatedBackground } from "@/components/AnimatedBackground";
import { FloatingParticles } from "@/components/FloatingParticles";
import { verifyEmail } from "@/api";

type VerifyStatus = 'loading' | 'success' | 'error';

const VerifyEmailPage = () => {
  const [searchParams] = useSearchParams();
  const [verifyStatus, setVerifyStatus] = useState<VerifyStatus>('loading');
  const [message, setMessage] = useState('');
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    setIsVisible(true);

    const uidb64 = searchParams.get('uidb64');
    const token = searchParams.get('token');

    if (!uidb64 || !token) {
      setVerifyStatus('error');
      setMessage('Link inválido. Parâmetros ausentes.');
      return;
    }

    verifyEmail(uidb64, token)
      .then(() => {
        setVerifyStatus('success');
        setMessage('Sua conta está ativa. Agora você pode fazer login.');
      })
      .catch((err) => {
        setVerifyStatus('error');
        setMessage(err.response?.data?.error || 'Link inválido ou expirado. Solicite um novo cadastro.');
      });
  }, [searchParams]);

  const iconMap = {
    loading: <Loader2 className="w-8 h-8 text-primary-foreground animate-spin" />,
    success: <CheckCircle className="w-8 h-8 text-primary-foreground" />,
    error: <XCircle className="w-8 h-8 text-primary-foreground" />,
  };

  const titleMap = {
    loading: 'VERIFICANDO...',
    success: 'EMAIL CONFIRMADO',
    error: 'LINK INVÁLIDO',
  };

  const cardTitleMap = {
    loading: 'Processando seu link...',
    success: 'Conta Ativada com Sucesso!',
    error: 'Ops, algo deu errado',
  };

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
                  {iconMap[verifyStatus]}
                </div>
              </div>
              <h1 className="text-4xl font-bold text-gradient animate-neon-pulse mb-2">
                {titleMap[verifyStatus]}
              </h1>
            </div>

            <Card className={`border-glow bg-gradient-card/70 backdrop-blur-xl relative overflow-hidden transition-all duration-800 delay-200 animated-border holographic ${
              isVisible ? 'opacity-100 translate-y-0 scale-100' : 'opacity-0 translate-y-16 scale-90'
            }`}>
              <div className="absolute top-0 left-0 w-full h-0.5 bg-gradient-to-r from-transparent via-accent to-transparent animate-scan" />

              <CardHeader className="text-center pb-4">
                <CardTitle className="text-xl font-bold text-gradient">
                  {cardTitleMap[verifyStatus]}
                </CardTitle>
                {message && (
                  <CardDescription className="text-muted-foreground">
                    {message}
                  </CardDescription>
                )}
              </CardHeader>

              {verifyStatus !== 'loading' && (
                <CardContent className="text-center">
                  <Link to="/login">
                    <Button className="w-full bg-gradient-primary hover:opacity-90 text-primary-foreground font-bold py-4 glow-modern transition-all duration-300 relative overflow-hidden group">
                      <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent transform -skew-x-12 -translate-x-full group-hover:translate-x-full transition-transform duration-1000" />
                      <LogIn className="w-4 h-4 mr-2" />
                      {verifyStatus === 'success' ? 'Fazer Login' : 'Voltar para o Login'}
                    </Button>
                  </Link>
                </CardContent>
              )}
            </Card>

          </div>
        </div>
      </PageLayout>
    </div>
  );
};

export default VerifyEmailPage;
