import pytest

def main():
    test_airflow_dag()

@pytest.mark.skip
def test_airflow_dag():
    # from airflow.decorators import task, dag
    @dag
    def test_dag():
        @task
        def foo():
            return 'foo'

        @task
        def bar(foo):
            return f'{foo}bar'

        bar(foo())

if __name__ == '__main__':
    main()
