from setuptools import setup

setup(
    name='base16-builder',
    version='0.1',
    py_modules=['builder'],
    install_requires=[
        'Click',
        'pyyaml',
        'pystache',
        'click_default_group'
    ],
    entry_points='''
        [console_scripts]
        base16-builder=builder:cli
    ''',
)