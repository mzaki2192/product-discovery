DECLARE target STRING DEFAULT '679a1899-6b39-493a-8590-5d79b1fbe6d0';
DECLARE dyn_sql STRING;

SET dyn_sql = (
  SELECT STRING_AGG(
    FORMAT(
      "SELECT '%s' AS table_schema, '%s' AS table_name, '%s' AS column_name, COUNT(1) AS matched_rows FROM `%s.%s` WHERE CAST(`%s` AS STRING) = '%s'",
      table_schema, table_name, column_name, table_schema, table_name, column_name, target
    ),
    ' UNION ALL '
  )
  FROM `tabby-dp.region-me-central2.INFORMATION_SCHEMA.COLUMNS`
  WHERE (LOWER(table_schema) LIKE '%capital%' OR table_schema IN ('raw_direct_debit','billing_rawdata','merchants_datamarts'))
    AND column_name IN ('id','payment_id','ref_no','external_transaction_id')
);

EXECUTE IMMEDIATE dyn_sql;
