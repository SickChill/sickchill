from setuptools import setup

setup(name='sickrage',
      version='3.3.2',
      description='Automated Video File Manager',
      url='http://github.com/SiCKRAGETV/SickRage',
      author='echel0n',
      author_email='sickrage.tv@gmail.com',
      license='MIT',
      packages=['funniest'],
      install_requires=[
          'requests',
      ],
      zip_safe=False,
)