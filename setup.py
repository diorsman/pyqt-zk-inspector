from setuptools import setup

setup(name='qtinspector',
      version='0.0.1',
      packages=['qtinspector'],
      include_package_data=True,
      entry_points={
          'console_scripts': [
              'qtinspector = qtinspector.cli:main',
          ]
      },

      # You can't install PyQt4 with pip/etc so I can't list it here.
      # Aside from that, all that's special is kazoo (zk library)
      install_requires=[
          'kazoo',
      ]
      )
