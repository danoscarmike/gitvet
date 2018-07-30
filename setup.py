from setuptools import setup


def readme():
    with open('README.rst') as f:
        return f.read()


setup(name='gitvet',
      version='0.1',
      description='Tools for GitHub issue triage',
      long_description='readme()',
      classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.6',
      ],
      url='http://github.com/danoscarmike/gitvet',
      author='Dan O\'Meara,
      author_email='omeara.dan@gmail.com',
      license='MIT',
      packages=['gitvet'],
      install_requires=[
          'click',
          'github3.py', 
          'pytz'
      ],
      zip_safe=False)