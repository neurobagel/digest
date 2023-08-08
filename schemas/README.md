# Schema for inputs to the dashboard

## Overview
The set of recognized and expected columns within a tabular input file for the dashboard (referred to generically as a `bagel.csv`) is specified in `.json` files called bagel schemas.
Different schemas correspond to `bagel.csv` files containing different types of data (e.g. imaging vs. phenotypic).

| Schema                    | (Meta)data type of corresponding CSV                               |
| ------------------------- | ------------------------------------------------------------------ |
| `bagel_schema.json`       | Metadata for raw neuroimaging data and processing pipeline outputs |
| `bagel_schema_pheno.json` | Demographic and phenotypic assessment data                         |

**NOTE:** 
Within a `bagel.csv`, each row is expected to correspond to a single subject session (i.e., a unique pairing of `participant_id` and `session_id`), 
and is referred to as a "record."

## How to read the schema
### Column categories
Within a schema, columns are organized into two categories to simplify the process of automated `bagel.csv` generation 
(these categories are not present in an actual input file):

**Global columns:** Includes columns describing basic metadata that should have the same meaning regardless of the specific task described by a given record 
(e.g., a certain processing pipeline or phenotypic assessment), 
and does not depend on task outputs.  
**Task-specific columns:** Includes columns whose values may have task-specific meanings.
e.g., in the schema for an imaging bagel, the `"PIPELINE_STATUS_COLUMNS"` convey info about processing pipeline completion that depends on pipeline-specific outputs and may vary depending on the pipeline tracker used.

### Column attributes
Recognized columns are individually described in the schema using the following attributes:
- `Description`
  - Describes the column contents, along with the meaning of different acceptable values for categorical columns.
- `dtype`
  - The expected type for values in the column.
- `IsRequired`
  - Whether or not the column is required to be present in `bagel.csv`. 
  If `true`, the dashboard will throw an error if the column is missing.
- `Range`
  - Acceptable values for data in the column. 
  Only present for categorical columns.
- `MissingValue`
  - The value expected to denote that data is not available for the column. 
  Only present for non-categorical columns.
- `IsPrefixedColumn`
  - Whether or not this column will be recognized by a prefix in the column name.
  If `true`, columns with this prefix are expected to have unique user-defined informative suffixes in line with the  `Description`. 
  More than one column can have the same prefix.
