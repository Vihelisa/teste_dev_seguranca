import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";

export const FaqSection = () => {
  const faqs = [
    {
      question: "Os robôs são realmente gratuitos?",
      answer: "Sim! Nossa plataforma oferece acesso gratuito a uma seleção de robôs verificados. Você pode testar e usar sem custos iniciais. Planos premium oferecem recursos avançados e acesso a robôs exclusivos."
    },
    {
      question: "Qual o valor mínimo para começar?",
      answer: "Não há valor mínimo obrigatório da plataforma. O valor depende apenas dos requisitos da sua corretora. Recomendamos começar com valores que você se sinta confortável para aprender."
    },
    {
      question: "Como posso confiar nos algoritmos?",
      answer: "Todos os robôs passam por rigorosa auditoria antes de serem disponibilizados. Fornecemos histórico completo de performance, backtest detalhado e métricas de risco para cada algoritmo."
    },
    {
      question: "Posso parar o robô a qualquer momento?",
      answer: "Absolutamente! Você tem controle total. Pode pausar, parar ou ajustar configurações a qualquer momento através do dashboard. Não há período de lock-in ou penalidades."
    },
    {
      question: "Quais corretoras são suportadas?",
      answer: "Suportamos as principais corretoras do Brasil incluindo XP, Clear, Rico, BTG, Inter e muitas outras. Nossa API se integra facilmente com a maioria das plataformas."
    },
    {
      question: "Há garantia de lucro?",
      answer: "Não oferecemos garantia de lucro pois o mercado financeiro sempre envolve riscos. Nossos robôs são ferramentas baseadas em análise técnica e estatística, mas resultados passados não garantem resultados futuros."
    },
    {
      question: "Como funciona o suporte técnico?",
      answer: "Oferecemos suporte 24/7 através de chat, email e telefone. Nossa equipe de especialistas está sempre disponível para ajudar com configurações, dúvidas técnicas e estratégias."
    },
    {
      question: "Posso usar múltiplos robôs simultaneamente?",
      answer: "Sim! Você pode executar vários robôs ao mesmo tempo, cada um com suas próprias configurações e estratégias. Isso ajuda na diversificação de risco."
    }
  ];

  return (
    <section className="py-24 bg-gradient-to-b from-background to-muted/10">
      <div className="container mx-auto px-6">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold mb-4">
            Perguntas Frequentes
          </h2>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            Tire suas dúvidas sobre trading automatizado e nossa plataforma
          </p>
        </div>

        <div className="max-w-3xl mx-auto">
          <Accordion type="single" collapsible className="space-y-4">
            {faqs.map((faq, index) => (
              <AccordionItem 
                key={index} 
                value={`item-${index}`}
                className="bg-card rounded-xl border border-border/50 px-6"
              >
                <AccordionTrigger className="text-left hover:no-underline py-6">
                  <span className="font-semibold">{faq.question}</span>
                </AccordionTrigger>
                <AccordionContent className="pb-6 text-muted-foreground leading-relaxed">
                  {faq.answer}
                </AccordionContent>
              </AccordionItem>
            ))}
          </Accordion>
        </div>
      </div>
    </section>
  );
};