"""Class for storing Seller details for easy access"""

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