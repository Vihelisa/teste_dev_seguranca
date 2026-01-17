import { PageLayout } from "@/components/PageLayout";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";

const Academy = () => {
  const courses = [
    {
      title: "Fundamentos do Trading Automatizado",
      description: "Aprenda os conceitos básicos do trading algorítmico e como começar",
      level: "Iniciante",
      duration: "4 horas",
      lessons: 12,
      progress: 0,
      price: "Gratuito",
      category: "Básico"
    },
    {
      title: "Estratégias de Scalping com IA",
      description: "Domine as técnicas de scalping usando inteligência artificial",
      level: "Intermediário",
      duration: "6 horas",
      lessons: 18,
      progress: 45,
      price: "R$ 197",
      category: "Estratégias"
    },
    {
      title: "Análise de Risco Avançada",
      description: "Aprenda a gerenciar riscos e proteger seu capital",
      level: "Avançado",
      duration: "8 horas",
      lessons: 24,
      progress: 12,
      price: "R$ 297",
      category: "Gestão"
    },
    {
      title: "Desenvolvimento de Robôs Personalizados",
      description: "Crie seus próprios robôs usando nossa API e linguagem Pine Script",
      level: "Avançado",
      duration: "12 horas",
      lessons: 32,
      progress: 0,
      price: "R$ 497",
      category: "Desenvolvimento"
    }
  ];

  const articles = [
    {
      title: "Como Escolher o Robô Ideal para seu Perfil",
      excerpt: "Descubra quais características observar na hora de escolher um robô de trading",
      readTime: "5 min",
      category: "Iniciantes",
      date: "15 Jan 2024"
    },
    {
      title: "10 Erros Comuns no Trading Automatizado",
      excerpt: "Evite os principais erros que podem comprometer seus resultados",
      readTime: "8 min",
      category: "Dicas",
      date: "12 Jan 2024"
    },
    {
      title: "Backtesting: Testando Estratégias Antes de Operar",
      excerpt: "Aprenda a importância dos testes históricos para validar estratégias",
      readTime: "12 min",
      category: "Avançado",
      date: "08 Jan 2024"
    },
    {
      title: "Gerenciamento de Risco em Operações Automáticas",
      excerpt: "Técnicas essenciais para proteger seu capital no trading automatizado",
      readTime: "10 min",
      category: "Gestão",
      date: "05 Jan 2024"
    }
  ];

  const webinars = [
    {
      title: "Mercado de Criptomoedas com Robôs",
      speaker: "Dr. Carlos Silva",
      date: "25 Jan 2024",
      time: "19:00",
      attendees: 1247,
      status: "upcoming"
    },
    {
      title: "Estratégias para Mercado Lateral",
      speaker: "Ana Santos",
      date: "22 Jan 2024",
      time: "20:00",
      attendees: 892,
      status: "recorded"
    },
    {
      title: "Análise Fundamentalista + IA",
      speaker: "Prof. João Mendes",
      date: "18 Jan 2024", 
      time: "19:30",
      attendees: 1456,
      status: "recorded"
    }
  ];

  return (
    <PageLayout 
      title="Academia Aura Quant"
      description="Aprenda trading automatizado com nossos cursos, artigos e webinars exclusivos. Do básico ao avançado."
    >
      <div className="container mx-auto px-6 py-12">
        {/* Hero Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-12">
          <Card className="p-6 text-center bg-gradient-card border-border/20">
            <div className="text-2xl font-bold text-primary mb-2">50+</div>
            <p className="text-muted-foreground">Cursos Disponíveis</p>
          </Card>
          <Card className="p-6 text-center bg-gradient-card border-border/20">
            <div className="text-2xl font-bold text-primary mb-2">15K+</div>
            <p className="text-muted-foreground">Alunos Ativos</p>
          </Card>
          <Card className="p-6 text-center bg-gradient-card border-border/20">
            <div className="text-2xl font-bold text-neon mb-2">4.8⭐</div>
            <p className="text-muted-foreground">Avaliação Média</p>
          </Card>
          <Card className="p-6 text-center bg-gradient-card border-border/20">
            <div className="text-2xl font-bold text-yellow-400 mb-2">200h</div>
            <p className="text-muted-foreground">Conteúdo Total</p>
          </Card>
        </div>

        {/* Courses Section */}
        <section className="mb-16">
          <div className="flex justify-between items-center mb-8">
            <h2 className="text-3xl font-bold">Cursos em Destaque</h2>
            <Button variant="outline">Ver Todos os Cursos</Button>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {courses.map((course, index) => (
              <Card key={index} className="p-6 bg-gradient-card border-border/20 hover:border-primary/20 transition-all duration-300">
                <div className="flex justify-between items-start mb-4">
                  <Badge 
                    variant={course.level === 'Iniciante' ? 'secondary' : course.level === 'Intermediário' ? 'default' : 'destructive'}
                    className={
                      course.level === 'Iniciante' ? 'bg-green-500/10 text-green-400' :
                      course.level === 'Intermediário' ? 'bg-yellow-500/10 text-yellow-400' :
                      'bg-red-500/10 text-red-400'
                    }
                  >
                    {course.level}
                  </Badge>
                  <Badge variant="outline" className="text-xs">
                    {course.category}
                  </Badge>
                </div>

                <h3 className="text-xl font-semibold mb-2">{course.title}</h3>
                <p className="text-muted-foreground mb-4 text-sm">{course.description}</p>

                <div className="grid grid-cols-3 gap-4 mb-4 text-sm">
                  <div>
                    <span className="text-muted-foreground">Duração:</span>
                    <div className="font-medium">{course.duration}</div>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Aulas:</span>
                    <div className="font-medium">{course.lessons}</div>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Preço:</span>
                    <div className={`font-medium ${course.price === 'Gratuito' ? 'text-primary' : ''}`}>
                      {course.price}
                    </div>
                  </div>
                </div>

                {course.progress > 0 && (
                  <div className="mb-4">
                    <div className="flex justify-between text-sm mb-2">
                      <span>Progresso</span>
                      <span>{course.progress}%</span>
                    </div>
                    <Progress value={course.progress} />
                  </div>
                )}

                <div className="flex gap-2">
                  <Button 
                    className={course.progress > 0 ? 'bg-gradient-primary flex-1' : 'flex-1'}
                    variant={course.progress > 0 ? 'default' : 'outline'}
                  >
                    {course.progress > 0 ? 'Continuar' : course.price === 'Gratuito' ? 'Começar' : 'Inscrever-se'}
                  </Button>
                  <Button variant="ghost" size="sm">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
                    </svg>
                  </Button>
                </div>
              </Card>
            ))}
          </div>
        </section>

        {/* Articles Section */}
        <section className="mb-16">
          <div className="flex justify-between items-center mb-8">
            <h2 className="text-3xl font-bold">Artigos Recentes</h2>
            <Button asChild variant="outline">
              <a href="/blog">Ver Blog Completo</a>
            </Button>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {articles.map((article, index) => (
              <Card key={index} className="p-6 bg-gradient-card border-border/20 hover:border-primary/20 transition-all duration-300 cursor-pointer">
                <div className="flex justify-between items-start mb-3">
                  <Badge variant="secondary" className="text-xs">
                    {article.category}
                  </Badge>
                  <span className="text-xs text-muted-foreground">{article.readTime}</span>
                </div>
                
                <h3 className="font-semibold text-lg mb-2">{article.title}</h3>
                <p className="text-muted-foreground mb-4 text-sm">{article.excerpt}</p>
                
                <div className="flex justify-between items-center">
                  <span className="text-xs text-muted-foreground">{article.date}</span>
                  <Button variant="ghost" size="sm">
                    Ler mais →
                  </Button>
                </div>
              </Card>
            ))}
          </div>
        </section>

        {/* Webinars Section */}
        <section>
          <h2 className="text-3xl font-bold mb-8">Webinars e Eventos</h2>
          
          <div className="space-y-4">
            {webinars.map((webinar, index) => (
              <Card key={index} className="p-6 bg-gradient-card border-border/20">
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <h3 className="font-semibold text-lg">{webinar.title}</h3>
                      <Badge 
                        variant={webinar.status === 'upcoming' ? 'default' : 'secondary'}
                        className={webinar.status === 'upcoming' ? 'bg-primary/10 text-primary' : ''}
                      >
                        {webinar.status === 'upcoming' ? 'Em breve' : 'Gravação disponível'}
                      </Badge>
                    </div>
                    
                    <p className="text-sm text-muted-foreground mb-2">
                      Com <span className="font-medium">{webinar.speaker}</span>
                    </p>
                    
                    <div className="flex items-center gap-4 text-sm">
                      <span className="flex items-center gap-1">
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                        </svg>
                        {webinar.date} às {webinar.time}
                      </span>
                      <span className="flex items-center gap-1">
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z" />
                        </svg>
                        {webinar.attendees} participantes
                      </span>
                    </div>
                  </div>
                  
                  <Button 
                    className={webinar.status === 'upcoming' ? 'bg-gradient-primary' : ''}
                    variant={webinar.status === 'upcoming' ? 'default' : 'outline'}
                  >
                    {webinar.status === 'upcoming' ? 'Inscrever-se' : 'Assistir Gravação'}
                  </Button>
                </div>
              </Card>
            ))}
          </div>
        </section>
      </div>
    </PageLayout>
  );
};

export default Academy;