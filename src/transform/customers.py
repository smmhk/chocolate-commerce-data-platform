import pandas as pd


def transform_customer(customer_df: pd.DataFrame) -> dict:
    # 고객 한 명씩 처리
    if len(customer_df) != 1:
        raise ValueError("고객 한 명이 담긴 DataFrame을 전달해주세요.")

    row = customer_df.iloc[0]

    # CSV의 빈 값(NaN)을 빈 문자열로 처리
    def clean_text(value) -> str:
        if pd.isna(value):
            return ""
        return str(value).strip()

    customer_id = clean_text(row["id"])
    first_name = clean_text(row["first_name"])
    last_name = clean_text(row["last_name"])
    email = clean_text(row["email"])
    phone = clean_text(row["phone"])

    if not customer_id:
        raise ValueError("원본 고객 id가 없습니다.")

    if not any([first_name, last_name, email, phone]):
        raise ValueError("전송할 고객 이름, 이메일 또는 전화번호가 필요합니다.")

    # 원본 고객 ID를 중복 검색에 사용할 reference_id로 저장
    square_customer = {
        "reference_id": customer_id,
    }

    # 값이 있는 필드만 요청에 포함
    field_mapping = {
        "given_name": first_name,
        "family_name": last_name,
        "email_address": email,
        "phone_number": phone,
    }

    for field, value in field_mapping.items():
        if value:
            square_customer[field] = value
    
    return square_customer