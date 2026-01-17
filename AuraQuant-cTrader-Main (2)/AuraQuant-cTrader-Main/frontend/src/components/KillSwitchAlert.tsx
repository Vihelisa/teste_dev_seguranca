import { useEffect, useState } from "react";
import { AlertTriangle, ShieldAlert } from "lucide-react";
import apiClient from "@/api/client";
import { useAuth } from "@/contexts/AuthContext";

export const KillSwitchAlert = () => {
  const { isAuthenticated } = useAuth();
  const [status, setStatus] = useState<{ status: string; message: string } | null>(null);

  useEffect(() => {
    if (!isAuthenticated) return;

    const checkStatus = async () => {
      try {
        const response = await apiClient.get("/safety-status/");
        if (response.data.status === "CRITICAL") {
          setStatus(response.data);
        } else {
          setStatus(null);
        }
      } catch (error) {
        console.error("Erro ao verificar status de segurança:", error);
      }
    };

    checkStatus();
    const interval = setInterval(checkStatus, 30000); // Check every 30 seconds

    return () => clearInterval(interval);
  }, [isAuthenticated]);

  if (!status) return null;

  return (
    <div className="bg-destructive/15 border-b border-destructive/30 p-4">
      <div className="container mx-auto flex items-center gap-3 text-destructive">
        <ShieldAlert className="h-6 w-6 animate-pulse" />
        <div>
          <h3 className="font-bold">GUARDIÃO ATIVADO - SISTEMA PARADO</h3>
          <p className="text-sm opacity-90">{status.message}</p>
        </div>
      </div>
    </div>
  );
};
