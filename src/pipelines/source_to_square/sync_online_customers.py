import logging
import sys

from src.pipelines.source_to_square.customer_sync import run_customer_sync


def run_customers_pipeline():
    run_customer_sync(channel="ONLINE", update_existing=True)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        stream=sys.stdout,
        force=True,
    )
    run_customers_pipeline()