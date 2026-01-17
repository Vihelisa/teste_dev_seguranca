import { useState, useEffect } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

interface TourStep {
  id: number;
  title: string;
  content: string;
  target: string;
  position: "top" | "bottom" | "left" | "right";
}

interface OnboardingTourProps {
  isVisible: boolean;
  onComplete: () => void;
  onSkip: () => void;
}

export const OnboardingTour = ({ isVisible, onComplete, onSkip }: OnboardingTourProps) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [tourPosition, setTourPosition] = useState({ top: 0, left: 0 });

  const tourSteps: TourStep[] = [
    {
      id: 1,
      title: "Bem-vindo ao Dashboard!",
      content: "Este é seu painel de controle principal. Aqui você pode monitorar todos os seus robôs e operações.",
      target: "dashboard-header",
      position: "bottom"
    },
    {
      id: 2,
      title: "Estatísticas em Tempo Real",
      content: "Acompanhe seu saldo, lucro diário, robôs ativos e taxa de acerto em tempo real.",
      target: "stats-section",
      position: "bottom"
    },
    {
      id: 3,
      title: "Gerenciar Robôs",
      content: "Controle seus robôs ativos, pause ou inicie estratégias e monitore a performance individual.",
      target: "robots-section",
      position: "right"
    },
    {
      id: 4,
      title: "Histórico de Operações",
      content: "Veja todas as operações realizadas pelos seus robôs com detalhes de lucro e horário.",
      target: "trades-section",
      position: "left"
    },
    {
      id: 5,
      title: "Gráfico de Performance",
      content: "Acompanhe a evolução da sua carteira com gráficos interativos de performance.",
      target: "chart-section",
      position: "top"
    }
  ];

  const currentStepData = tourSteps[currentStep];

  useEffect(() => {
    if (isVisible && currentStepData) {
      const targetElement = document.getElementById(currentStepData.target);
      if (targetElement) {
        const rect = targetElement.getBoundingClientRect();
        const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
        
        let top = rect.top + scrollTop;
        let left = rect.left;

        // Adjust position based on desired placement
        switch (currentStepData.position) {
          case "bottom":
            top = rect.bottom + scrollTop + 10;
            left = rect.left + rect.width / 2 - 200; // Center horizontally
            break;
          case "top":
            top = rect.top + scrollTop - 150;
            left = rect.left + rect.width / 2 - 200;
            break;
          case "right":
            top = rect.top + scrollTop + rect.height / 2 - 75;
            left = rect.right + 10;
            break;
          case "left":
            top = rect.top + scrollTop + rect.height / 2 - 75;
            left = rect.left - 410;
            break;
        }

        // Ensure tooltip stays within viewport
        const maxLeft = window.innerWidth - 420;
        const maxTop = window.innerHeight + scrollTop - 200;
        
        left = Math.max(10, Math.min(left, maxLeft));
        top = Math.max(scrollTop + 10, Math.min(top, maxTop));

        setTourPosition({ top, left });

        // Scroll to element with some offset
        window.scrollTo({
          top: rect.top + scrollTop - 100,
          behavior: 'smooth'
        });
      }
    }
  }, [currentStep, isVisible, currentStepData]);

  if (!isVisible || !currentStepData) return null;

  const nextStep = () => {
    if (currentStep < tourSteps.length - 1) {
      setCurrentStep(currentStep + 1);
    } else {
      onComplete();
    }
  };

  const prevStep = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  return (
    <>
      {/* Overlay */}
      <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40" onClick={onSkip} />
      
      {/* Spotlight effect on target element */}
      <style>
        {`
          #${currentStepData.target} {
            position: relative;
            z-index: 45;
            box-shadow: 0 0 0 4px hsl(var(--primary)), 0 0 0 9999px rgba(0, 0, 0, 0.5);
            border-radius: 8px;
          }
        `}
      </style>

      {/* Tour Card */}
      <Card 
        className="fixed w-96 p-6 bg-background border-primary/20 shadow-xl z-50 animate-fade-in"
        style={{
          top: `${tourPosition.top}px`,
          left: `${tourPosition.left}px`,
        }}
      >
        <div className="flex items-center justify-between mb-4">
          <Badge variant="outline" className="bg-primary/10 text-primary">
            {currentStep + 1} de {tourSteps.length}
          </Badge>
          <Button
            variant="ghost"
            size="sm"
            onClick={onSkip}
            className="h-6 w-6 p-0"
          >
            ✕
          </Button>
        </div>

        <h3 className="text-lg font-semibold mb-2">{currentStepData.title}</h3>
        <p className="text-muted-foreground mb-6">{currentStepData.content}</p>

        <div className="flex justify-between">
          <Button
            variant="ghost"
            onClick={prevStep}
            disabled={currentStep === 0}
            size="sm"
          >
            Anterior
          </Button>
          
          <div className="flex gap-2">
            <Button variant="outline" onClick={onSkip} size="sm">
              Pular Tour
            </Button>
            <Button onClick={nextStep} size="sm">
              {currentStep === tourSteps.length - 1 ? 'Finalizar' : 'Próximo'}
            </Button>
          </div>
        </div>

        {/* Progress dots */}
        <div className="flex justify-center gap-2 mt-4">
          {tourSteps.map((_, index) => (
            <div
              key={index}
              className={`w-2 h-2 rounded-full transition-colors ${
                index === currentStep ? 'bg-primary' : 'bg-muted'
              }`}
            />
          ))}
        </div>
      </Card>
    </>
  );
};