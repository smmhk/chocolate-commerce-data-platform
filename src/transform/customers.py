import pandas as pd


def clean_value(value):
    """
    None, NaN, 빈 문자열을 None으로 변환한다.
    """
    if pd.isna(value):
        return None

    value = str(value).strip()

    return value if value else None


def normalize_country(country):
    """
    Source country 값을 Square API country code로 변환한다.
    """
    country = clean_value(country)

    if country is None:
        return None

    country_mapping = {
        "Canada": "CA",
        "CA": "CA",
    }

    return country_mapping.get(country, country)


def transform_address(address_row):
    """
    Lovable customer_addresses 데이터
    → Square Address 형식
    """

    address = {
        "address_line_1": clean_value(address_row.get("address_line1")),
        "address_line_2": clean_value(address_row.get("address_line2")),
        "locality": clean_value(address_row.get("city")),
        "administrative_district_level_1": clean_value(
            address_row.get("province")
        ),
        "postal_code": clean_value(address_row.get("postal_code")),
        "country": normalize_country(address_row.get("country")),
    }

    # 값이 없는 필드는 Square에 보내지 않는다.
    return {
        key: value
        for key, value in address.items()
        if value is not None
    }


def find_default_address(customer_id, addresses_df):
    """
    customer_id에 해당하는 기본 주소를 찾는다.

    기본 주소가 없으면 None 반환.
    """

    customer_addresses = addresses_df[
        addresses_df["customer_id"] == customer_id
    ]

    if customer_addresses.empty:
        return None

    default_addresses = customer_addresses[
        customer_addresses["is_default"] == True
    ]

    if default_addresses.empty:
        return None

    return default_addresses.iloc[0]


def transform_customer(customer_row, addresses_df):
    """
    Lovable Customer + Default Address
    → Square Customer API payload
    """

    customer_id = customer_row["id"]

    payload = {
        "given_name": clean_value(customer_row.get("first_name")),
        "family_name": clean_value(customer_row.get("last_name")),
        "email_address": clean_value(customer_row.get("email")),
        "phone_number": clean_value(customer_row.get("phone")),
        "reference_id": clean_value(customer_id),
    }

    # -------------------------
    # Default Address 조회
    # -------------------------
    address_row = find_default_address(
        customer_id=customer_id,
        addresses_df=addresses_df
    )

    if address_row is not None:
        address = transform_address(address_row)

        if address:
            payload["address"] = address

    # None 제거
    return {
        key: value
        for key, value in payload.items()
        if value is not None
    }


def transform_customers(customers_df, addresses_df):
    """
    전체 Customer DataFrame을 Square payload 리스트로 변환한다.
    """

    return [
        transform_customer(
            customer_row=row,
            addresses_df=addresses_df
        )
        for _, row in customers_df.iterrows()
    ]