def transform_store(store_row):
    # 현재 CSV 주소 형식: "188 Cocoa Lane, Vancouver, BC"
    street_address = str(store_row["address"]).rsplit(",", 2)[0].strip()

    return {
        "location": {
            "name": str(store_row["store_name"]).strip(),
            "type": "PHYSICAL",
            "timezone": store_row["timezone"],
            "address": {
                "address_line_1": street_address,
                "locality": store_row["city"],
                "administrative_district_level_1": store_row["province"],
                "postal_code":store_row["postal_code"] ,
                "country": "CA",
            },
        }
    }