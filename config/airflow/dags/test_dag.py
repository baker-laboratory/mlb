import json
from airflow.decorators import dag, task

@dag(
    schedule=None,
    catchup=False,
    tags='mlb test'.split(),
)
def mlb_test_dag():
    @task()
    def extract(config: dict):
        data_string = '{"1001": 301.27, "1002": 433.21, "1003": 502.22}'
        order_data_dict = json.loads(data_string)
        return order_data_dict

    @task()
    def transform(order_data_dict: dict) -> dict[str, int]:
        total_order_value = 0
        for value in order_data_dict.values():
            total_order_value += value
        return {"total_order_value": total_order_value}

    @task()
    def load(total_order_value: float):
        print(f"Total order value is: {total_order_value:.2f}")

    order_data = extract()
    order_summary = transform(order_data)
    load(order_summary["total_order_value"])

mlb_test_dag()
