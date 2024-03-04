import datetime
import json
import random
from json import JSONEncoder
from uuid import uuid4


# subclass JSONEncoder
class DateTimeEncoder(JSONEncoder):
    # Override the default method
    def default(self, obj):
        if isinstance(obj, (datetime.date, datetime.datetime)):
            return obj.isoformat()


def get_business_unit():
    return random.choice(("LMFR", "LMES", "LMIT", "RMFR"))


def get_origin():
    return random.choice(("PEGASE", "BOMP", "FLEX"))


def get_document_type():
    return random.choice(["invoice","credit-note"])


def get_curency_code():
    return "EUR"


def get_identifier():
    return str(uuid4())


def get_seller():
    return {
        "companyName": "-", # optional
        "tradingName": "-", # optional
        "companySubdivision": { # optional
            "identifier": "",
            "schemaIdentifier": "FIT"
        },
        "identifier": { # optional
            "identifier": "",
            "schemaIdentifier": "FIT"
        },
        "routing": [ # optional
            {
                "routingCode": "",
                "schemaIdentifier": ""
            }
        ],
        "invoicingCompany": {
            "companyCode": "",
            "schemaIdentifier": ""
        },
        "electronicalAddress": {
            "addressCode": "",
            "schemaIdentifier": ""
        },
        "sellerAddress": {
            "addressLine1": "",
            "addressLine2": "",
            "addressLine3": "",
            "addressLocality": "",
            "addressPostalCode": "",
            "addressCountrySubdivision": "",
            "addressCountryCode": ""
        },
        "sellerContact": [
            {
                "sellerContactPoint": "",
                "sellerContactPhone": "",
                "sellerContactEmail": ""
            }
        ]
    }


def get_buyer():
    return {
        "invoicingCompany": {
            "companyCode": "",
            "schemaIdentifier": ""
        },
        "buyerIdentifier": [
            {
                "identifierCode": "",
                "schemaIdentifier": ""
            }
        ],
        "buyerCompany": {
            "identifier": "",
            "schema": ""
        },
        "buyerEstablishment": {
            "identifier": "",
            "schema": ""
        },
        "routing": {
            "routingCode": "",
            "schemaIdentifier": ""
        },
        "buyerAddress": {
            "addressLine1": "",
            "addressLine2": "",
            "addressLine3": "",
            "addressLocality": "",
            "addressPostalCode": "",
            "addressCountrySubdivision": "",
            "addressCountryCode": ""
        },
        "buyerContact": {
            "contactPoint": "",
            "contactPhone": "",
            "contactEmail": ""
        }
    }

def generate_invoice_request():
    invoice_request = {
        "invoiceRequestDate": datetime.datetime.now(),
        "businessUnitCode": get_business_unit(),
        "origin": get_origin(),
        "documentType": get_document_type(),
        "currencyCode": get_curency_code(),
        "identifier": get_identifier(),
        "identifierSchema": "XXX",
        "seller": get_seller(),
        "buyer": get_buyer()
    }

    return json.dumps(invoice_request, indent=4, cls=DateTimeEncoder)


if __name__ == "__main__":
    invoice_request = generate_invoice_request()
    print(invoice_request)
