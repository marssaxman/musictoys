from setuptools import setup, find_packages

setup(
    name = "musictoys",
    version = "0.1a0",
    author = "Mars Saxman",
    author_email = "mars@redecho.org",
    license = "MIT License",

    url = "https://marssaxman.github.io/musictoys/",
    project_urls = {
        "Source": "https://github.com/marssaxman/musictoys/",
    },

    keywords = 'music analysis',
    classifiers = [
        'Development Status :: 2 - Pre-Alpha',
        'License :: OSI Approved :: MIT License',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Topic :: Multimedia :: Sound/Audio',
        'Topic :: Multimedia :: Sound/Audio :: Analysis',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],

    packages = find_packages(exclude=['docs', 'scrapbook']),
    python_requires = '~=2.7',
    install_requires = [
        'numpy>=1.11'
        'soundfile>=0.8',
    ],
)

