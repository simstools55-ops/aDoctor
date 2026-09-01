# Batch Doctor Policy

Batch Doctor coordinates many independent single-article diagnoses.

Each item:

- receives its own Case and Medical Record
- is prioritized independently
- may fail without stopping other items
- may be retried and resumed
- produces the same single-case result contract as an individual diagnosis

Batch Doctor does not weaken single-case validation or merge Medical Records.
