# Compliance Bot

Detects compliance violations by sellers

## How to run on your local machine

1. Install [Python 3](https://www.python.org/)
2. Create a [virtual python environment](https://docs.python.org/3/library/venv.html) and activate it
3. Run `python3 -m pip install -r requirements.txt` in your CLI to install required python packages
4. In the top-level project directory (i.e. the same dir where `.gitignore` lives), run `touch .env` in the CLI
5. In the newly-created .env file, add the following line: `MVM_API_BEARER_TOKEN=your_bearer_token`, replacing `your_bearer_token` with your [MVM API Bearer Token](https://webkul.com/blog/shopify-multivendor-marketplace-app-api/) (To find tokens, in the MVM UI Admin view navigation bar, hover over three dots on the right of the navigation bar and click "Multivendor API")
6. You are now ready to run the bot! Use `python3 epr_violation_bot.py`
