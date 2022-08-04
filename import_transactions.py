'''
This script automatically reads in transactions from a CSV downloaded from the ING bank.
All transactions are for the "lopende rekening" (main bank account) and will be registered
against the Imbalanced-EUR account. This makes it explicit which transactions are automatically
imported and should be manually checked.

This script uses piecash and assumes you store your data in sq3lite format.
Make sure to make a backup before testing.

There is currently no filtering on dates, so all transactions provided in the csv will be imported.
Instead, only request a csv from ING for the time period you want to import.

The bank statement with the most recent format downloaded from ING has the following fields:

    - Datum
    - Naam / Omschrijving
    - Rekening
    - Tegenrekening
    - Code
        * IC : incasso
        * ID : iDeal
        * BA : Betaalautomaat
        * GT : Online bankieren
        * OV : Overschrijving
        * VZ : Verzamelbetaling
        * ... ?
    - Af Bij
    - Bedrag (EUR)
    - Mutatiesoort
    - Mededelingen
    - Saldo na mutatie
    - Tag

- CSV: bank_statement.csv
- Ledger: practice.gnucash

'''

from piecash import open_book, Transaction, Split, GnucashException, Account  # , Commodity
from decimal import Decimal
from pathlib import Path
from csv import DictReader
from datetime import datetime
import sys
import yaml


def load_config(name='config.yml'):
    '''
    Config file assumed to be in the same folder as this script
    '''
    with open(name) as f:
        cfg = yaml.load(f)
    # Print the config
    for section in cfg:
        print(section, ":")
        print("\t", cfg[section])
    return cfg


def print_account_transactions(account):
    '''
    Print basic info on the transactions from some account

    TODO maybe allow a filter on date; currently don't need this.
    '''
    print("Transactions for account", account.name)
    print("------------------------------------")
    for split in account.splits:
        transaction = split.transaction
        print(str(transaction.enter_date), str(split.value), currency, transaction.description)
    print()


def create_transaction(value, from_acc, to_acc, description, datetime):
    '''
    You don't need to do anything with the return value.
    The transaction is applied to the book anyways.
    '''
    value = Decimal(value)
    return Transaction(
        currency=currency,
        description=description,
        enter_date=datetime,
        post_date=datetime.date(),
        splits=[
            Split(value=-value, account=from_acc),
            Split(value=value, account=to_acc)],
        )


def record_ING_transactions(infile):
    '''
    TODO some transactions I schedule directly in GnuCash
    I want to detect those as duplicates and NOT add them here.
    Right now, I have to manually remove them.
    
    TODO number transactions meaningfully; maybe parse info?

    TODO make more generic; get field names from config?
    '''
    with open(CSV) as f:
        reader = DictReader(f, delimiter=SEP)
        for transaction in reader:
            dt = datetime.strptime(transaction['Datum'], '%Y%m%d')
            afbij = transaction['Af Bij']
            # From 10.000,55 to 10000.55
            bedrag = transaction['Bedrag (EUR)'].replace('.', '').replace(',', '.')
            code = transaction['Code']
            mutatiesoort = transaction['Mutatiesoort']
            omschrijving = transaction['Naam / Omschrijving']
            mededelingen = transaction['Mededelingen']
            print(dt.date(), code, omschrijving, mutatiesoort, mededelingen)
            descr = ' '.join((mutatiesoort, omschrijving))
            if afbij == 'Af':
                create_transaction(bedrag, checkings, imbalance, descr, dt)
            else:
                create_transaction(bedrag, imbalance, checkings, descr, dt)


def test(book):
    '''
    Test some functionality. Notice that transactions are created,
    so saving the book will add two dummy transactions (that cancel each other out).
    '''
    # Iterating over all splits in all books and print the transaction description:
    for acc in book.accounts:
        print_account_transactions(acc)

    # Test transaction: move 1000 euros from savings to lopende rekening, and back
    test_transaction()


def test_transaction():
    '''
    Move 1000 euros from saving account to checking account, and back
    '''
    print("Before:", checkings.get_balance())
    create_transaction(1000, savings, checkings, "Test transaction", datetime.today())
    print("After:", checkings.get_balance())
    create_transaction(1000, checkings, savings, "Test transaction", datetime.today())
    print("Restored:", checkings.get_balance())


if __name__ == '__main__':

    # Load config
    cfg = load_config(name='config.yml')

    # Define global variables, reading from config
    READ_ONLY = cfg['read_only']
    BASE_DIR = Path.home() / Path(cfg['locations']['dir'])
    INFILE = BASE_DIR / cfg['locations']['book']
    CSV = BASE_DIR / cfg['locations']['bank_statement']
    SEP = cfg['csv_delimiter']

    # Open book
    try:
        book = open_book(INFILE, readonly=READ_ONLY)
    except GnucashException as exc:
        print("Exception:", exc)
        sys.exit(1)

    # We are currently assuming we always use the default currency
    currency = book.default_currency

    # Read in the accounts we need by their full name
    # These accounts should exist; fail loudly if not
    root = book.root_account
    checkings = book.accounts(fullname=cfg['bank']['checkings'])
    savings = book.accounts(fullname=cfg['bank']['savings'])

    # Create an imbalance account under root account if it does not exist yet
    # The naming follows GnuCash convention, e.g. 'Imbalance-EUR'
    imbalance_fn = f'Imbalance-{currency.mnemonic}'
    # imbalance_fn = f'Imbalance-TEST'
    try:
        imbalance = book.accounts(name=imbalance_fn)
    except KeyError:
        # The original error message prints all accounts and is very long
        print("Could not find account with name", imbalance_fn)
        print("Creating imbalance account", imbalance_fn)
        imbalance = Account(
                type='BANK',
                commodity=currency,
                name=imbalance_fn,
                parent=root
                )

    # Create records for the transactions in the CSV
    record_ING_transactions(CSV)

    # test(book)

    # Save transactions to the book
    book.save()

    # Close the book
    book.close()
