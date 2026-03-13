import unittest
from unittest.mock import Mock

from src.models import CartItem, Order
from src.pricing import PricingService, PricingError
from src.checkout import CheckoutService, ChargeResult

class TestCheckoutService(unittest.TestCase):

	def setUp(self):
		self.payments = Mock()
		self.email = Mock()
		self.fraud = Mock()
		self.repo = Mock()
		self.pricing = Mock()
		self.checkout = CheckoutService(
			payments=self.payments,
			email=self.email,
			fraud=self.fraud,
			repo=self.repo,
			pricing=self.pricing,
		)

	def test_checkout_success(self):

		user_id = "diego"
		items = [CartItem("sku1", 1000, 2)]
		payment_token = "mastercard"
		country = "CL"
		self.pricing.total_cents.return_value = 2380
		self.fraud.score.return_value = 10
		charge_result = ChargeResult(ok=True, charge_id="ch_1", reason=None)
		self.payments.charge.return_value = charge_result

		result = self.checkout.checkout(user_id, items, payment_token, country)

		# estos para ver si fueron llamados 1 vez y con los argumentos bien
		self.pricing.total_cents.assert_called_once_with(items, None, country)
		self.fraud.score.assert_called_once_with(user_id, 2380)
		self.payments.charge.assert_called_once_with(user_id=user_id, amount_cents=2380, payment_token=payment_token)
		self.repo.save.assert_called_once()
		self.email.send_receipt.assert_called_once()

		# este pa ver si llega correctamente el resultado
		self.assertTrue(result.startswith("OK:"))

	def test_checkout_invalid_user(self):

		user_id = "   "  # usuario inválido
		items = [CartItem("sku1", 1000, 2)]
		payment_token = "mastercard"
		country = "CL"


		result = self.checkout.checkout(user_id, items, payment_token, country)


		self.assertEqual(result, "INVALID_USER")

	def test_checkout_invalid_cart(self):
		user_id = "diego"
		items = [CartItem("sku1", 1000, 0)]  # qty inválida
		payment_token = "mastercard"
		country = "CL"
		self.pricing.total_cents.side_effect = PricingError("qty must be > 0")

		result = self.checkout.checkout(user_id, items, payment_token, country)

		self.assertEqual(result, "INVALID_CART:qty must be > 0")

	def test_checkout_rejected_fraud(self):
		user_id = "diego"
		items = [CartItem("sku1", 1000, 2)]
		payment_token = "mastercard"
		country = "CL"
		self.pricing.total_cents.return_value = 2380
		self.fraud.score.return_value = 85  # score alto

		result = self.checkout.checkout(user_id, items, payment_token, country)

		self.assertEqual(result, "REJECTED_FRAUD")

	def test_checkout_payment_failed(self):
		user_id = "diego"
		items = [CartItem("sku1", 1000, 2)]
		payment_token = "mastercard"
		country = "CL"
		self.pricing.total_cents.return_value = 2380
		self.fraud.score.return_value = 10
		charge_result = ChargeResult(ok=False, charge_id=None, reason="card_declined")
		self.payments.charge.return_value = charge_result

		result = self.checkout.checkout(user_id, items, payment_token, country)

		self.assertEqual(result, "PAYMENT_FAILED:card_declined")
