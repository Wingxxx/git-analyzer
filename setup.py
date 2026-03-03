from setuptools import setup, find_packages

setup(
    name="openclaw-git-analyzer",
    version="1.0.0",
    description="Git repository analysis tool for OpenClaw",
    author="Wing",
    author_email="wing@example.com",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "GitPython>=3.1.0"
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)