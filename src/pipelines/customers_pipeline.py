#todo
from src.extract.load_csv import load_csv
from src.transform.customers import transform_customers


def run_customers_pipeline():

    customers_df = load_csv(
        "data/raw/customers.csv"
    )

    addresses_df = load_csv(
        "data/raw/customer_addresses.csv"
    )

    customers = transform_customers(
        customers_df=customers_df,
        addresses_df=addresses_df
    )

    for customer in customers:
        print(customer)