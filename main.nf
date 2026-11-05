nextflow.enable.dsl = 2

/*
========================================================================================
    🏥 CLINICAL TELEMETRY & RESIDENT ENRICHMENT PIPELINE (NEXTFLOW DSL2)
    Simulating Philips Lifeline Event-Driven Micro-Batch Architecture
========================================================================================
*/

params.telemetry = "$projectDir/data/telemetry/*.csv"
params.registry  = "$projectDir/data/db/resident_registry.csv"
params.outdir    = "$projectDir/results"

/*
 * PROCESS 1: Clean & Validate Raw Telemetry
 * Drops malformed records, checks timestamp formats and physiological bounds.
 */
process CLEAN_TELEMETRY {
    tag "Cleaning $batch_id"
    publishDir "${params.outdir}/cleaned", mode: 'copy'

    input:
    tuple val(batch_id), path(raw_csv)

    output:
    tuple val(batch_id), path("${batch_id}_cleaned.csv"), emit: cleaned_telemetry

    script:
    """
    clean_telemetry.py \\
        --input ${raw_csv} \\
        --output ${batch_id}_cleaned.csv
    """
}

/*
 * PROCESS 2: Enrich with Resident Database & Evaluate Clinical Alerts
 * Performs database lookup against Master Patient Index (Resident Registry),
 * joins resident metadata, and detects vital sign anomalies (bradycardia, tachycardia, falls).
 */
process ENRICH_RESIDENT {
    tag "Enriching $batch_id"
    publishDir "${params.outdir}/enriched", mode: 'copy'

    input:
    tuple val(batch_id), path(cleaned_csv)
    path registry_db

    output:
    tuple val(batch_id), path("${batch_id}_enriched.csv"), emit: enriched_telemetry

    script:
    """
    enrich_resident.py \\
        --telemetry ${cleaned_csv} \\
        --registry ${registry_db} \\
        --output ${batch_id}_enriched.csv
    """
}

/*
 * PROCESS 3: Aggregate Batches & Generate Warehousing Reports
 * Collects all processed wing batches (Micro-Batch Synchronization Barrier),
 * builds consolidated data warehouse table and executive clinical alert report.
 */
process AGGREGATE_WAREHOUSE {
    tag "Aggregating all batches"
    publishDir "${params.outdir}/warehousing", mode: 'copy'

    input:
    path enriched_files

    output:
    path "clinical_warehouse_master.csv", emit: master_table
    path "clinical_alert_summary.md",    emit: alert_report

    script:
    """
    aggregate_warehouse.py \\
        --inputs ${enriched_files} \\
        --output-table clinical_warehouse_master.csv \\
        --output-summary clinical_alert_summary.md
    """
}

/*
 * MAIN WORKFLOW ENTRYPOINT
 */
workflow {

    log.info """\
    =================================================================
    🏥  C L I N I C A L   T E L E M E T R Y   N E X T F L O W   E T L
    =================================================================
    Telemetry Input : ${params.telemetry}
    Resident DB     : ${params.registry}
    Results Dir     : ${params.outdir}
    =================================================================
    """
    .stripIndent()
    
    // 1. Create asynchronous queue channel from input telemetry batch files
    telemetry_ch = Channel
        .fromPath(params.telemetry, checkIfExists: true)
        .map { file -> tuple(file.simpleName, file) }

    // 2. Value channel for the reference resident registry database
    registry_file = file(params.registry, checkIfExists: true)

    // 3. Process 1: Clean & Validate (executes in parallel per batch)
    CLEAN_TELEMETRY(telemetry_ch)

    // 4. Process 2: Enrich with Resident Registry (executes in parallel per batch)
    ENRICH_RESIDENT(CLEAN_TELEMETRY.out.cleaned_telemetry, registry_file)

    // 5. Channel Operator: .collect() acts as the Micro-Batch barrier (like Kinesis Firehose!)
    // Gathers all enriched files from all parallel workers into a single list
    all_enriched_batches_ch = ENRICH_RESIDENT.out.enriched_telemetry
        .map { batch_id, file -> file }
        .collect()

    // 6. Process 3: Consolidate for Data Warehousing & Clinical Alerts
    AGGREGATE_WAREHOUSE(all_enriched_batches_ch)
}

