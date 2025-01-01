from setuptools import setup, find_packages

setup(
    name="youtube_to_article",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        'yt-dlp',
        'openai',
        'python-dotenv',
        'selenium',
        'pydub',
        'requests'
    ],
) 