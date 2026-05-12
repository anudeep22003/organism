class RetryableStripeWebhookError(Exception):
    """A webhook could not be fully processed yet and should be retried."""


class NonRetryableStripeWebhookError(Exception):
    """A webhook is invalid or anomalous for local state and should not be retried."""
