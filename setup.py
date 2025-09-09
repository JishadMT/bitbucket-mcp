
from setuptools import setup, find_packages

setup(
    name='mcp_bitbucket_review',
    version='0.1.0',
    package_dir={'': 'src'},
    packages=find_packages(where='src'),
    entry_points={
        'console_scripts': [
            'mcp-bitbucket-review-server=mcp_bitbucket_review.mcp_bitbucket_review_server:main',
        ],
    },
)