import Nav from "@/components/Nav";
import Hero from "@/components/Hero";
import Features from "@/components/Features";
import HowItWorks from "@/components/HowItWorks";
import SystemRequirements from "@/components/SystemRequirements";
import Download from "@/components/Download";
import Footer from "@/components/Footer";

export default function HomePage() {
  return (
    <div className="min-h-screen bg-[#0a0a0a]">
      <Nav />
      <main>
        <Hero />
        <Features />
        <HowItWorks />
        <SystemRequirements />
        <Download />
      </main>
      <Footer />
    </div>
  );
}
