import unittest
from unittest.mock import patch

from src.pipelines.source_to_square import complete_order


class SquareOrderCompletionTests(unittest.TestCase):
    def setUp(self):
        self.money = {"amount": 7150, "currency": "CAD"}
        self.order = {
            "id": "square-order",
            "reference_id": "CCF-000002",
            "location_id": "location",
            "state": "OPEN",
            "total_money": self.money,
            "net_amount_due_money": self.money,
            "line_items": [{"uid": "line", "catalog_object_id": "variation"}],
        }
        self.completed_order = {
            **self.order,
            "state": "COMPLETED",
            "net_amount_due_money": {"amount": 0, "currency": "CAD"},
        }
        self.payment = {
            "id": "payment",
            "order_id": self.order["id"],
            "location_id": self.order["location_id"],
            "amount_money": self.money,
            "total_money": self.money,
            "status": "APPROVED",
            "source_type": "EXTERNAL",
            "external_details": {"source": "Lovable POS simulated cash"},
        }

    @patch.object(complete_order, "approve_external_payment")
    @patch.object(complete_order, "pay_order")
    @patch.object(complete_order, "list_order_payments")
    def test_completed_order_skips_payment_operations(self, list_payments, pay, approve):
        complete_order.complete_cash_order(self.completed_order)
        list_payments.assert_not_called()
        pay.assert_not_called()
        approve.assert_not_called()

    @patch.object(complete_order, "retrieve_order")
    @patch.object(complete_order, "pay_order")
    @patch.object(complete_order, "approve_external_payment")
    @patch.object(complete_order, "list_order_payments")
    def test_resume_after_create_timeout(self, list_payments, approve, pay, retrieve):
        list_payments.side_effect = [[], [self.payment]]
        approve.side_effect = TimeoutError
        retrieve.return_value = self.completed_order

        with self.assertRaises(TimeoutError):
            complete_order.complete_cash_order(self.order)
        pay.assert_not_called()

        complete_order.complete_cash_order(self.order)
        approve.assert_called_once_with(self.order, "ccf-ext-square-order-v1")
        pay.assert_called_once_with("square-order", "payment", "ccf-pay-square-order-v1")
        retrieve.assert_called_once_with("square-order")

    @patch.object(complete_order, "retrieve_order")
    @patch.object(complete_order, "pay_order")
    @patch.object(complete_order, "approve_external_payment")
    @patch.object(complete_order, "list_order_payments", return_value=[])
    def test_new_payment_requires_completed_order_on_retrieval(
        self, list_payments, approve, pay, retrieve
    ):
        approve.return_value = self.payment
        retrieve.return_value = self.order
        with self.assertRaisesRegex(RuntimeError, "완료 상태"):
            complete_order.complete_cash_order(self.order)
        list_payments.assert_called_once_with(self.order)
        pay.assert_called_once_with("square-order", "payment", "ccf-pay-square-order-v1")

    @patch.object(complete_order, "pay_order")
    @patch.object(complete_order, "approve_external_payment")
    @patch.object(complete_order, "list_order_payments")
    def test_wrong_amount_blocks_payment(self, list_payments, approve, pay):
        list_payments.return_value = [{**self.payment, "amount_money": {"amount": 7151, "currency": "CAD"}}]
        with self.assertRaisesRegex(ValueError, "금액 연결"):
            complete_order.complete_cash_order(self.order)
        approve.assert_not_called()
        pay.assert_not_called()

    def test_sync_retrieves_existing_successful_cash_order(self):
        from pathlib import Path
        from tempfile import TemporaryDirectory

        import pandas as pd

        from src.pipelines.source_to_square import sync_orders

        line = {
            "uid": "line",
            "catalog_object_id": "variation",
            "quantity": "1",
            "base_price_money": self.money,
        }
        completed_order = {
            **self.completed_order,
            "total_tax_money": {"amount": 0, "currency": "CAD"},
            "line_items": [line],
        }
        frames = [
            pd.DataFrame([{
                "order_id": "CCF-000002", "channel": "RETAIL",
                "order_status": "COMPLETED", "payment_method": "CASH",
                "square_sync_status": "SUCCESS", "square_order_id": "square-order",
                "square_location_id": "location", "store_id": "store",
                "customer_id": "", "tax_amount": "0", "total_amount": "71.50",
            }]),
            pd.DataFrame([{
                "id": "line", "order_id": "CCF-000002", "sku": "SKU-1",
                "square_line_item_uid": "line", "square_catalog_object_id": "variation",
            }]),
            pd.DataFrame([{"store_id": "store", "square_location_id": "location"}]),
            pd.DataFrame(),
            pd.DataFrame([{"sku": "SKU-1", "square_catalog_object_id": "variation"}]),
        ]

        with TemporaryDirectory() as directory:
            root = Path(directory)
            with (
                patch.object(sync_orders, "get_online_source_dir", return_value=root),
                patch.object(sync_orders, "PROCESSED_DATA_DIR", root / "processed"),
                patch.object(sync_orders, "read_csv", side_effect=frames),
                patch.object(sync_orders, "transform_order", return_value={
                    "order": {"location_id": "location", "line_items": [line]},
                }),
                patch.object(sync_orders, "retrieve_order", return_value=completed_order) as retrieve,
                patch.object(sync_orders, "create_order") as create,
                patch.object(sync_orders, "save_csv") as save,
                patch.object(complete_order, "list_order_payments") as list_payments,
            ):
                sync_orders.run_order_pipeline()

        retrieve.assert_called_once_with("square-order")
        create.assert_not_called()
        save.assert_not_called()
        list_payments.assert_not_called()
