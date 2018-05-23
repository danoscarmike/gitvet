from datetime import datetime as dt
import github3
import os


def print_remaining():
    g = github3.login(token=os.environ['GH_TOKEN'])
    rates = g.rate_limit()
    print('Rate limit:', str(rates['rate']['limit']))
    print('Rate remaining:', str(rates['rate']['remaining']))
    print('Rate resets:', dt.fromtimestamp(
                            rates['rate']['reset']).strftime('%F %X'))


def remaining():
    g = github3.login(token=os.environ['GH_TOKEN'])
    rates = g.rate_limit()
    return rates['rate']['remaining']


def reset():
    g = github3.login(token=os.environ['GH_TOKEN'])
    rates = g.rate_limit()
    return rates['rate']['reset']


if __name__ == "__main__":
    print_remaining()
