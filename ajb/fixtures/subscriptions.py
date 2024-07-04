import time
from ajb.base.models import RequestScope
from ajb.contexts.billing.billing_models import SubscriptionPlan
from ajb.contexts.billing.usecase.billing_usecase import CompanyBillingUsecase
from ajb.vendor.stripe.mock_repository import MockStripeRepository
from ajb.vendor.stripe.models import (
    InvoicePaymentSucceeded,
    StripeCheckoutSessionCompleted,
)


class SubscriptionFixture:
    def setup_company_subscription(self, request_scope: RequestScope, company_id: str):
        mock_stripe = MockStripeRepository()
        billing = CompanyBillingUsecase(request_scope, stripe=mock_stripe)
        billing.start_create_subscription(
            company_id, SubscriptionPlan.GOLD, appsumo_code=""
        )
        billing.complete_create_subscription(
            StripeCheckoutSessionCompleted(**mock_stripe.create_session())
        )
        billing.company_completes_update_subscription(
            InvoicePaymentSucceeded(
                id="1",
                created=1622547800,
                effective_at=int(round(time.time())),
                amount_due=1000,
                amount_paid=1000,
                customer="1",
                customer_email="rcg@example.com",
                customer_name="recruiting guy",
                hosted_invoice_url="invoices.test.com",
                livemode=False,
                paid=True,
                status="paid",
                billing_reason="subscription_create",
                subscription="sub_1234567890",
            )
        )
        return True
