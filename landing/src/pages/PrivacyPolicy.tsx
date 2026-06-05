import { Link } from "react-router"

export function PrivacyPolicy() {
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
        <h1 className="text-4xl font-bold mb-2">Privacy Policy</h1>
        <p className="text-muted-foreground mb-12">Last updated: June 2026</p>

        <div className="space-y-8 text-muted-foreground leading-relaxed">
          <section>
            <h2 className="text-xl font-semibold text-foreground mb-3">1. Information We Collect</h2>
            <p>
              We collect information you provide when creating an account (name, email address via Google OAuth),
              content you create using the Service (stories, image references, generated comics), and usage data
              (pages visited, features used) to improve the Service.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-foreground mb-3">2. How We Use Your Information</h2>
            <p>
              We use your information to provide and improve the Service, process payments, communicate with
              you about your account, and ensure compliance with our Terms of Service. We do not sell your
              personal information to third parties.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-foreground mb-3">3. Third-Party Services</h2>
            <p>
              We use the following third-party services to operate Ohgraffy:
            </p>
            <ul className="list-disc pl-6 mt-2 space-y-1">
              <li>Google OAuth for authentication</li>
              <li>Stripe for payment processing</li>
              <li>Google Cloud Platform for hosting and storage</li>
              <li>PostHog for product analytics</li>
              <li>OpenAI for AI-powered story generation</li>
            </ul>
            <p className="mt-2">
              Each service has its own privacy policy governing how they handle your data.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-foreground mb-3">4. Data Storage & Security</h2>
            <p>
              Your data is stored securely on Google Cloud Platform. We use encryption in transit and at rest
              to protect your information. Image references and generated content are stored in secure cloud
              storage buckets.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-foreground mb-3">5. Your Rights</h2>
            <p>
              You may request access to, correction of, or deletion of your personal data at any time by
              contacting us. You may delete your account and all associated data through your account settings
              or by emailing us.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-foreground mb-3">6. Cookies</h2>
            <p>
              We use essential cookies for authentication and session management. We use analytics cookies
              (PostHog) to understand how the Service is used. You can disable non-essential cookies in your
              browser settings.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-foreground mb-3">7. Children's Privacy</h2>
            <p>
              The Service is not directed at children under 13. We do not knowingly collect personal
              information from children under 13. If you believe a child has provided us personal information,
              contact us to have it removed.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-foreground mb-3">8. Changes to This Policy</h2>
            <p>
              We may update this Privacy Policy from time to time. We will notify you of material changes
              via email or in-app notification. Continued use of the Service constitutes acceptance of the
              updated policy.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-foreground mb-3">9. Contact</h2>
            <p>
              For questions about this Privacy Policy, contact us at{" "}
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
