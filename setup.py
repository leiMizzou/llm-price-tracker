from setuptools import setup
setup(
    name="llm-price-tracker",
    version="0.1.0",
    description="Compare LLM API prices across providers",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Lei Hua",
    url="https://github.com/leiMizzou/llm-price-tracker",
    py_modules=["llm_prices"],
    python_requires=">=3.8",
    entry_points={"console_scripts": ["llm-price-tracker=llm_prices:main"]},
)
