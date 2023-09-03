from dotenv import load_dotenv
import json
import os
import requests

load_dotenv()


# Environment vars. Bearer token must be specified. Field IDs must be overridden if using any marketplace other than scrandyb.myshopify.com
MVM_API_BEARER_TOKEN = os.getenv("MVM_API_BEARER_TOKEN")
FR_EPR_REG_NUMBER_CUSTOM_FIELD_ID = os.getenv("FR_EPR_REG_NUMBER_CUSTOM_FIELD_ID", "22305")
DE_LUCID_REG_NUMBER_CUSTOM_FIELD_ID = os.getenv("DE_LUCID_REG_NUMBER_CUSTOM_FIELD_ID", "22316")


MVM_API_BASE = "https://mvmapi.webkul.com/api/v2/"
AUTH_HEADERS = {"Authorization": "Bearer {}".format(MVM_API_BEARER_TOKEN)}

SELLERS_URL = "{}{}".format(MVM_API_BASE, "sellers.json")
SELLER_SHIPPING_URL = "{}{}".format(MVM_API_BASE, "feature-apps/shipping/{seller_id}.json")
SELLER_SHIPPING_RANGE_PRICE_URL = "{}{}".format(MVM_API_BASE, "feature-apps/shipping/range-price/{seller_id}.json")


class ComplianceViolationException(Exception):
	pass


class Seller:
	"""Information about an individual seller"""

	class SellerShippingDetails:
		"""Shipping details for an individual seller"""

		def __init__(self):
			self.ships_from_country = None
			self.seller_shipping_ids = []
			self.ships_to_countries = []

		@property
		def ships_from_country(self):
			return self._ships_from_country

		@ships_from_country.setter
		def ships_from_country(self, ships_from_country):
			self._ships_from_country = ships_from_country

		@property
		def seller_shipping_ids(self):
			return self._seller_shipping_ids

		@seller_shipping_ids.setter
		def seller_shipping_ids(self, seller_shipping_ids):
			self._seller_shipping_ids = seller_shipping_ids

		def add_seller_shipping_id(self, seller_shipping_id):
			self.seller_shipping_ids.append(seller_shipping_id)

		@property
		def ships_to_countries(self):
			return self._ships_to_countries

		@ships_to_countries.setter
		def ships_to_countries(self, ships_to_countries):
			self._ships_to_countries = ships_to_countries

		def add_ships_to_country(self, country_iso_code):
			self.ships_to_countries.append(country_iso_code)


	class SellerComplianceDetails:
		"""Compliance details for an individual seller, such as EPR registration numbers"""

		def __init__(self):
			self.fr_epr_reg_number = None
			self.de_lucid_reg_number = None

		@property
		def fr_epr_reg_number(self):
			return self._fr_epr_reg_number

		@fr_epr_reg_number.setter
		def fr_epr_reg_number(self, fr_epr_reg_number):
			self._fr_epr_reg_number = fr_epr_reg_number

		@property
		def de_lucid_reg_number(self):
			return self._de_lucid_reg_number
		
		@de_lucid_reg_number.setter
		def de_lucid_reg_number(self, de_lucid_reg_number):
			self._de_lucid_reg_number = de_lucid_reg_number

	def __init__(self):
		self.id = None
		self.compliance_details = Seller.SellerComplianceDetails()
		self.shipping_details = Seller.SellerShippingDetails()

	@property
	def id(self):
		return self._id

	@id.setter
	def id(self, id_val):
		self._id = id_val


class ComplianceCheck:
	"""Parent class for compliance checks, e.g. checking if a seller can sell in FR"""
	@classmethod
	def get_name(cls):
		return cls.__name__

	def run_check(seller):
		raise NotImplementedError("Compliance check has not been implemented for case: {}".format(get_name()))



class SellerCanSellInDE(ComplianceCheck):
	def run_check(seller):
		if (('FR' in seller.shipping_details.ships_to_countries or 'WR' in seller.shipping_details.ships_to_countries)
				and (seller.compliance_details.de_lucid_reg_number is None or seller.compliance_details.de_lucid_reg_number == "")):
			raise ComplianceViolationException("Seller {} failed compliance check {}".format(seller.id, SellerCanSellInDE.get_name()))
		return None

class SellerCanSellInFR(ComplianceCheck):
	def run_check(seller):
		if (('FR' in seller.shipping_details.ships_to_countries or 'WR' in seller.shipping_details.ships_to_countries)
				and (seller.compliance_details.fr_epr_reg_number is None or seller.compliance_details.fr_epr_reg_number == "")):
			raise ComplianceViolationException("Seller {} failed compliance check {}".format(seller.id, SellerCanSellInFR.get_name()))
		return None


class RunComplianceChecks:
	"""Runs all compliance checks for an individual seller"""
	checks_to_run = [SellerCanSellInDE, SellerCanSellInFR]

	def run_all_checks_for_seller(seller):
		seller_check_results = {'checks_passed': [], 'checks_failed': []}
		for check in RunComplianceChecks.checks_to_run:
			try:
				check.run_check(seller)
				seller_check_results['checks_passed'].append(check.get_name())
			except ComplianceViolationException as violation:
				seller_check_results['checks_failed'].append(check.get_name())
		return seller_check_results


def populate_seller_details(seller):
	"""Populates individual seller with all relevant details that aren't available in the sellers.json list response
		
		It kind of sucks that we get a couple seller fields in the list API call, and fill in the rest in this fn.
		It would be better if this fn simply took a seller_id and generated/populated the entire Seller object,
		but due to strict MVM API rate limits, calls are at a premium and this approach minimizes redundant calls.
	"""
	shipping_url = SELLER_SHIPPING_URL.format(seller_id=seller.id)
	seller_shipping_range_url = SELLER_SHIPPING_RANGE_PRICE_URL.format(seller_id=seller.id)
	r_shipping_details = requests.get(shipping_url, headers=AUTH_HEADERS)
	r_shipping_details.raise_for_status()
	if len(r_shipping_details.json()["shipping"]) == 0:
		return
	for shipping_id_json in r_shipping_details.json()["shipping"]["available_shipping"]:
		seller_shipping_id = shipping_id_json["seller_shipping_id"]
		seller.shipping_details.add_seller_shipping_id(seller_shipping_id)

		# get shipping range information for seller_shipping_id
		r_shipping_range = requests.get(seller_shipping_range_url, params={"seller_shipping_id": seller_shipping_id}, headers=AUTH_HEADERS)
		r_shipping_range.raise_for_status()
		for country_range in r_shipping_range.json()['range-price']['country_ranges']:
			country_iso_code = country_range['country_iso_code']
			if country_iso_code not in seller.shipping_details.ships_to_countries:
				seller.shipping_details.add_ships_to_country(country_iso_code)


def get_seller_batch(page_num, page_limit):
	"""Calls MVM API to get a batch of sellers, returns list of Seller objects"""
	r = requests.get(SELLERS_URL, params={"limit": page_limit, "page": page_num}, headers=AUTH_HEADERS)
	r.raise_for_status()
	seller_batch = []
	for seller_json in r.json()["sellers"]:
		seller = Seller()
		seller.id = seller_json["id"]
		seller.shipping_details.ships_from_country = seller_json.get("id_country", {}).get("iso_code")
		custom_fields = json.loads(seller_json.get("custom_fields", ""))
		if custom_fields.get(FR_EPR_REG_NUMBER_CUSTOM_FIELD_ID, {}).get("value"):
			seller.compliance_details.fr_epr_reg_number = custom_fields.get(FR_EPR_REG_NUMBER_CUSTOM_FIELD_ID, {}).get("value")
		if custom_fields.get(DE_LUCID_REG_NUMBER_CUSTOM_FIELD_ID, {}).get("value"):
			seller.compliance_details.de_lucid_reg_number = custom_fields.get(DE_LUCID_REG_NUMBER_CUSTOM_FIELD_ID, {}).get("value")
		seller_batch.append(seller)
	return seller_batch


def check_epr_compliance_for_all_sellers():
	more_sellers = True
	page_limit = 100
	page_num = 1
	max_page_num = 50
	seen_seller_ids = set()
	sellers_with_no_violations = 0
	sellers_with_violations = 0
	seller_check_result_details = {}


	while more_sellers:
		print("Analyzing sellers, page {}".format(page_num))
		seller_batch = get_seller_batch(page_num, page_limit)
		results_in_page = len(seller_batch)
		for seller in seller_batch:
			if seller.id in seen_seller_ids:
				continue

			seen_seller_ids.add(seller.id)
			populate_seller_details(seller)
			seller_check_results = RunComplianceChecks.run_all_checks_for_seller(seller)
			if len(seller_check_results['checks_failed']) == 0:
				sellers_with_no_violations += 1
			else:
				sellers_with_violations  += 1
			seller_check_result_details[seller.id] = seller_check_results

		# we stop after 100 pages (10000 sellers) to stop forever loops (due to bugs etc)
		# TODO should we even do this, or can we rely on our code being good enough?
		if results_in_page < 100 or max_page_num > 50:
			more_sellers = False
		else:
			page_num += 1

	if (page_num / max_page_num) > .5:
		# TODO: if we want to keep using max_page_num, this statement should also push a warning to a notificaiton channel (e.g. email)
		print("Hey, we're getting near the max page limit. You should increase max_page_num value sometime soon")
	for seller_id, check_results in seller_check_result_details.items():
		pass_or_fail = "PASS" if len(check_results['checks_failed']) == 0 else "FAIL"
		print("Seller {} result: {}\nSuccessful tests: {}\nFailed tests: {}\n\n".format(
			seller_id,
			pass_or_fail,
			check_results['checks_passed'],
			check_results['checks_failed']
		))
	print("Finished. Total passed: {}, Total failed: {}".format(sellers_with_no_violations, sellers_with_violations))


if __name__ == "__main__":
	check_epr_compliance_for_all_sellers()
