from setuptools import setup, find_packages


setup(
    name="infra-terragrunt-examples",
    version="1.0",
    packages=find_packages(),
    entry_points = {
        'console_scripts': [
            'generate-examples=nextgeninfrastructure.generate:main'
        ],
    }
)
