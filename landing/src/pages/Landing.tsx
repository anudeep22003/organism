import { Header } from "@/components/Header"
import { Hero } from "@/components/Hero"
import { Etymology } from "@/components/Etymology"
import { Vision } from "@/components/Vision"
import { Product } from "@/components/Product"
import { HowItWorks } from "@/components/HowItWorks"
import { UseCases } from "@/components/UseCases"
import { Pricing } from "@/components/Pricing"
import { Footer } from "@/components/Footer"

export function Landing() {
  return (
    <div className="min-h-screen">
      <Header />
      <main>
        <Hero />
        <Etymology />
        <Vision />
        <Product />
        <HowItWorks />
        <UseCases />
        <Pricing />
      </main>
      <Footer />
    </div>
  )
}
