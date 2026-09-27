# Data folder

This repository does **not** include Vireo's raw ticket data (it contains customer
messages and is not for public GitHub — see root README "Data privacy considerations").

To run the tool, place Vireo's supplied files here, unmodified:

```
data/
├── tickets.csv
├── agents.csv
├── orders.csv       (optional — not used by app.py in this version)
├── customers.csv    (optional — not used by app.py in this version)
└── products.csv     (optional — not used by app.py in this version)
```

Only `tickets.csv` and `agents.csv` are required to run `app.py`. Column definitions are
in the client-supplied `README.txt` (data pack) — not reproduced here since it isn't ours
to redistribute either; ask the Vireo account lead for the original data pack.
