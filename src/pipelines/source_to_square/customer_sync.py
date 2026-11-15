# 온라인 회원정보를 Square에 동기화
import hashlib
import json
import logging
import os
import shutil
from datetime import datetime, timezone
from urllib.parse import quote

import pandas as pd
import requests

from src.clients.square.config import headers
from src.clients.square.customers import create_customer, list_customers
from src.config.paths import get_online_source_dir
from src.transform.square.customers_payload import transform_customer


LOGGER = logging.getLogger(__name__)

READ_OPTIONS = {
    "sep": ";",
    "dtype": str,
    "keep_default_na": False,
    "encoding": "utf-8-sig",
}


def save_csv(df, path):
    temporary_path = path.with_suffix(".csv.tmp")
    try:
        df.to_csv(
            temporary_path,
            sep=";",
            index=False,
            encoding="utf-8-sig",
        )
        temporary_path.replace(path)
    finally:
        temporary_path.unlink(missing_ok=True)


def update_square_customer(customer, payload):
    # 원본에 값이 있는 필드만 반영한다.
    # 원본의 빈 값으로 Square의 기존 정보를 삭제하지 않는다.
    fields = {
        key: value
        for key, value in payload.items()
        if key != "address"
    }

    if "address" in payload:
        fields["address"] = {
            **(customer.get("address") or {}),
            **payload["address"],
        }

    if all(customer.get(key) == value for key, value in fields.items()):
        return customer, "unchanged"

    # 조회 이후 다른 변경이 있었다면 덮어쓰지 않고 충돌로 처리
    if "version" in customer:
        fields["version"] = customer["version"]

    response = requests.put(
        "https://connect.squareupsandbox.com/v2/customers/"
        + quote(customer["id"], safe=""),
        headers=headers,
        json=fields,
        timeout=30,
    )

    if not response.ok:
        raise RuntimeError(
            f"Square 고객 수정 실패: HTTP {response.status_code} "
            f"{response.text}"
        )

    data = response.json()
    result = data.get("customer")

    if data.get("errors") or not result or not result.get("id"):
        raise RuntimeError(
            f"Square 고객 수정 응답 오류: {data.get('errors')}"
        )

    if result["id"] != customer["id"]:
        raise ValueError("수정 응답의 Square 고객 ID가 다릅니다.")

    return result, "updated"


def run_customer_sync(channel, update_existing):
    source_dir = get_online_source_dir()
    customers_path = source_dir / "customers_export.csv"
    addresses_path = source_dir / "customer_addresses_export.csv"

    customers = pd.read_csv(customers_path, **READ_OPTIONS)
    addresses = pd.read_csv(addresses_path, **READ_OPTIONS)

    for frame, required in (
        (customers, {"id", "signup_channel"}),
        (addresses, {"customer_id", "is_default"}),
    ):
        missing = required - set(frame.columns)
        if missing:
            raise ValueError(f"필수 CSV 컬럼이 없습니다: {missing}")

    customer_ids = customers["id"]

    if (
        customer_ids.str.strip().eq("").any()
        or customer_ids.ne(customer_ids.str.strip()).any()
        or customer_ids.duplicated().any()
    ):
        raise ValueError("고객 ID가 비어 있거나, 중복되거나, 앞뒤 공백이 있습니다.")

    target = customers.loc[
        customers["signup_channel"].str.strip().str.upper().eq(channel)
    ].copy()

    LOGGER.info(
        "status=started channel=%s run_id=%s source=%s total=%d target=%d",
        channel,
        os.getenv("PIPELINE_RUN_ID", "local"),
        source_dir,
        len(customers),
        len(target),
    )

    if target.empty:
        LOGGER.info("status=completed target=0")
        return

    # 기존 변환 함수는 is_default를 bool 값으로 사용한다.
    transform_addresses = addresses.copy()
    default_flags = addresses["is_default"].str.strip().str.lower()

    if not default_flags.isin(("", "true", "false", "1", "0")).all():
        raise ValueError("주소 CSV의 is_default 값이 올바르지 않습니다.")

    transform_addresses["is_default"] = default_flags.isin(("true", "1"))

    default_addresses = transform_addresses.loc[
        transform_addresses["is_default"]
    ]

    if default_addresses["customer_id"].duplicated().any():
        raise ValueError("기본 주소가 여러 개인 고객이 있습니다.")

    payloads = {
        row["id"]: transform_customer(row, transform_addresses)
        for _, row in target.iterrows()
    }

    for column in (
        "square_customer_id",
        "square_sync_status",
        "square_synced_at",
        "square_sync_error",
    ):
        if column not in customers.columns:
            customers[column] = ""

    if "square_customer_id" not in addresses.columns:
        addresses["square_customer_id"] = ""

    # 이메일 대신 원본 고객 ID(reference_id)로 연결한다.
    existing_by_reference = {}

    for customer in list_customers():
        reference_id = customer.get("reference_id")
        if reference_id:
            existing_by_reference.setdefault(reference_id, []).append(customer)

    for customer_id in payloads:
        if len(existing_by_reference.get(customer_id, [])) > 1:
            raise ValueError(
                f"동일 reference_id의 Square 고객이 여러 명입니다: {customer_id}"
            )

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")

    for path in (customers_path, addresses_path):
        backup_path = path.with_name(f"{path.name}.{timestamp}.bak")
        shutil.copy2(path, backup_path)
        LOGGER.info("stage=backup path=%s", backup_path)

    counts = {
        "created": 0,
        "updated": 0,
        "unchanged": 0,
        "existing": 0,
    }
    expected_mapping = {}

    for customer_id, payload in payloads.items():
        stage = "sync"

        try:
            matches = existing_by_reference.get(customer_id, [])

            if matches:
                customer = matches[0]

                if update_existing:
                    customer, action = update_square_customer(customer, payload)
                else:
                    action = "existing"
            else:
                create_payload = dict(payload)

                # 앞서 사용한 고객 생성 키 규칙을 유지한다.
                create_payload["idempotency_key"] = hashlib.sha256(
                    json.dumps(
                        payload,
                        sort_keys=True,
                        ensure_ascii=False,
                    ).encode("utf-8")
                ).hexdigest()

                customer = create_customer(create_payload)
                action = "created"

            square_id = customer["id"]

            if not square_id or customer.get("reference_id") != customer_id:
                raise ValueError("Square 고객의 reference_id가 다릅니다.")

            LOGGER.info(
                "stage=sync customer_id=%s square_customer_id=%s action=%s",
                customer_id,
                square_id,
                action,
            )

            customer_mask = customers["id"].eq(customer_id)
            address_mask = addresses["customer_id"].eq(customer_id)

            customers.loc[customer_mask, "square_customer_id"] = square_id
            customers.loc[customer_mask, "square_sync_status"] = "SUCCESS"
            customers.loc[customer_mask, "square_synced_at"] = (
                datetime.now(timezone.utc).isoformat()
            )
            customers.loc[customer_mask, "square_sync_error"] = ""
            addresses.loc[address_mask, "square_customer_id"] = square_id

            stage = "save_csv"

            # 파일별로 저장한다. 중간 실패 시 재실행해서 매핑을 복구한다.
            save_csv(addresses, addresses_path)
            save_csv(customers, customers_path)

            expected_mapping[customer_id] = square_id
            counts[action] += 1

            LOGGER.info(
                "stage=save_csv customer_id=%s address_rows=%d status=completed",
                customer_id,
                int(address_mask.sum()),
            )

        except Exception:
            LOGGER.exception(
                "stage=%s customer_id=%s status=failed",
                stage,
                customer_id,
            )
            raise

    # 디스크에 저장된 실제 결과 검증
    saved_customers = pd.read_csv(customers_path, **READ_OPTIONS)
    saved_addresses = pd.read_csv(addresses_path, **READ_OPTIONS)

    if (
        len(saved_customers) != len(customers)
        or len(saved_addresses) != len(addresses)
    ):
        raise ValueError("저장 후 CSV 행 수가 달라졌습니다.")

    for customer_id, square_id in expected_mapping.items():
        customer_rows = saved_customers.loc[
            saved_customers["id"].eq(customer_id)
        ]
        address_rows = saved_addresses.loc[
            saved_addresses["customer_id"].eq(customer_id)
        ]

        if (
            len(customer_rows) != 1
            or not customer_rows["square_customer_id"].eq(square_id).all()
            or not customer_rows["square_sync_status"].eq("SUCCESS").all()
            or not address_rows["square_customer_id"].eq(square_id).all()
        ):
            raise ValueError(f"CSV 매핑 저장 검증 실패: {customer_id}")

    LOGGER.info(
        "stage=validate_csv status=completed verified=%d",
        len(expected_mapping),
    )
    LOGGER.info(
        "status=completed channel=%s target=%d "
        "created=%d updated=%d unchanged=%d existing=%d",
        channel,
        len(target),
        counts["created"],
        counts["updated"],
        counts["unchanged"],
        counts["existing"],
    )