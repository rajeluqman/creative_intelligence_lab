"""S3 video -> Gemini (Flash, responseSchema) -> bronze_asset_raw (verbatim JSON)."""
# TODO: upload, poll (deferrable in Airflow), structured-output call, stamp model_version/prompt_version,
# write verbatim to Bronze. NEVER re-call on re-model (ADR-003). Log tokens/cost -> fact_extraction_run.
