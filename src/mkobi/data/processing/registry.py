"""Data processing module.

The authoritative pipeline implementation is in data_worker.py, which handles
background CSV processing with proper transaction management via RQ workers.
This module contains helper functions for data transformations and aggregations.
"""