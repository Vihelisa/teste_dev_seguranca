import { Navigation } from "@/components/Navigation";
import { Footer } from "@/components/Footer";
import { ReactNode } from "react";

interface PageLayoutProps {
  children: ReactNode;
  title?: string;
  description?: string;
}

export const PageLayout = ({ children, title, description }: PageLayoutProps) => {
  return (
    <div className="min-h-screen flex flex-col">
      <Navigation />
      <main className="pt-20 flex-grow">
        {(title || description) && (
          <div className="bg-gradient-to-b from-background to-muted/10 py-16 border-b border-border/20">
            <div className="container mx-auto px-6 text-center">
              {title && (
                <h1 className="text-4xl md:text-5xl font-bold mb-4">{title}</h1>
              )}
              {description && (
                <p className="text-lg text-muted-foreground max-w-3xl mx-auto">
                  {description}
                </p>
              )}
            </div>
          </div>
        )}
        {children}
      </main>
      <Footer />
    </div>
  );
};