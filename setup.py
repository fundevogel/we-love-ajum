import setuptools

# Load README
with open('README.md', 'r', encoding='utf8') as file:
    long_description = file.read()

# Define package metadata
setuptools.setup(
    name='we-love-ajum',
    version='0.7.2',
    author='Martin Folkers',
    author_email='hello@twobrain.io',
    maintainer='Fundevogel',
    maintainer_email='maschinenraum@fundevogel.de',
    description='Tools for interacting with the "AJuM" database',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/fundevogel/we-love-ajum',
    license='MIT',
    project_urls={
        'Issues': 'https://github.com/fundevogel/we-love-ajum/issues',
    },
    entry_points='''
        [console_scripts]
        ajum=src.cli:cli
    ''',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    packages=setuptools.find_packages(),
    install_requires=[
        'bs4',
        'click',
        'isbnlib',
        'requests',
    ],
    python_requires='>=3.6',
)
