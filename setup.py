from setuptools import setup, find_packages

setup(
    name="gpt3-contextual",
    version=0.4,
    url="https://github.com/uezo/gpt3-contextual",
    author="uezo",
    author_email="uezo@uezo.net",
    maintainer="uezo",
    maintainer_email="uezo@uezo.net",
    description="Contextual chat with GPT-3 of OpenAI API.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(exclude=["examples*", "tests*"]),
    install_requires=["openai==0.26.5"],
    license="MIT",
    classifiers=[
        "Programming Language :: Python :: 3"
    ]
)
