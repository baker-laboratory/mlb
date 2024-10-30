export AIRFLOW_HOME=/mlb/airflow
mamba env create -f airflow/environment.yaml
mamba run -n airflow_test airflow standalone
