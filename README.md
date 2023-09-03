# Compliance Bot

Detects compliance violations by sellers

## How to run on your local machine

1. Install [Python 3](https://www.python.org/)
2. Create a [virtual python environment](https://docs.python.org/3/library/venv.html) and activate it
3. From the root directory (the directory where `README.md` lives), run `python3 -m pip install -r requirements.txt -r requirements_test.txt` to install required python packages.
4. Run `python3 setup.py develop` to configure your local environment.
5. From the root directory (the directory where `README.md` lives), run `touch .env` in the CLI
6. Run `echo "MVM_API_BEARER_TOKEN=your_bearer_token" >> .env`, replacing `your_bearer_token` with your [MVM API Bearer Token](https://webkul.com/blog/shopify-multivendor-marketplace-app-api/) (To find tokens, in the MVM UI Admin view navigation bar, hover over three dots on the right of the navigation bar and click "Multivendor API")
7. You are now ready to run the bot! To run the check use `python3 compliance_bot/epr_violations_check.py`. To run tests, use `pytest` or `pytest tests/some_specific_test_file`.

## TODOs

* Add unit tests
* [Dockerize](https://www.docker.com/blog/how-to-dockerize-your-python-applications/)
* Test this code when there are a large number of stores (multiple pages)
* Better exception handling for API errors