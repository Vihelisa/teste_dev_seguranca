import { PageLayout } from "@/components/PageLayout";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { useState } from "react";

const Onboarding = () => {
  const [currentStep, setCurrentStep] = useState(1);
  const totalSteps = 5;

  const steps = [
    {
      id: 1,
      title: "Bem-vindo à Aura Quant",
      description: "Vamos configurar sua conta em alguns passos simples",
      content: (
        <div className="text-center space-y-6">
          <div className="text-6xl mb-4">👋</div>
          <h2 className="text-2xl font-bold">Bem-vindo ao futuro do trading!</h2>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            A Aura Quant é a plataforma líder em trading automatizado no Brasil. 
            Vamos ajudar você a configurar tudo para começar a operar com robôs inteligentes.
          </p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-8">
            <div className="p-4 rounded-lg border border-border/20">
              <div className="text-2xl mb-2">🤖</div>
              <h3 className="font-semibold">Robôs Gratuitos</h3>
              <p className="text-sm text-muted-foreground">Acesso a robôs premium sem custo</p>
            </div>
            <div className="p-4 rounded-lg border border-border/20">
              <div className="text-2xl mb-2">📈</div>
              <h3 className="font-semibold">Performance Superior</h3>
              <p className="text-sm text-muted-foreground">ROI médio de +18.7% ao ano</p>
            </div>
            <div className="p-4 rounded-lg border border-border/20">
              <div className="text-2xl mb-2">🛡️</div>
              <h3 className="font-semibold">Segurança Total</h3>
              <p className="text-sm text-muted-foreground">Certificações bancárias e CVM</p>
            </div>
          </div>
        </div>
      )
    },
    {
      id: 2,
      title: "Configuração de Perfil",
      description: "Defina seu perfil de risco e objetivos",
      content: (
        <div className="space-y-6">
          <h2 className="text-2xl font-bold text-center">Qual é seu perfil de investidor?</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <Card className="p-6 cursor-pointer hover:border-primary transition-colors">
              <div className="text-center">
                <div className="text-4xl mb-3">🛡️</div>
                <h3 className="font-semibold mb-2">Conservador</h3>
                <p className="text-sm text-muted-foreground mb-4">
                  Busca segurança e preservação do capital
                </p>
                <Badge variant="outline" className="border-green-400/20 text-green-400">
                  Baixo Risco
                </Badge>
              </div>
            </Card>
            <Card className="p-6 cursor-pointer hover:border-primary transition-colors">
              <div className="text-center">
                <div className="text-4xl mb-3">⚖️</div>
                <h3 className="font-semibold mb-2">Moderado</h3>
                <p className="text-sm text-muted-foreground mb-4">
                  Equilibra risco e retorno de forma balanceada
                </p>
                <Badge variant="outline" className="border-yellow-400/20 text-yellow-400">
                  Risco Médio
                </Badge>
              </div>
            </Card>
            <Card className="p-6 cursor-pointer hover:border-primary transition-colors">
              <div className="text-center">
                <div className="text-4xl mb-3">🚀</div>
                <h3 className="font-semibold mb-2">Agressivo</h3>
                <p className="text-sm text-muted-foreground mb-4">
                  Busca máximo retorno, aceita volatilidade
                </p>
                <Badge variant="outline" className="border-red-400/20 text-red-400">
                  Alto Risco
                </Badge>
              </div>
            </Card>
          </div>
        </div>
      )
    },
    {
      id: 3,
      title: "Escolha sua Corretora",
      description: "Conecte-se com uma de nossas corretoras parceiras",
      content: (
        <div className="space-y-6">
          <h2 className="text-2xl font-bold text-center">Conectar Corretora</h2>
          <p className="text-center text-muted-foreground">
            Escolha sua corretora para começar a operar
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card className="p-6 cursor-pointer hover:border-primary transition-colors">
              <div className="flex items-center gap-4">
                <div className="text-4xl">🏦</div>
                <div className="flex-1">
                  <h3 className="font-semibold">XP Investimentos</h3>
                  <p className="text-sm text-muted-foreground">Maior corretora do Brasil</p>
                  <Badge className="bg-green-400/10 text-green-400 mt-2">Recomendado</Badge>
                </div>
              </div>
            </Card>
            <Card className="p-6 cursor-pointer hover:border-primary transition-colors">
              <div className="flex items-center gap-4">
                <div className="text-4xl">💰</div>
                <div className="flex-1">
                  <h3 className="font-semibold">Rico Investimentos</h3>
                  <p className="text-sm text-muted-foreground">Foco em trading profissional</p>
                  <Badge variant="outline">Popular</Badge>
                </div>
              </div>
            </Card>
            <Card className="p-6 cursor-pointer hover:border-primary transition-colors">
              <div className="flex items-center gap-4">
                <div className="text-4xl">📈</div>
                <div className="flex-1">
                  <h3 className="font-semibold">Clear Corretora</h3>
                  <p className="text-sm text-muted-foreground">Zero corretagem</p>
                  <Badge variant="outline">Econômico</Badge>
                </div>
              </div>
            </Card>
            <Card className="p-6 cursor-pointer hover:border-primary transition-colors">
              <div className="flex items-center gap-4">
                <div className="text-4xl">🧡</div>
                <div className="flex-1">
                  <h3 className="font-semibold">Inter Investimentos</h3>
                  <p className="text-sm text-muted-foreground">Banco digital</p>
                  <Badge variant="outline">Novo</Badge>
                </div>
              </div>
            </Card>
          </div>
        </div>
      )
    },
    {
      id: 4,
      title: "Selecione seus Robôs",
      description: "Escolha os robôs ideais para seu perfil",
      content: (
        <div className="space-y-6">
          <h2 className="text-2xl font-bold text-center">Robôs Recomendados</h2>
          <p className="text-center text-muted-foreground">
            Baseado no seu perfil, recomendamos estes robôs
          </p>
          <div className="space-y-4">
            <Card className="p-6 cursor-pointer hover:border-primary transition-colors">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center">
                    <span className="text-xl">🤖</span>
                  </div>
                  <div>
                    <h3 className="font-semibold">Alpha Scalper Pro</h3>
                    <p className="text-sm text-muted-foreground">Scalping inteligente • ROI: +12.4%</p>
                    <div className="flex gap-2 mt-2">
                      <Badge variant="outline" className="border-green-400/20 text-green-400">Baixo Risco</Badge>
                      <Badge variant="outline">Recomendado</Badge>
                    </div>
                  </div>
                </div>
                <Button variant="outline">Adicionar</Button>
              </div>
            </Card>
            <Card className="p-6 cursor-pointer hover:border-primary transition-colors">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center">
                    <span className="text-xl">📊</span>
                  </div>
                  <div>
                    <h3 className="font-semibold">Grid Master 3000</h3>
                    <p className="text-sm text-muted-foreground">Grid trading • ROI: +8.9%</p>
                    <div className="flex gap-2 mt-2">
                      <Badge variant="outline" className="border-green-400/20 text-green-400">Conservador</Badge>
                      <Badge variant="outline">Estável</Badge>
                    </div>
                  </div>
                </div>
                <Button variant="outline">Adicionar</Button>
              </div>
            </Card>
          </div>
        </div>
      )
    },
    {
      id: 5,
      title: "Configuração Final",
      description: "Defina capital inicial e configurações finais",
      content: (
        <div className="space-y-6">
          <div className="text-center">
            <div className="text-4xl mb-4">🎉</div>
            <h2 className="text-2xl font-bold">Tudo Pronto!</h2>
            <p className="text-lg text-muted-foreground mb-6">
              Sua conta está configurada e você pode começar a operar
            </p>
          </div>
          
          <Card className="p-6 bg-gradient-card border-border/20">
            <h3 className="font-semibold mb-4">Resumo da Configuração</h3>
            <div className="space-y-3 text-sm">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Perfil de Risco:</span>
                <span>Conservador</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Corretora:</span>
                <span>XP Investimentos</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Robôs Selecionados:</span>
                <span>2</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Capital Inicial:</span>
                <span>R$ 10.000,00</span>
              </div>
            </div>
          </Card>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card className="p-4 text-center">
              <h4 className="font-semibold mb-2">Próximos Passos</h4>
              <p className="text-sm text-muted-foreground">Ative seus robôs no dashboard</p>
            </Card>
            <Card className="p-4 text-center">
              <h4 className="font-semibold mb-2">Suporte 24/7</h4>
              <p className="text-sm text-muted-foreground">Estamos aqui para ajudar</p>
            </Card>
            <Card className="p-4 text-center">
              <h4 className="font-semibold mb-2">Academia</h4>
              <p className="text-sm text-muted-foreground">Aprenda com nossos cursos</p>
            </Card>
          </div>
        </div>
      )
    }
  ];

  const currentStepData = steps.find(step => step.id === currentStep);
  const progress = (currentStep / totalSteps) * 100;

  return (
    <PageLayout>
      <div className="container mx-auto px-6 py-12">
        <div className="max-w-4xl mx-auto">
          {/* Progress Bar */}
          <div className="mb-8">
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm text-muted-foreground">
                Passo {currentStep} de {totalSteps}
              </span>
              <span className="text-sm text-muted-foreground">{Math.round(progress)}%</span>
            </div>
            <Progress value={progress} className="h-2" />
          </div>

          {/* Step Header */}
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold mb-2">{currentStepData?.title}</h1>
            <p className="text-lg text-muted-foreground">{currentStepData?.description}</p>
          </div>

          {/* Step Content */}
          <Card className="p-8 bg-gradient-card border-border/20 mb-8">
            {currentStepData?.content}
          </Card>

          {/* Navigation */}
          <div className="flex justify-between">
            <Button 
              variant="outline" 
              onClick={() => setCurrentStep(Math.max(1, currentStep - 1))}
              disabled={currentStep === 1}
            >
              Anterior
            </Button>
            
            <div className="flex gap-2">
              <Button 
                variant="ghost"
                onClick={() => setCurrentStep(totalSteps)}
              >
                Pular Configuração
              </Button>
              
              {currentStep < totalSteps ? (
                <Button 
                  onClick={() => setCurrentStep(Math.min(totalSteps, currentStep + 1))}
                >
                  Próximo
                </Button>
              ) : (
                <Button 
                  onClick={() => window.location.href = '/dashboard'}
                  className="bg-gradient-primary"
                >
                  Ir para Dashboard
                </Button>
              )}
            </div>
          </div>
        </div>
      </div>
    </PageLayout>
  );
};

export default Onboarding;