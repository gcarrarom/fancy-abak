from setuptools import setup, find_packages

setup(
    name='fancy-abak',
    version='0.0.1',
    author='Gui Martins',
    url='https://fancywhale.ca/',
    author_email='gmartins@fancywhale.ca',
    packages=find_packages(),
    include_package_data=True,
    py_modules=['fancy-abak'],
    install_requires=[
        'Click',
        'requests'
    ],
    entry_points='''
        [console_scripts]
        abak=abak:abak
    ''',
)
