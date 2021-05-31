from setuptools import setup, find_packages

setup(
    name='fancy-abak',
    version='0.1.10',
    author='Gui Martins',
    url='https://fancywhale.ca/',
    author_email='gmartins@fancywhale.ca',
    packages=find_packages(),
    include_package_data=True,
    py_modules=['abak'],
    python_requires='>=3.6',
    install_requires=[
        'click>=7',
        'requests',
        'tabulate',
        'iterfzf',
        'PyYAML'
    ],
    entry_points='''
        [console_scripts]
        abak=abak:abak
    ''',
)
