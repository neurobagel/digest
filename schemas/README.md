# Schema for inputs to the dashboard

## `bagel_schema.json`

### Overview
This file describes the recognized columns in tabular inputs to the dashboard (`bagel.csv`). In general, each row in a `bagel.csv` is expected to correspond to a single subject session (i.e., a unique pairing of `participant_id` and `session`), and is referred to as a "record."

### Column categorization in schema
In the schema, columns are organized into two categories. 
These purely meant to guide automated `bagel.csv` generation, and do not have any bearing on the actual formatting of the `bagel.csv` itself:  
- `GLOBAL_COLUMNS`: Includes columns describing metadata that should have the same meaning regardless of pipeline, and does not depend on pipeline outputs.  
- `PIPELINE_STATUS_COLUMNS`: Includes columns conveying information about pipeline completion that depends on pipeline-specific outputs and may vary depending on the pipeline tracker used.

### Prefixed vs. non-prefixed columns
For columns which are recognized by their _prefix_ rather than full column name (see `IsPrefixed` schema attribute below), 
prefixes must be separated from user- or pipeline tracker-defined suffixes in the column name by a double underscore, `"__"`.

### Column schema attributes
The `bagel_schema.json` describes each recognized column in a `bagel.csv` using attributes from the following table.
Note that keys in the .json are purely column identifiers meant to make automated `bagel.csv` generation easier; the actual expected column name is defined by the `Label` attribute.

| Column attribute   | Meaning                                                                                                                                                                                                                                                               |
| ------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `Label`            | The actual expected string name or prefix for the column (header) in the `bagel.csv`. _See also_ `IsPrefixedColumn`_._                                                                                                                                                                                        |
| `Description`      | Description of the column values, including the definitions of different acceptable values for categorical columns.                                                                                                                                                   |
| `dtype`            | The expected type for values in the column.                                                                                                                                                                                                                     |
| `IsRequired`       | Whether or not the column is required to be present in `bagel.csv`. If `true`, the dashboard will throw an error if the column is missing.                                                                                                                      |
| `Range`            | Acceptable values for data in the column. _Only present for categorical columns._                                                                                                                                                                             |
| `MissingValue`     | Value expected to denote that data is not available for the column. _Only present for non-categorical columns that allow missing values._                                                                                                                 |
| `IsPrefixedColumn` | Whether the `Label` for this column represents a recognized prefix in the column name (`true`) or the full column name (`false`). Columns for which `"IsPrefixedColumn": true` can have more than one instance in the `bagel.csv`, and are expected to have unique user-defined informative suffixes in line with the column `Description`. |
|                    |                                                                                                                                                                                                                                                                 |
