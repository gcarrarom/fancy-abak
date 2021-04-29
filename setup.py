from setuptools import setup, find_packages

setup(
    name='fancy-abak',
    version='0.0.2',
    author='Gui Martins',
    url='https://fancywhale.ca/',
    author_email='gmartins@fancywhale.ca',
    packages=find_packages(),
    include_package_data=True,
    py_modules=['fancy-abak'],
    install_requires=[
        'click',
        'requests',
        'tabulate'
    ],
    entry_points='''
        [console_scripts]
        abak=abak:abak
    ''',
)
