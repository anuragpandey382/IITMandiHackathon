   // src/app/layout.tsx (Basic ShadCN setup is already done by init)
  
   import type { Metadata } from "next";
   import { Inter } from "next/font/google";
   import "./globals.css";
  //  import { ThemeProvider } from "@/components/theme-provider"; // Optional: For dark/light mode
   import { Toaster as SonnerToaster } from "@/components/ui/sonner" // Use Sonner for toasts

   const inter = Inter({ subsets: ["latin"] });

   export const metadata: Metadata = {
     title: "MATFix AI",
      description: "AI-powered MATLAB troubleshooting assistant",
   };

   export default function RootLayout({
     children,
   }: Readonly<{
     children: React.ReactNode;
   }>) {
     return (
       <html lang="en" suppressHydrationWarning>
         <body className={inter.className} suppressHydrationWarning>
           {/* Optional ThemeProvider for dark/light mode */}
           {/* <ThemeProvider
             attribute="class"
             defaultTheme="system"
             enableSystem
             disableTransitionOnChange
           > */}
             {children}
             <SonnerToaster position="top-right" richColors />
           {/* </ThemeProvider> */}
         </body>
       </html>
     );
   }