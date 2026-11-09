# NZ election 2026
The dataset of New Zealand election results in 2026

![](https://shields.io/badge/dependencies-Python_3.14-blue)



## Install

Create and activate a Python virtual environment.

Run the following command.

```
pip install -r requirements.txt
```



## Usage

### Collect data

*Valid before official results are declared. After that, data source may be overwritten.*

*If having the database, this step can be skipped.*

Run the following command.

```
python get_electorates_list_rnz_preliminary.py
python get_parties_rnz.py
python get_votes_rnz_preliminary.py
```

