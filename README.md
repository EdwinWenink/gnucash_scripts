# GnuCash scripts

Scripts for the GnuCash double entry accounting software.
Currently, there is only one script for importing transactions from a CSV bank statement.

## Importing from an ING transaction overview

`import_transactions.py` is a script to automatically import transactions in CSV format from the ING bank.
All transactions are assumed to be for the "Lopende Rekening" (main bank account) or the "Spaarrekening" (savings account) and will be registered against the Imbalanced-EUR account.
This makes it explicit which transactions are automatically imported into your GnuCash book and should be manually checked and processed.

[This](This.md) script uses `piecash` and assumes you store your GnuCash data in `sq3lite` format.

There is currently no filtering on dates, so all transactions provided in the csv will be imported.
Instead, only request a csv from ING for the time period you want to import.
The script does recognize duplicates to some extent and will not import them.

### Bank statement fields

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

### Configuration

By default the configuration file is assumed to be located in the same folder as the import script.
You can override the default location by providing a path to `config.yml` with the `-c` or `--config` flag.
E.g. `python .\gnucash_scripts\import_transactions.py --config gnucash_scripts\config.yml`.

Example configuration, see [config.yml](./config.yml):

```
bank:  # specify full name to avoid ambiguity
    checkings: 'Activa:Huidige Activa:Lopende Rekening'
    savings: 'Activa:Huidige Activa:Spaarrekening'
    from_account: 'checkings'  # Whether you are importing transactions for the checkings or savings account
locations:
    dir: 'Documents/Financien/'  # Relative to your home folder 
    book: 'ledger.gnucash'  # relative to dir
    bank_statement: 'bank_statement.csv'  # relative to dir
read_only: false
csv_delimiter: ';'
```
