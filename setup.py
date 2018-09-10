from setuptools import setup

setup(
    name='dxtrack',
    version='0.1.3',
    description='Python utilities and aws service for Daltix metric and error '
                'tracking',
    author='Sam Hopkins',
    author_email='sam@daredata.engineering',
    packages=['dxtrack'],
    install_requires=[
        'boto3'
    ],
)
