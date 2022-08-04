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


'''
class Transaction(Transaction):
    # Overrides piecash Transaction class to add an equality function
    # 
    # NOTE __hash__ and __cmp__ are used before __eq__ with the "in" operator
    # where __eq__ is called last:
    # 'Match' if hash(a) == hash(b) and (a is b or a==b) else 'No Match'

    # Problem with this class: the SQL database may return two types now
    # Transaction and Transaction; I need to set some flag to allow this
    # but haven't figured out how. I'll just hardcode the __eq__ function
    # where I need it ...

    __mapper_args__ = {
            'polymorphic_identity': 'transactions',
            'with_polymorphic': '*',
            'polymorphic_on': ...?
            }

    def __eq__(self, other):
        # We consider a transaction to be the same if
        # it has the same post date, currency, and amount.
        # NOTE this condition is very weak! Ideally add some sort of id?

        # print(self.post_date, other.post_date)
        # print(self.currency, other.currency)
        # print(self.splits[0].value, other.splits[0].value)

        if isinstance(other, Transaction):
            if (self.post_date == other.post_date and
                    self.currency == other.currency and
                    self.splits[0].value == other.splits[0].value):
                return True
        return False
'''


def load_config(name='config.yml'):
    '''
    Config file assumed to be in the same folder as this script
    '''
    with open(name) as f:
        cfg = yaml.load(f, Loader=yaml.SafeLoader)
    # Print the config
    print("CONFIG:")
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


def create_transaction(value, from_acc, to_acc, description, dt):
    '''
    You don't need to do anything with the return value.
    The transaction is applied to the book anyways.
    '''
    value = Decimal(value)

    # Check if a transaction already exists
    # Check relative to the checkings account, because the imbalance split is meant as a placeholder
    # NOTE hard coded checkings account for now...
    transactions = [split.transaction for split in checkings.splits]

    # Define the new transaction
    new_transaction = Transaction(
            currency=currency,
            description=description,
            enter_date=dt,
            post_date=dt.date(),
            splits=[
                Split(value=value, account=to_acc),
                Split(value=-value, account=from_acc)],
            )

    # Validate the transaction
    new_transaction.validate()

    # Keep track of duplicates
    duplicate = False

    # print()
    # print("NEW", new_transaction.splits[0].value, new_transaction.splits[1].value)

    for transaction in transactions:
        # print("OLD", transaction.splits[0].value, transaction.splits[1].value)
        if (new_transaction.post_date == transaction.post_date and
                # NOTE Assuming all transactions are balanced, we can ignore on which side
                # the checkings account is and just take the absolute value
                abs(new_transaction.splits[0].value) == abs(transaction.splits[0].value) and
                new_transaction.currency == transaction.currency):

            # if new_transaction == transaction:  # Requires overloading __eq__
            # print("DUPLICATES:", new_transaction, transaction, "\n")
            duplicate = True

    print()

    return duplicate


def test_transaction_eq():

    value = Decimal(1000)
    from_acc = checkings
    to_acc = imbalance
    description = 'test'
    dt = datetime.now()

    tr1 = Transaction(
             currency=currency,
             description=description,
             enter_date=dt,
             post_date=dt.date(),
             splits=[
                 Split(value=-value, account=from_acc),
                 Split(value=value, account=to_acc)],
              )

    # Same transaction, but different object in memory
    tr2 = Transaction(
             currency=currency,
             description=description,
             enter_date=dt,
             post_date=dt.date(),
             splits=[
                 Split(value=-value, account=from_acc),
                 Split(value=value, account=to_acc)],
              )

    # Change value
    value = Decimal(500)
    tr3 = Transaction(
             currency=currency,
             description=description,
             enter_date=dt,
             post_date=dt.date(),
             splits=[
                 Split(value=-value, account=from_acc),
                 Split(value=value, account=to_acc)],
              )

    print("tr1 == tr2?", tr1 == tr2)
    print("tr1 == tr3?", tr1 == tr3)


def record_ING_transactions(infile):
    '''
    TODO some transactions I schedule directly in GnuCash
    I want to detect those as duplicates and NOT add them here.
    Right now, I have to manually remove them.

    TODO number transactions meaningfully; maybe parse info?
    Goal is to link to real-life documents; will I use this?

    TODO make more generic; get field names from config?
    '''
    with open(CSV) as f:
        reader = DictReader(f, delimiter=SEP)
        for transaction in reader:
            dt = datetime.strptime(transaction['Datum'], '%Y%m%d')
            afbij = transaction['Af Bij']
            # Convert from 10.000,55 to 10000.55
            bedrag = transaction['Bedrag (EUR)'].replace('.', '').replace(',', '.')
            code = transaction['Code']
            mutatiesoort = transaction['Mutatiesoort']
            omschrijving = transaction['Naam / Omschrijving']
            mededelingen = transaction['Mededelingen']
            descr = ' '.join((mutatiesoort, omschrijving, mededelingen))
            if afbij == 'Af':
                duplicate = create_transaction(bedrag, checkings, imbalance, descr, dt)
            else:
                duplicate = create_transaction(bedrag, imbalance, checkings, descr, dt)

            # NOTE may be really slow to commit each small edit!
            if duplicate:
                # If duplicate, do not save the transaction to the book
                print("DUPLICATE: ", dt.date(), code, omschrijving, mutatiesoort, mededelingen)
                book.cancel()
            else:
                # Save this transaction to the book
                print(dt.date(), code, omschrijving, mutatiesoort, mededelingen)
                book.save()


def test(book):
    '''
    Test some functionality. Notice that transactions are created,
    so saving the book will add two dummy transactions (that cancel each other out).
    Instead, we cancel all uncommited changes (also ones unsaved *before* the test function!).
    '''
    # Iterating over all splits in all books and print the transaction description:
    for acc in book.accounts:
        print_account_transactions(acc)

    # Test transaction: move 1000 euros from savings to lopende rekening, and back
    test_transaction()

    # Test equality function between transactions
    test_transaction_eq()

    # Cancel dummy transactions
    book.cancel()


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

    # Close the book
    book.close()
