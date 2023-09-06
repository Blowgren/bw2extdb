from setuptools import setup, find_packages

setup(
    name='bw2extdb',
    version='0.4',
    author="Bartolomeus Löwgren",
    author_email='bartolomeus.haeusslingloewgren@vito.be',
    description='Tools to import and export data from brightway to an external sql database',
    zip_safe=True,
    packages=find_packages(),
    install_requires=[
        'bw2data',
        "bw2io",
        # for app:
        "streamlit",
        # for sql:
        "sqlmodel",
        # for ipynb:
        "ipykernel",
        # for database:
        'psycopg2',
    ],
   entry_points={
        "console_scripts": [
            "bw2extdb-app = bw2extdb.app.app_entry_point:main",
        ]
    },
)