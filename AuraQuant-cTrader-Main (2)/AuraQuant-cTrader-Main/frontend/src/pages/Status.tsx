import { PageLayout } from "@/components/PageLayout";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

const Status = () => {
  const services = [
    { name: "API Principal", status: "operational", uptime: "99.9%", responseTime: "124ms" },
    { name: "Robôs de Trading", status: "operational", uptime: "99.8%", responseTime: "45ms" },
    { name: "Feed de Dados", status: "operational", uptime: "99.7%", responseTime: "23ms" },
    { name: "Dashboard", status: "operational", uptime: "99.9%", responseTime: "89ms" },
    { name: "Notificações", status: "degraded", uptime: "97.2%", responseTime: "234ms" },
    { name: "Backup Systems", status: "operational", uptime: "100%", responseTime: "12ms" }
  ];

  const incidents = [
    {
      id: 1,
      title: "Lentidão no sistema de notificações",
      status: "investigating",
      date: "2024-01-15",
      time: "14:30",
      description: "Investigando lentidão nas notificações push"
    },
    {
      id: 2,
      title: "Manutenção programada - API",
      status: "scheduled",
      date: "2024-01-20",
      time: "02:00",
      description: "Manutenção de rotina da infraestrutura"
    }
  ];

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'operational': return 'bg-green-400';
      case 'degraded': return 'bg-yellow-400';
      case 'outage': return 'bg-red-400';
      default: return 'bg-gray-400';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'operational': return 'Operacional';
      case 'degraded': return 'Degradado';
      case 'outage': return 'Fora do Ar';
      default: return 'Desconhecido';
    }
  };

  return (
    <PageLayout 
      title="Status do Sistema" 
      description="Monitore a saúde e disponibilidade de todos os nossos serviços em tempo real."
    >
      <div className="container mx-auto px-6 py-12">
        {/* Overall Status */}
        <Card className="p-6 mb-8 bg-gradient-card border-border/20">
          <div className="flex items-center gap-4">
            <div className="w-4 h-4 bg-green-400 rounded-full animate-pulse"></div>
            <div>
              <h2 className="text-xl font-bold">Todos os sistemas operacionais</h2>
              <p className="text-muted-foreground">Última verificação: há 2 minutos</p>
            </div>
          </div>
        </Card>

        {/* Services Status */}
        <div className="mb-8">
          <h2 className="text-2xl font-bold mb-6">Status dos Serviços</h2>
          <div className="space-y-4">
            {services.map((service, index) => (
              <Card key={index} className="p-6 bg-gradient-card border-border/20">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className={`w-3 h-3 ${getStatusColor(service.status)} rounded-full`}></div>
                    <div>
                      <h3 className="font-semibold">{service.name}</h3>
                      <p className="text-sm text-muted-foreground">
                        Uptime: {service.uptime} • Tempo de resposta: {service.responseTime}
                      </p>
                    </div>
                  </div>
                  <Badge 
                    variant={service.status === 'operational' ? 'default' : 'secondary'}
                    className={`${service.status === 'operational' ? 'bg-green-400/10 text-green-400' : 'bg-yellow-400/10 text-yellow-400'}`}
                  >
                    {getStatusText(service.status)}
                  </Badge>
                </div>
              </Card>
            ))}
          </div>
        </div>

        {/* Incidents and Maintenance */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <div>
            <h2 className="text-2xl font-bold mb-6">Incidentes Recentes</h2>
            <div className="space-y-4">
              {incidents.filter(i => i.status === 'investigating').map((incident) => (
                <Card key={incident.id} className="p-6 bg-gradient-card border-border/20">
                  <div className="flex items-start justify-between mb-3">
                    <h3 className="font-semibold">{incident.title}</h3>
                    <Badge variant="destructive" className="bg-red-400/10 text-red-400">
                      Investigando
                    </Badge>
                  </div>
                  <p className="text-sm text-muted-foreground mb-2">{incident.description}</p>
                  <p className="text-xs text-muted-foreground">{incident.date} às {incident.time}</p>
                </Card>
              ))}
            </div>
          </div>

          <div>
            <h2 className="text-2xl font-bold mb-6">Manutenções Programadas</h2>
            <div className="space-y-4">
              {incidents.filter(i => i.status === 'scheduled').map((incident) => (
                <Card key={incident.id} className="p-6 bg-gradient-card border-border/20">
                  <div className="flex items-start justify-between mb-3">
                    <h3 className="font-semibold">{incident.title}</h3>
                    <Badge variant="outline" className="border-blue-400/20 text-blue-400">
                      Agendado
                    </Badge>
                  </div>
                  <p className="text-sm text-muted-foreground mb-2">{incident.description}</p>
                  <p className="text-xs text-muted-foreground">{incident.date} às {incident.time}</p>
                </Card>
              ))}
            </div>
          </div>
        </div>

        {/* Historical Uptime */}
        <Card className="p-6 mt-8 bg-gradient-card border-border/20">
          <h2 className="text-xl font-bold mb-4">Histórico de Uptime (Últimos 90 dias)</h2>
          <div className="flex gap-1">
            {Array.from({ length: 90 }, (_, i) => (
              <div 
                key={i} 
                className={`w-2 h-8 rounded-sm ${
                  Math.random() > 0.05 ? 'bg-green-400' : 'bg-red-400'
                }`}
                title={`Dia ${90 - i}: ${Math.random() > 0.05 ? '100%' : '95%'} uptime`}
              />
            ))}
          </div>
          <div className="flex justify-between text-sm text-muted-foreground mt-2">
            <span>90 dias atrás</span>
            <span>Hoje</span>
          </div>
        </Card>
      </div>
    </PageLayout>
  );
};

export default Status;