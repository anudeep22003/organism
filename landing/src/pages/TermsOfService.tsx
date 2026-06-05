import { Link } from "react-router"

export function TermsOfService() {
  return (
    <div className="min-h-screen">
      <header className="border-b border-border">
        <div className="max-w-4xl mx-auto px-6 h-16 flex items-center">
          <Link to="/" className="text-lg font-semibold tracking-tight">
            ohgraffy
          </Link>
        </div>
      </header>
      <main className="max-w-4xl mx-auto px-6 py-16">
        <h1 className="text-4xl font-bold mb-2">Terms of Service</h1>
        <p className="text-muted-foreground mb-12">Last updated: June 2026</p>

        <div className="space-y-8 text-muted-foreground leading-relaxed">
          <section>
            <h2 className="text-xl font-semibold text-foreground mb-3">1. Acceptance of Terms</h2>
            <p>
              By accessing or using Ohgraffy ("the Service"), operated by Ohgraffy ("we", "us", "our"),
              you agree to be bound by these Terms of Service. If you do not agree, do not use the Service.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-foreground mb-3">2. Description of Service</h2>
            <p>
              Ohgraffy provides an AI-powered storytelling platform that enables users to create
              comics and visual narratives. The Service includes story generation, character creation,
              panel rendering, and export capabilities.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-foreground mb-3">3. User Accounts</h2>
            <p>
              You must create an account to use the Service. You are responsible for maintaining the
              confidentiality of your account credentials and for all activities under your account.
              You must be at least 13 years old to use the Service.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-foreground mb-3">4. Subscriptions & Payments</h2>
            <p>
              Paid features are available through subscription plans. Payments are processed by Stripe.
              Subscriptions renew automatically unless cancelled before the renewal date. You may cancel
              your subscription at any time through your account settings.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-foreground mb-3">5. Refund Policy</h2>
            <p>
              If you are not satisfied with the Service, you may request a refund within 7 days of your
              initial purchase. Refunds are processed at our discretion. To request a refund, contact us
              at support@ohgraffy.com.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-foreground mb-3">6. User Content</h2>
            <p>
              You retain ownership of content you create using the Service, including stories, characters,
              and generated comics. By using the Service, you grant us a limited license to process your
              content solely for the purpose of providing the Service. You are responsible for ensuring
              that uploaded image references and content do not infringe on third-party rights.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-foreground mb-3">7. Acceptable Use</h2>
            <p>
              You agree not to use the Service to create content that is illegal, harmful, threatening,
              abusive, defamatory, or otherwise objectionable. We reserve the right to suspend or terminate
              accounts that violate these terms.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-foreground mb-3">8. Limitation of Liability</h2>
            <p>
              The Service is provided "as is" without warranties of any kind. We are not liable for any
              indirect, incidental, or consequential damages arising from your use of the Service.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-foreground mb-3">9. Changes to Terms</h2>
            <p>
              We may update these Terms from time to time. Continued use of the Service after changes
              constitutes acceptance of the updated terms. We will notify users of material changes via
              email or in-app notification.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-foreground mb-3">10. Contact</h2>
            <p>
              For questions about these Terms, contact us at{" "}
              <a href="mailto:support@ohgraffy.com" className="underline hover:text-foreground">
                support@ohgraffy.com
              </a>.
            </p>
          </section>
        </div>
      </main>
    </div>
  )
}
