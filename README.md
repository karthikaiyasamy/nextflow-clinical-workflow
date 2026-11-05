# 🏥 Clinical Telemetry & Resident Enrichment Nextflow DSL2 Masterclass
## Hands-On Training Sandbox: Bridging Philips Lifeline Telemetry to GSC High-Throughput Genomics

Welcome to your hands-on Nextflow DSL2 learning repository. This project is purpose-built to simulate a realistic, high-throughput clinical event-driven architecture that bridges your real-world background at **Philips Lifeline (clinical IoT telemetry and data warehousing)** with the **Genome Sciences Centre (high-throughput cancer pipelines and annotation databases)**.

---

## 🧭 The Architecture: Two Worlds, One Mental Model

### 1. Philips Lifeline Telemetry Architecture
```
[ Incoming Telemetry Batches ]
            │
            ▼  Process 1: CLEAN_TELEMETRY
[ Cleaned & Validated Sensor Packets ]
            │
            ▼  Process 2: ENRICH_RESIDENT (Database Join: Resident Registry / Vitals Baseline)
[ Enriched Telemetry + Anomaly Detection (Bradycardia, Tachycardia, Falls) ]
            │
            ▼  Channel Operator: .collect() (Micro-Batch Synchronization Barrier)
[ All Batches Synchronized ]
            │
            ▼  Process 3: AGGREGATE_WAREHOUSE
[ Redshift Warehousing Master Table + Nurse Alert Dashboard ]
```

### 2. GSC Cancer Genomics Equivalent
```
[ Raw Sequencing FASTQ Batches ]
            │
            ▼  Process 1: FASTQC_AND_TRIM (Filter Low-Quality Reads)
[ Cleaned FASTQ Reads ]
            │
            ▼  Process 2: VARIANT_ANNOTATION (Database Join: ClinVar, COSMIC, VEP)
[ Somatic Mutation Callset + Pathogenicity Scoring ]
            │
            ▼  Channel Operator: .collect() (Cohort Barrier)
[ All Sample Variants Synchronized ]
            │
            ▼  Process 3: MULTIQC_AND_POG_REPORT
[ Variant Warehouse Table + Molecular Tumor Board Clinical Report ]
```

---

## 📂 Project Directory Structure

```text
nextflow-clinical-etl/
├── README.md                      <-- You are here: Master training guide
├── main.nf                        <-- Nextflow DSL2 workflow definition
├── nextflow.config                <-- Parameters, resource profiles, reporting configuration
├── bin/                           <-- Nextflow puts this folder on the $PATH automatically!
│   ├── clean_telemetry.py         <-- Step 1: Data validation & cleaning
│   ├── enrich_resident.py         <-- Step 2: Database lookup & vital signs alerting
│   └── aggregate_warehouse.py     <-- Step 3: Warehousing & summary report generator
└── data/
    ├── telemetry/                 <-- Raw input files (multiple batches to demonstrate parallel execution)
    │   ├── batch_01_cedar_wing.csv
    │   ├── batch_02_maple_wing.csv
    │   └── batch_03_birch_wing.csv
    └── db/
        └── resident_registry.csv  <-- Master Patient Index / LIMS reference database
```

---

## 🚀 How to Run the Pipeline (Hands-On Exercises)

Open your terminal, navigate to this folder, and follow the exercises below:

```bash
cd /Users/karthik/dev/seymour/seymour-sandbox/nextflow-clinical-etl
```

---

### Exercise 1: Run the Pipeline Locally

Execute the pipeline using your local Nextflow installation:

```bash
nextflow run main.nf
```

#### What You Will See in the Terminal:
```text
N E X T F L O W  ~  version 24.10.x
Launching `main.nf` [friendly_einstein] DSL2 - revision: 9283f...

=================================================================
🏥  C L I N I C A L   T E L E M E T R Y   N E X T F L O W   E T L
=================================================================
Telemetry Input : .../data/telemetry/*.csv
Resident DB     : .../data/db/resident_registry.csv
Results Dir     : .../results
=================================================================

executor >  local (7)
[2a/1b4c91] process > CLEAN_TELEMETRY (Cleaning batch_01_cedar_wing) [100%] 3 of 3 ✔
[8f/90de32] process > ENRICH_RESIDENT (Enriching batch_02_maple_wing) [100%] 3 of 3 ✔
[d3/56ae11] process > AGGREGATE_WAREHOUSE                             [100%] 1 of 1 ✔
```

Notice how Nextflow launched **3 parallel tasks** for `CLEAN_TELEMETRY` (one for each batch CSV), then automatically routed their outputs into **3 parallel tasks** for `ENRICH_RESIDENT`, and finally synchronized all outputs into **1 task** for `AGGREGATE_WAREHOUSE`!

---

### Exercise 2: Inspect the Published Results

Inspect the generated outputs inside the `results/` folder:

```bash
ls -la results/
ls -la results/warehousing/
cat results/warehousing/clinical_alert_summary.md
```

You will see:
1. `results/cleaned/`: The cleaned CSVs with corrupted records stripped out.
2. `results/enriched/`: Enriched CSVs with patient names, room numbers, and clinical alert flags.
3. `results/warehousing/clinical_warehouse_master.csv`: Unified data warehouse table ready for bulk loading (`COPY`).
4. `results/warehousing/clinical_alert_summary.md`: The executive clinical dashboard showing active alerts (Arthur Pendelton with Bradycardia at 44 bpm, Robert Chen with a Critical Fall in Bathroom 205!).
5. `results/execution_reports/`: Nextflow automatically generated rich HTML reports (`report.html`, `timeline.html`, `pipeline_dag.html`). Open `results/execution_reports/report.html` in your web browser!

---

### Exercise 3: Inspect the `work/` Directory (Nextflow Internals)

Nextflow does all actual computing inside isolated sandbox folders under `work/`:

```bash
ls -la work/
```

Pick any subfolder (e.g. `work/8f/90de32...`) and inspect the hidden files Nextflow generates:
```bash
cd work/8f/90de32*   # (Use Tab auto-complete for your actual hash folder)
ls -la
```

* `.command.sh`: The exact bash command Nextflow ran with all variables substituted.
* `.command.run`: The wrapper script Nextflow used to execute the task, set environment variables, and monitor resource usage.
* `.command.log`: The captured standard output.
* `.command.err`: The captured standard error.
* `.exitcode`: The exit code (`0` for success, `137` for OOM killer).

This is where you go during production incidents to triage failures!

---

### Exercise 4: Test Nextflow Caching and Resuming (`-resume`)

Run the pipeline a second time with the `-resume` flag:

```bash
cd /Users/karthik/dev/seymour/seymour-sandbox/nextflow-clinical-etl
nextflow run main.nf -resume
```

#### What Happens:
```text
executor >  local (7)
[2a/1b4c91] process > CLEAN_TELEMETRY (Cleaning batch_01_cedar_wing) [100%] 3 of 3, cached: 3 ✔
[8f/90de32] process > ENRICH_RESIDENT (Enriching batch_02_maple_wing) [100%] 3 of 3, cached: 3 ✔
[d3/56ae11] process > AGGREGATE_WAREHOUSE                             [100%] 1 of 1, cached: 1 ✔
```

Notice: **cached: 3, cached: 3, cached: 1**!  
The execution took **0.2 seconds** because Nextflow evaluated the SHA-256 cryptographic hashes of the input files, scripts, and parameters, verified that nothing changed, and reused the previous outputs without recomputing!

---

### Exercise 5: Test Selective Cache Invalidation

Simulate a new incoming batch file:
```bash
cp data/telemetry/batch_03_birch_wing.csv data/telemetry/batch_04_oak_wing.csv
nextflow run main.nf -resume
```

#### What Happens:
* Batches 1, 2, and 3 are **instantly reused from cache**.
* Only the net-new `batch_04_oak_wing` executes through `CLEAN_TELEMETRY` and `ENRICH_RESIDENT`.
* `AGGREGATE_WAREHOUSE` automatically re-runs because its input channel now contains 4 files instead of 3.

This is the exact idempotency and checkpointing that saves hundreds of hours of compute on a cancer genomics cluster!

Clean up the test file when done:
```bash
rm data/telemetry/batch_04_oak_wing.csv
```

---

## 🧠 Nextflow DSL2 Concepts: The Software Engineer's Cheat Sheet

### 1. The `bin/` Directory Convention
In standard bash or Python, you have to specify `python3 /absolute/path/to/script.py`.  
In Nextflow, **any executable script in the `bin/` directory is automatically added to the `$PATH`** for all processes! Inside `main.nf`, you simply call `clean_telemetry.py` directly.

### 2. Queue Channels vs. Value Channels
* **Queue Channels (`Channel.fromPath`):** Non-blocking FIFO streams. Each item is consumed once by a process. Used for sample batches.
* **Value Channels (`file(params.registry)`):** Bound to a static resource. Can be read simultaneously by any number of parallel processes. Used for reference genomes, clinical registries, or configuration files.

### 3. Channel Operators Used in `main.nf`
* `map { file -> tuple(file.simpleName, file) }`: Transforms the raw path into a tuple `[ "batch_01_cedar_wing", /path/to/file.csv ]` so we have a clean sample ID tag.
* `.collect()`: Acts as a **synchronization barrier**. It waits until all upstream parallel tasks complete, gathers all their output files into a single list `[file1, file2, file3]`, and passes them together into `AGGREGATE_WAREHOUSE`.

---

## 🎙️ Spoken Interview Script: How to Talk About This Live

If the GSC selection committee asks:
*"Can you describe how you approach building pipelines in Nextflow?"*

> "Coming from a distributed systems background where I built high-throughput streaming and micro-batch architectures using AWS DynamoDB, Kinesis, Firehose, and Redshift, I found Nextflow DSL2's reactive dataflow paradigm very intuitive.
>
> In fact, to solidify my hands-on mastery, I built a working DSL2 pipeline modeled on an event-driven clinical telemetry architecture:
>
> * I structured the pipeline into decoupled, single-responsibility processes: first cleaning raw incoming sensor batches in parallel, then enriching them by joining against a master patient database and evaluating clinical vital sign alerts.
> * I used Nextflow channel operators like `.collect()` to establish a micro-batch synchronization barrier, mirroring the buffering window I engineered with Kinesis Firehose before bulk loading into a data warehouse.
> * I configured execution tracing and dynamic profiles in `nextflow.config`, and verified how Nextflow's DAG caching (`-resume`) uses task hashing to re-run only invalidated steps.
>
> That exact same pattern directly governs cancer variant calling at the GSC: streaming FASTQ files into parallel alignment processes, joining variant calls against ClinVar or COSMIC annotation databases, and collecting sample outputs into a unified cohort report for the POG molecular board."

