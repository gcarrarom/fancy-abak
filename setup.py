from setuptools import setup, find_packages

setup(
    name='fancy-abak',
    version='0.8.0',
    author='Gui Martins',
    url='https://fancywhale.ca/',
    author_email='gmartins@fancywhale.ca',
    packages=find_packages(),
    include_package_data=True,
    py_modules=['abak'],
    python_requires='>=3.6',
    install_requires=[
        'click>=7.1.2',
        'requests>=2.21.0',
        'tabulate>=0.8.9',
        'iterfzf>=0.5.0.20.0',
        'PyYAML>=5.4.1',
        'click-keyring>=0.2.1'
    ],
    entry_points='''
        [console_scripts]
        abak=abak:abak
    ''',
)
