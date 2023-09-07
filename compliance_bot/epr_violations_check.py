"""EPR Violations Bot

Evaluates all sellers in the MVM for EPR violdations.
"""

import json
import os

from dotenv import load_dotenv

from exceptions import ComplianceViolationException
from requests_session import requests_retry_session
from seller import Seller

load_dotenv()

# Environment vars. Bearer token must be specified. Field IDs must be overridden if using any marketplace other than scrandyb.myshopify.com
MVM_API_BEARER_TOKEN = os.getenv("MVM_API_BEARER_TOKEN")
FR_EPR_REG_NUMBER_CUSTOM_FIELD_ID = os.getenv("FR_EPR_REG_NUMBER_CUSTOM_FIELD_ID", "22305")
DE_LUCID_REG_NUMBER_CUSTOM_FIELD_ID = os.getenv("DE_LUCID_REG_NUMBER_CUSTOM_FIELD_ID", "22316")


MVM_API_BASE = "https://mvmapi.webkul.com/api/v2/"


SELLERS_URL = f"{MVM_API_BASE}{'sellers.json'}"
SELLER_SHIPPING_URL = f"{MVM_API_BASE}{'feature-apps/shipping/{seller_id}.json'}"
SELLER_SHIPPING_RANGE_PRICE_URL = \
    f"{MVM_API_BASE}{'feature-apps/shipping/range-price/{seller_id}.json'}"


session = requests_retry_session(bearer_token=MVM_API_BEARER_TOKEN)


class ComplianceCheck:
    """Parent class for compliance checks, e.g. checking if a seller can sell in FR"""
    @classmethod
    def get_name(cls):
        return cls.__name__

    @classmethod
    def run_check(cls, seller):
        raise NotImplementedError(
            f"Compliance check has not been implemented for case: {cls.get_name()}"
        )


# Compliance checks

class SellerCanSellInDE(ComplianceCheck):
    @classmethod
    def run_check(cls, seller):
        if (
                ('FR' in seller.shipping_details.ships_to_countries \
                    or 'WR' in seller.shipping_details.ships_to_countries
                )
                and (seller.compliance_details.de_lucid_reg_number is None \
                    or seller.compliance_details.de_lucid_reg_number == "")):
            raise ComplianceViolationException(
                f"Seller {seller.id} failed compliance check {cls.get_name()}"
            )

class SellerCanSellInFR(ComplianceCheck):
    @classmethod
    def run_check(cls, seller):
        if (
                ('FR' in seller.shipping_details.ships_to_countries \
                    or 'WR' in seller.shipping_details.ships_to_countries)
                and (seller.compliance_details.fr_epr_reg_number is None \
                    or seller.compliance_details.fr_epr_reg_number == "")):
            raise ComplianceViolationException(
                f"Seller {seller.id} failed compliance check {cls.get_name()}"
            )

class RunComplianceChecks:
    """Runs all compliance checks for an individual seller"""
    checks_to_run = [SellerCanSellInDE, SellerCanSellInFR]

    @staticmethod
    def run_all_checks_for_seller(seller):
        seller_check_results = {'checks_passed': [], 'checks_failed': []}
        for check in RunComplianceChecks.checks_to_run:
            try:
                check.run_check(seller)
                seller_check_results['checks_passed'].append(check.get_name())
            except ComplianceViolationException:
                seller_check_results['checks_failed'].append(check.get_name())
        return seller_check_results


def populate_seller_details(seller):
    """Populates seller with all details that aren't available in the sellers.json list response

        It kind of sucks that we get a couple seller fields in the list API call, and fill in the
        rest in this fn. It would be better if this fn simply took a seller_id and
        generated/populated the entire Seller object,
        but due to strict MVM API rate limits, calls are at a premium and this approach minimizes
        redundant calls.
    """
    shipping_url = SELLER_SHIPPING_URL.format(seller_id=seller.id)
    seller_shipping_range_url = SELLER_SHIPPING_RANGE_PRICE_URL.format(seller_id=seller.id)
    r_shipping_details = session.get(shipping_url)
    r_shipping_details.raise_for_status()
    if len(r_shipping_details.json()["shipping"]) == 0:
        return
    for shipping_id_json in r_shipping_details.json()["shipping"]["available_shipping"]:
        seller_shipping_id = shipping_id_json["seller_shipping_id"]
        seller.shipping_details.add_seller_shipping_id(seller_shipping_id)

        # get shipping range information for seller_shipping_id
        r_shipping_range = session.get(
            seller_shipping_range_url,
            params={"seller_shipping_id": seller_shipping_id}
        )
        r_shipping_range.raise_for_status()
        for country_range in r_shipping_range.json()['range-price']['country_ranges']:
            country_iso_code = country_range['country_iso_code']
            if country_iso_code not in seller.shipping_details.ships_to_countries:
                seller.shipping_details.add_ships_to_country(country_iso_code)


def get_seller_batch(page_num, page_limit):
    """Calls MVM API to get a batch of sellers, returns list of Seller objects"""
    r = session.get(SELLERS_URL, params={"limit": page_limit, "page": page_num})
    r.raise_for_status()
    seller_batch = []
    for seller_json in r.json()["sellers"]:
        seller = Seller()
        seller.id = seller_json["id"]
        seller.shipping_details.ships_from_country = seller_json.get("id_country", {}).get("iso_code")
        custom_fields = json.loads(seller_json.get("custom_fields", ""))
        if custom_fields.get(FR_EPR_REG_NUMBER_CUSTOM_FIELD_ID, {}).get("value"):
            seller.compliance_details.fr_epr_reg_number = custom_fields.get(
                FR_EPR_REG_NUMBER_CUSTOM_FIELD_ID, {}
                ).get("value")
        if custom_fields.get(DE_LUCID_REG_NUMBER_CUSTOM_FIELD_ID, {}).get("value"):
            seller.compliance_details.de_lucid_reg_number = custom_fields.get(
                DE_LUCID_REG_NUMBER_CUSTOM_FIELD_ID, {}
                ).get("value")
        seller_batch.append(seller)
    return seller_batch


def run_checks_for_seller_batch(seller_batch, seen_seller_ids):
    seller_check_result_details = {}
    for seller in seller_batch:
        if seller.id in seen_seller_ids:
            print(f"Skipping previously seen seller id: {seller.id}")
            continue
        seen_seller_ids.add(seller.id)
        print(f"Populating seller details for seller id: {seller.id}")
        populate_seller_details(seller)
        print(f"Running compliance checks for seller id: {seller.id}")
        seller_check_results = RunComplianceChecks.run_all_checks_for_seller(seller)
        seller_check_result_details[seller.id] = seller_check_results
        pass_fail_str = "PASSED" if len(seller_check_results['checks_failed']) == 0 else "FAILED"
        print(f"Finished compliance checks for seller id: {seller.id}. Verdict: {pass_fail_str}")
    return seller_check_result_details

def report_all_seller_check_results(all_seller_check_results):
    sellers_with_no_violations = 0
    sellers_with_violations = 0

    print("\n\nStarting to print detailed results:\n")

    for seller_id, check_results in all_seller_check_results.items():

        seller_passed_all_checks = len(check_results['checks_failed']) == 0
        if seller_passed_all_checks:
            sellers_with_no_violations += 1
        else:
            sellers_with_violations  += 1

        # TODO: Replace print statements with CSV file creation/upload
        pass_fail_str = "PASSED" if seller_passed_all_checks else "FAILED"
        print(
            f"Seller {seller_id} result: {pass_fail_str}\n" \
            f"Successful tests: {check_results['checks_passed']}\n" \
            f"Failed tests: {check_results['checks_failed']})"
        )
    print("\n\nFinished printing detailed results\n")

    print(
        "Summary of sellers:\n" \
        f"Total analyzed: {len(all_seller_check_results)}\n" \
        f"Total passed: {sellers_with_no_violations}\n" \
        f"Total failed: {sellers_with_violations}")


def check_epr_compliance_for_all_sellers():
    page_limit = 100
    max_page_num = 50
    seen_seller_ids = set()

    all_seller_check_results = {}

    # We stop after 50 pages (5000 sellers) to stop forever loops (due to bugs etc)
    # TODO should we even do this, or can we rely on our code being good enough?
    for page_num in range(1, max_page_num + 1):
        print("Analyzing sellers, page {}. Total sellers anaylzed so far: {}".format(
            page_num,
            len(all_seller_check_results)
        ))

        seller_batch = get_seller_batch(page_num, page_limit)

        if len(seller_batch) == 0:
            print(f"Analyzing sellers, page {page_num} is empty. All sellers have been analyzed")
            if (page_num / max_page_num) > .5:
                # TODO: if we want to keep enforcing max_page_num, this statement should also
                # push a warning to a notificaiton channel (e.g. discord)
                print("We're approaching the max page limit. Consier increasing max_page_num soon")
            break

        batch_result_details = run_checks_for_seller_batch(seller_batch, seen_seller_ids)

        all_seller_check_results.update(batch_result_details)

    report_all_seller_check_results(all_seller_check_results)



if __name__ == "__main__":
    check_epr_compliance_for_all_sellers()
    # TODO: figure out a more graceful way to close the session.
    # Today, if this file is called from somewhere else, it will not close
    session.close()
