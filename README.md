# GnuCash scripts

Scripts for the GnuCash double entry accounting software.

## Importing from an ING transaction overview

`import_transactions.py` is a script to automatically import transactions in CSV format from the ING bank.
All transactions are assumed to be for the "lopende rekening" (main bank account) and will be registered against the Imbalanced-EUR account.
This makes it explicit which transactions are automatically imported into your GnuCash book and should be manually checked.

This script uses `piecash` and assumes you store your GnuCash data in `sq3lite` format.

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
