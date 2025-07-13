from setuptools import setup, find_packages

def parse_requirements(requirements):
    with open(requirements) as f:
        return [l.strip('\n') for l in f if l.strip('\n') and not l.startswith('#')]

requirements = parse_requirements("requirements.txt")

setup(
    name='execution_backend',
    version='0.0.1',
    install_requires=requirements,
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "ctutor=ctutor_backend.cli.cli:cli",
        ],
    }
)