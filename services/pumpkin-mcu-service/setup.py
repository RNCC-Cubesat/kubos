# coding: utf-8
# pylint: skip-file
import os
import setuptools

try:
    with open('README.md', 'r') as fh:
        long_description = fh.read()
except FileNotFoundError:
    long_description = 'A kubos service for interacting with a Pumpkin satellite bus'

try:
    with open('requirements.txt', 'r') as f:
        requirements = f.read()
        requirements = requirements.splitlines()
        requirements = [r for r in requirements if r.strip() != '']
except FileNotFoundError:
    # User installing from pip
    requirements = [
        'pumpkin-supmcu',
        'pumpkin-supmcu-kubos'
        'graphene == 2.1.8'
        'kubos_service == 1.0'
    ]


if os.environ.get('CI_COMMIT_TAG'):
    version = os.environ['CI_COMMIT_TAG']
elif os.environ.get('CI_JOB_ID'):
    version = os.environ['CI_JOB_ID']
else:
    version = '0.0.1'  # Makes sure the read the docs version can build.

setuptools.setup(
    name='pumpkin-mcu-service',
    version=version,
    author='James Womack, Austin Small',
    author_email='info@pumpkininc.com',
    description='Kubos service for interacting with Pumpkin a satellite bus',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://gitlab.com/pumpkin-space-systems/public/kubos/-/tree/master/services/pumpkin-mcu-service',
    packages=setuptools.find_packages(),
    entry_points={
        'console_scripts': ['pumkin-mcu-service=pumkin_mcu_service.service:execute']
    },
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    install_requires=requirements,
    python_requires='>=3.7',
)