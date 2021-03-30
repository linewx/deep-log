from setuptools import setup, find_packages
install_requires = [
   
]


setup(
    name='deep-log',
    version="0.0.2",
    description='log analysis tool',
    license='MIT',
    author='Lu Ganlin',
    author_email='linewx1981@gmail.com',
    url='https://github.com/linewx/deep-log',
    packages=find_packages(),
    install_requires=install_requires,
    package_data={'deep_log.config': ['*.json']},
    entry_points={
        'console_scripts': [
            'dl = deep_log.main:main',
        ],
    }
)
