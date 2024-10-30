from setuptools import find_namespace_packages, setup
 requirements = [
     "flake8",
     "pytest",
     "requests",
     "pytest-helpers-namespace",
     "pytest-mock",
     "apache-airflow",
     "apache-airflow-providers-databricks",
     "pytest-xdist","pytest==7.1.2",
     "pytest-cov==2.10.1"
 ]


 setup(
     name="py-project",
     version=0.1,
     description="testing github workflows",
     author="Rana Sushant",
     author_email="ABC@YYY.com",
     python_requires=">=3.7",
     py_modules=["root directory"],
     install_requires=requirements,
 )
