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

from piecash import open_book, Transaction, Split, GnucashException  # , Account, Commodity
from decimal import Decimal
from pathlib import Path
from csv import DictReader
from datetime import datetime
import sys

READ_ONLY = False

# TODO read stuff in from a config file

BOOK_DIR = 'Documents/Financien/'  # Provide relative to your home folder
BASE_DIR = Path.home() / Path(BOOK_DIR)
BOOK_NAME = 'practice.gnucash'
INFILE = BASE_DIR / BOOK_NAME

CSV = BASE_DIR / 'bank_statement.csv'
SEP = ';'


def print_account_transactions(account):
    '''
    Functions on account object:
    'book', 'budget_amounts', 'children', 'code', 'commodity', 'commodity_guid', 'commodity_scu', 'description', 'fullname', 'get', 'get_all_changes', 'get_balance', 'guid', 'hidden', 'is_template', 'iteritems', 'lots', 'metadata', 'name', 'non_std_scu', 'object_to_validate', 'observe_commodity', 'on_book_add', 'parent', 'parent_guid', 'placeholder', 'scheduled_transaction', 'sign', 'slots', 'splits', 'type', 'validate'
    '''
    print("Transactions for account", account.name)
    print("------------------------------------")
    for split in account.splits:
        transaction = split.transaction
        print(str(transaction.enter_date), str(split.value), currency, split.transaction.description)
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
    '''
    with open(CSV) as f:
        reader = DictReader(f, delimiter=SEP)
        for transaction in reader:
            dt = datetime.strptime(transaction['Datum'], '%Y%m%d')
            # dt = datetime.strptime(transaction['Datum'], '%Y%m%d').date()
            afbij = transaction['Af Bij']
            # From 10.000,55 to 10000.55
            bedrag = transaction['Bedrag (EUR)'].replace('.', '').replace(',', '.')
            omschrijving = transaction['Naam / Omschrijving']
            print(dt.date(), transaction['Code'], omschrijving,
                  transaction['Mutatiesoort'], transaction['Mededelingen'])
            if afbij == 'Af':
                create_transaction(bedrag, lopende_rekening, imbalance, omschrijving, dt)
            else:
                create_transaction(bedrag, imbalance, lopende_rekening, omschrijving, dt)

def test(book):

    # Iterating over all splits in all books and print the transaction description:
    for acc in book.accounts:
        print_account_transactions(acc)

    test_transaction

def test_transaction():
    # Test transaction: move 1000 euros from spaarrekening to lopende rekening, and back
    print("Before:", lopende_rekening.get_balance())
    create_transaction(1000, spaarrekening, lopende_rekening, "Test transaction", datetime.today())
    print("After:", lopende_rekening.get_balance())
    create_transaction(1000, lopende_rekening, spaarrekening, "Test transaction", datetime.today())
    print("Restored:", lopende_rekening.get_balance())


if __name__ == '__main__':

    # Open book
    try:
        book = open_book(INFILE, readonly=READ_ONLY)
    except GnucashException as exc:
        print("Exception:", exc)
        sys.exit(1)

    # We are currently assuming we always use the default currency
    currency = book.default_currency

    # Read in the accounts we need
    # Either by navigation the object tree, e.g.:
    # root = book.root_account
    # activa = root.children(name='Activa')
    # Or accessing by the full name (or by name)
    lopende_rekening = book.accounts(fullname='Activa:Huidige Activa:Lopende Rekening')
    spaarrekening = book.accounts(fullname='Activa:Huidige Activa:Spaarrekening')
    imbalance = book.accounts(name=f'Imbalance-{currency.mnemonic}')

    # Create records for the transactions in the CSV
    record_ING_transactions(CSV)

    # test(book)

    # Save transactions to the book
    book.save()

    # Close the book
    book.close()
