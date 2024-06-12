from setuptools import setup, find_packages

setup(
    name='omnetpypy',
    version='0.1.1',
    packages=find_packages(),
    install_requires=[
        # Add your dependencies here
    ],
    entry_points={},
    package_data={
        'omnetpypy': ['data/seeds.csv'],
    },
    include_package_data=True,
    url='https://github.com/LBacciottini/OmnetPyPy',
    author='Leonardo Bacciottini',
    author_email='baccio.leonardo@gmail.com',
    description='An omnet++-like simulation framework fully implemented on Python, '
                'with the possibility to support different simulation backends such as SimPy.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    license='MIT',
)
