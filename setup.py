from setuptools import setup, find_packages

setup(
    name="openclaw",
    version="0.1.0",
    description="OpenClaw开发工具集",
    author="OpenClaw Team",
    author_email="contact@openclaw.dev",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "GitPython>=3.1.0"
    ],
    entry_points={
        "console_scripts": [
            "openclaw=openclaw.main:main"
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)