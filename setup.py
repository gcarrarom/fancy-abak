from setuptools import setup, find_packages

setup(
    name='fancy-abak',
    version='1.2.0',
    author='Gui Martins',
    url='https://fancywhale.ca/',
    author_email='gmartins@fancywhale.ca',
    packages=find_packages(),
    include_package_data=True,
    py_modules=['abak'],
    python_requires='>=3.6',
    install_requires=[
        "certifi==2022.12.7",
        "charset-normalizer==3.0.1",
        "click==8.1.3",
        "idna==3.4",
        "importlib-metadata==6.0.0",
        "pyfzf==0.3.1",
        "jaraco.classes==3.2.3",
        "keyring==23.13.1",
        "more-itertools==9.0.0",
        "pyaml==21.10.1",
        "PyYAML==6.0",
        "requests==2.28.2",
        "tabulate==0.9.0",
        "urllib3==1.26.14",
        "zipp==3.12.0",
    ],
    entry_points='''
        [console_scripts]
        abak=abak:abak
    ''',
    long_description="CLI Tool to interface with Abak"
)
