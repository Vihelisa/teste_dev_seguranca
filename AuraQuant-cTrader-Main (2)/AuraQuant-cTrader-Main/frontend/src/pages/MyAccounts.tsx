import { PageLayout } from "@/components/PageLayout";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Trash2, Settings, Eye, Plus } from "lucide-react";
import { useState, FormEvent } from "react";
import { createAccount, getAccounts } from "@/api";
import { useToast } from "@/hooks/use-toast";
import { useQuery, useQueryClient } from "@tanstack/react-query";

const MyAccounts = () => {
  const [showAddForm, setShowAddForm] = useState(false);
  const [showOpenAccount, setShowOpenAccount] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [formData, setFormData] = useState({
    nickname: '',
    server: '',
    account_login: '',
    password: ''
  });

  const { data: accounts = [], isLoading: isLoadingAccounts } = useQuery({
    queryKey: ['accounts'],
    queryFn: getAccounts
  });

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { id, value } = e.target;
    setFormData(prev => ({ ...prev, [id]: value }));
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setIsLoading(true);

    const accountData = {
      ...formData,
      account_login: parseInt(formData.account_login, 10)
    };
    
    if (isNaN(accountData.account_login)) {
        toast({
            title: "Erro de Validação",
            description: "O login da conta deve ser um número.",
            variant: "destructive",
        });
        setIsLoading(false);
        return;
    }

    try {
      await createAccount(accountData);
      toast({
        title: "Sucesso!",
        description: "Sua conta foi adicionada e validada.",
      });
      setShowAddForm(false);
      setFormData({ nickname: '', server: '', account_login: '', password: '' });
      queryClient.invalidateQueries({ queryKey: ['accounts'] });
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || "Ocorreu um erro ao conectar sua conta. Verifique suas credenciais e tente novamente.";
      toast({
        title: "Erro ao Conectar Conta",
        description: errorMessage,
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <PageLayout 
      title="Minhas Contas de Trading"
      description="Gerencie suas contas de trading conectadas à plataforma Aura Quant."
      showFooter={false}
    >
      <div className="container mx-auto px-6 py-12">
        {/* Account Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
          {isLoadingAccounts && <p>Carregando contas...</p>}
          {!isLoadingAccounts && accounts.map((account) => (
            <Card key={account.id} className="p-6 bg-gradient-card border-border/20">
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h3 className="font-semibold text-lg">{account.nickname}</h3>
                  <p className="text-sm text-muted-foreground">Login: {account.account_login}</p>
                </div>
              </div>

              <div className="space-y-2 mb-4">
                <div className="flex justify-between">
                  <span className="text-sm text-muted-foreground">Servidor:</span>
                  <span className="text-sm font-medium">{account.server}</span>
                </div>
              </div>

              <div className="flex gap-2">
                <Button variant="outline" size="sm" className="flex-1">
                  <Settings className="w-4 h-4 mr-2" />
                  Config
                </Button>
                <Button variant="outline" size="sm" className="flex-1">
                  <Eye className="w-4 h-4 mr-2" />
                  Detalhes
                </Button>
                <Button variant="outline" size="sm" className="text-red-400 hover:text-red-300">
                  <Trash2 className="w-4 h-4" />
                </Button>
              </div>
            </Card>
          ))}
        </div>

        {/* Add Account Button */}
        <div className="text-center mb-8">
          <Button
            onClick={() => setShowAddForm(!showAddForm)}
            className="bg-gradient-primary"
          >
            <Plus className="w-4 h-4 mr-2" />
            Adicionar Conta
          </Button>
        </div>

        {/* Add Account Form */}
        {showAddForm && (
          <Card className="p-6 bg-gradient-card border-border/20 mb-8">
            <form onSubmit={handleSubmit}>
              <h3 className="text-lg font-semibold mb-4">Adicionar Nova Conta</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="broker">Corretora</Label>
                  <Select defaultValue="fp-markets" disabled>
                    <SelectTrigger>
                      <SelectValue placeholder="Selecione a corretora" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="fp-markets">FP Markets</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label htmlFor="nickname">Apelido da Conta</Label>
                  <Input
                    id="nickname"
                    placeholder="Ex: Minha Conta Principal"
                    type="text"
                    value={formData.nickname}
                    onChange={handleInputChange}
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="account_login">Login da Conta (Número)</Label>
                  <Input
                    id="account_login"
                    placeholder="Ex: 123456789"
                    type="text"
                    value={formData.account_login}
                    onChange={handleInputChange}
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="server">Servidor</Label>
                  <Input
                    id="server"
                    placeholder="Ex: FPMarkets-Live"
                    type="text"
                    value={formData.server}
                    onChange={handleInputChange}
                    required
                  />
                </div>
                <div className="md:col-span-2">
                  <Label htmlFor="password">Senha da Conta (somente leitura)</Label>
                  <Input
                    id="password"
                    placeholder="Sua senha da conta"
                    type="password"
                    value={formData.password}
                    onChange={handleInputChange}
                    required
                  />
                </div>
              </div>
              <div className="flex gap-2 mt-4">
                <Button type="submit" className="bg-gradient-primary" disabled={isLoading}>
                  {isLoading ? 'Conectando...' : 'Conectar Conta'}
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setShowAddForm(false)}
                  disabled={isLoading}
                >
                  Cancelar
                </Button>
              </div>
            </form>
          </Card>
        )}

        {/* No Account Message */}
        <Card className="p-8 bg-gradient-card border-border/20 text-center">
          <h3 className="text-xl font-semibold mb-4">Não tem uma conta de trading?</h3>
          <p className="text-muted-foreground mb-6">
            Abra uma conta gratuita com nosso parceiro FP Markets e comece a operar em minutos.
          </p>
          <Button
            onClick={() => setShowOpenAccount(!showOpenAccount)}
            size="lg"
            className="bg-gradient-primary"
          >
            Abrir Conta
          </Button>

          {showOpenAccount && (
            <div className="mt-6 p-6 bg-muted/20 rounded-lg">
              <h4 className="font-semibold mb-4">FP Markets - Conta Gratuita</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-left">
                <div>
                  <h5 className="font-medium mb-2">Benefícios:</h5>
                  <ul className="space-y-1 text-sm text-muted-foreground">
                    <li>• Conta demo com US$ 100.000</li>
                    <li>• Spreads a partir de 0.0 pips</li>
                    <li>• Execução ECN ultra-rápida</li>
                    <li>• Regulamentação ASIC e CySEC</li>
                  </ul>
                </div>
                <div>
                  <h5 className="font-medium mb-2">Instrumentos:</h5>
                  <ul className="space-y-1 text-sm text-muted-foreground">
                    <li>• 70+ Pares de moedas</li>
                    <li>• Índices globais</li>
                    <li>• Commodities</li>
                    <li>• Criptomoedas</li>
                  </ul>
                </div>
              </div>
              <div className="mt-4">
                <Button asChild className="w-full md:w-auto">
                  <a href="https://www.fpmarkets.com" target="_blank" rel="noopener noreferrer">
                    Abrir Conta na FP Markets
                  </a>
                </Button>
              </div>
            </div>
          )}
        </Card>
      </div>
    </PageLayout>
  );
};

export default MyAccounts;