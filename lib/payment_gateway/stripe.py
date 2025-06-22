import logging
from dataclasses import dataclass, field
from typing import Literal, Optional

import stripe

logger = logging.getLogger(__name__)


@dataclass(init=False)
class StripePaymentGateway:
    _client: stripe.StripeClient = field(init=False)

    def __init__(self, api_key: str):
        """Initialize Stripe client after dataclass instantiation"""
        try:
            self._client = stripe.StripeClient(api_key=api_key)
            logger.info("Stripe client initialized successfully")
        except Exception as ex:
            logger.critical("Stripe initialization failed")
            logger.debug(str(ex))
            raise RuntimeError(f"Stripe init failed")

    @property
    def client(self) -> stripe.StripeClient:
        return self._client

    def create_payment_intent(
        self,
        amount: int,
        payment_method_types: list[str],
        currency: str = "usd",
        metadata: Optional[dict] = None,
        customer_id: Optional[str] = None,
    ) -> stripe.PaymentIntent:
        """
        Create a payment intent for a given amount and currency

        Args:
            amount (int): Amount in cents
            payment_method_types (list[str]): List of payment method types (e.g., ['card'])
            currency (str): Currency code (default: 'usd')
            metadata (Optional[dict]): Additional metadata for the payment intent
            customer_id (Optional[str]): Stripe customer ID to associate with the payment intent

        Returns:
            stripe.PaymentIntent: Created PaymentIntent object

        Raises:
            ConnectionError: If the payment intent creation fails
        """
        try:
            intent = self._client.payment_intents.create(
                params={
                    "amount": amount,
                    "currency": currency,
                    "metadata": metadata or {},
                    "customer": customer_id or "",
                    "payment_method_types": payment_method_types,
                },
            )
            logger.info(
                f"PaymentIntent created: {intent.id}",
                extra={"amount": amount, "currency": currency},
            )
            return intent
        except stripe.StripeError as e:
            logger.error(
                "PaymentIntent creation failed",
                extra={"error": str(e), "amount": amount, "currency": currency},
            )
            raise ConnectionError(f"Failed to create PaymentIntent") from e

    def confirm_payment_intent(
        self,
        payment_intent_id: str,
        payment_method: Optional[str] = None,
    ) -> stripe.PaymentIntent:
        """
        Confirm a payment intent with an optional payment method

        Args:
            payment_intent_id (str): ID of the PaymentIntent to confirm
            payment_method (Optional[str]): ID of the payment method to use for confirmation

        Returns:
            stripe.PaymentIntent: Confirmed PaymentIntent object

        Raises:
            ConnectionError: If the payment intent confirmation fails
        """
        try:
            intent = self.client.payment_intents.confirm(
                intent=payment_intent_id,
                params={
                    "payment_method": payment_method or "",
                },
            )
            logger.info(f"PaymentIntent confirmed: {payment_intent_id}")
            return intent
        except stripe.StripeError as e:
            logger.error(
                f"PaymentIntent confirmation failed: {payment_intent_id}",
            )
            logger.debug(str(e))
            raise ConnectionError(f"Failed to confirm PaymentIntent: {payment_intent_id}") from e

    def create_refund(
        self,
        payment_intent_id: str,
        amount: int,
        reason: Literal["duplicate", "fraudulent", "requested_by_customer"],
    ) -> stripe.Refund:
        """
        Create a refund for a given payment intent

        Args:
            payment_intent_id (str): ID of the PaymentIntent to refund
            amount (int): Amount to refund in cents
            reason (Literal["duplicate", "fraudulent", "requested_by_customer"]): Reason for the refund

        Returns:
            stripe.Refund: Created Refund object

        Raises:
            ConnectionError: If the refund creation fails
        """
        try:
            refund = self.client.refunds.create(
                params={
                    "payment_intent": payment_intent_id,
                    "amount": amount,
                    "reason": reason,
                },
            )
            logger.info(
                f"Refund created for payment: {payment_intent_id}- Refund id: {refund.id} - Amount: {amount}, Reason: {reason}",
            )
            return refund
        except stripe.StripeError as e:
            logger.error(
                f"Refund failed for payment: {payment_intent_id}",
                extra={"error": str(e)},
            )
            logger.debug(str(e))
            raise ConnectionError(f"Failed to create refund for PaymentIntent: {payment_intent_id}") from e

    def get_payment_intent(self, payment_intent_id: str) -> stripe.PaymentIntent:
        """
        Retrieve a PaymentIntent by its ID
        Args:
            payment_intent_id (str): ID of the PaymentIntent to retrieve
        Returns:
            stripe.PaymentIntent: Retrieved PaymentIntent object

        Raises:
            ConnectionError: If the retrieval fails
        """
        try:
            return self.client.payment_intents.retrieve(payment_intent_id)
        except stripe.StripeError as e:
            logger.error(f"Failed to retrieve PaymentIntent: {payment_intent_id}")
            logger.debug(str(e))
            raise ConnectionError(f"Failed to retrieve PaymentIntent: {payment_intent_id}") from e
