import unittest
from unittest.mock import Mock

from src.models import CartItem, Order
from src.pricing import PricingService, PricingError

class TestPricingService(unittest.TestCase):
	
	def setUp(self):
		self.pricing = PricingService()

	def test_subtotal_cents_valid(self):
		items = [
			CartItem("sku1", 1000, 2),  # 2000
			CartItem("sku2", 500, 3),   # 1500
		]
		result = self.pricing.subtotal_cents(items)
		self.assertEqual(result, 3500)

	def test_subtotal_cents_invalid_qty(self):
		items = [
			CartItem("sku1", 1000, 2),
			CartItem("sku2", 500, 0),   # qty inválida
		]
		with self.assertRaises(PricingError) as err:
			self.pricing.subtotal_cents(items)
		self.assertEqual(str(err.exception), "qty must be > 0")
	
	def test_subtotal_cents_invalid_price(self):
		items = [
			CartItem("sku1", 1000, 2),
			CartItem("sku2", -500, 3),   # unit_price_cents inválido
		]
		with self.assertRaises(PricingError) as err:
			self.pricing.subtotal_cents(items)
		self.assertEqual(str(err.exception), "unit_price_cents must be >= 0")

	def test_apply_coupon_valid(self):
		self.assertEqual(self.pricing.apply_coupon(10000, None), 10000)
		self.assertEqual(self.pricing.apply_coupon(10000, ""), 10000)
		self.assertEqual(self.pricing.apply_coupon(10000, "   "), 10000)
		self.assertEqual(self.pricing.apply_coupon(10000, "SAVE10"), 9000)
		self.assertEqual(self.pricing.apply_coupon(10000, "CLP2000"), 8000)
		self.assertEqual(self.pricing.apply_coupon(1500, "CLP2000"), 0)

	def test_apply_coupon_otro(self):
		with self.assertRaises(PricingError) as err:
			self.pricing.apply_coupon(10000, "100%RealNoFakeCoupon")
		self.assertEqual(str(err.exception), "invalid coupon")
	
	def test_tax_cents_valid(self):
		self.assertEqual(self.pricing.tax_cents(10000, "CL"), 1900)
		self.assertEqual(self.pricing.tax_cents(10000, "EU"), 2100)
		self.assertEqual(self.pricing.tax_cents(10000, "US"), 0)

	def test_tax_cents_unsupported_country(self):
		with self.assertRaises(PricingError) as err:
			self.pricing.tax_cents(10000, "XX")
		self.assertEqual(str(err.exception), "unsupported country")
	
	def test_shipping_cents_valid(self):
		self.assertEqual(self.pricing.shipping_cents(20000, "CL"), 0)
		self.assertEqual(self.pricing.shipping_cents(5000, "CL"), 2500)
		self.assertEqual(self.pricing.shipping_cents(20000, "EU"), 5000)
		self.assertEqual(self.pricing.shipping_cents(5000, "EU"), 5000)
		self.assertEqual(self.pricing.shipping_cents(20000, "US"), 5000)
		self.assertEqual(self.pricing.shipping_cents(5000, "US"), 5000)
	
	def test_shipping_cents_unsupported_country(self):
		with self.assertRaises(PricingError) as err:
			self.pricing.shipping_cents(10000, "AUS")
		self.assertEqual(str(err.exception), "unsupported country")
	
	def test_total_cents_valid(self):
		items = [
			CartItem("sku1", 1000, 2),  # 2000
			CartItem("sku2", 500, 3),   # 1500
		]
		result = self.pricing.total_cents(items, "SAVE10", "CL")
		# subtotal: 3500; net_subtotal: 3150; tax: 598; shipping: 2500; total: 6248
		self.assertEqual(result, 6248)