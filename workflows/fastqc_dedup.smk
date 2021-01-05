QCBIN, QCENV = env_bin_from_config3( config, 'QC')
outdir = 'QC/'+str(QCENV)+'/'
moutdir = 'QC/Multi/'+str(QCENV)+'/'

wildcard_constraints:
    rawfile = '|'.join(list(SAMPLES)),
    read = "R1|R2",
    outdir = outdir,
    moutdir = moutdir

rule themall:
    input:  expand("{moutdir}DEDUP_RAW/{condition}/multiqc_report.html", moutdir=moutdir, condition=str.join(os.sep,conditiononly(SAMPLES[0],config)))

if paired == 'paired':
    log.info('Running paired mode QC')
    rule qc_raw:
        input:  r1 = "FASTQ/{rawfile}_{read}.fastq.gz"
        output: o1 = report("{outdir}{rawfile}_{read}_fastqc.zip")
        log:    "LOGS/{outdir}{rawfile}_fastqc_{read}_raw.log"
        conda:  "nextsnakes/envs/"+QCENV+".yaml"
        threads: MAXTHREAD
        params:  qpara = lambda wildcards: ' '.join("{!s} {!s}".format(key,val) for (key,val) in tool_params(SAMPLES[0], None ,config, 'QC', QCENV)['OPTIONS'][0].items())
        shell: "OUT=$(dirname {output.o1});fastqc --quiet -o $OUT -t {threads} --noextract {params.qpara} -f fastq {input.r1} 2> {log}"

    rule qc_dedup:
        input:  r1 = "DEDUP_FASTQ/{combo}{file}_{read}_dedup.fastq.gz"
        output: o1 = report("{outdir}{file}_{read}_dedup_fastqc.zip", category="QC")
        log:    "LOGS/{outdir}{file}_{read}_fastqc_dedup.log"
        conda:  "nextsnakes/envs/"+QCENV+".yaml"
        threads: MAXTHREAD
        params:  qpara = lambda wildcards: ' '.join("{!s} {!s}".format(key,val) for (key,val) in tool_params(SAMPLES[0], None ,config, 'QC', QCENV)['OPTIONS'][0].items())
        shell: "OUT=$(dirname {output.o1});fastqc --quiet -o $OUT -t {threads} --noextract {params.qpara} -f fastq {input.r1} 2> {log}"

    rule multiqc:
        input:  expand(rules.qc_raw.output.o1, rawfile=list(SAMPLES), read=['R1','R2']),
                expand(rules.qc_dedup.output.o1, file=samplecond(SAMPLES,config), read=['R1','R2'])
        output: html = report("{moutdir}DEDUP_RAW/{condition}/multiqc_report.html", category="QC"),
                tmp = temp("{moutdir}DEDUP_RAW/{condition}/tmp"),
                lst = "{moutdir}DEDUP_RAW/{condition}/qclist.txt"
        log:    "LOGS/{outdir}{condition}_multiqc_trimmed_raw.log"
        conda:  "nextsnakes/envs/"+QCENV+".yaml"
        threads: 1
        shell:  "OUT=$(dirname {output.html}); for i in {input};do echo $(dirname \"${{i}}\") >> {output.tmp};done; cat {output.tmp} |sort -u > {output.lst};export LC_ALL=en_US.utf8; export LC_ALL=C.UTF-8; multiqc -f --exclude picard --exclude gatk -k json -z -s -o $OUT -l {output.lst} 2> {log}"

else:
    rule qc_raw:
        input:  r1 = "FASTQ/{rawfile}.fastq.gz"
        output: o1 = report("{outdir}{rawfile}_fastqc.zip", category="QC")
        log:    "LOGS/{outdir}{rawfile}_fastqc_raw.log"
        conda:  "nextsnakes/envs/"+QCENV+".yaml"
        threads: MAXTHREAD
        params:  qpara = lambda wildcards: ' '.join("{!s} {!s}".format(key,val) for (key,val) in tool_params(SAMPLES[0], None ,config, 'QC', QCENV)['OPTIONS'][0].items())
        shell: "OUT=$(dirname {output.o1});fastqc --quiet -o $OUT -t {threads} --noextract {params.qpara} -f fastq {input.r1} 2> {log}"

    rule qc_dedup:
        input:  r1 = "DEDUP_FASTQ/{combo}{file}_dedup.fastq.gz"
        output: o1 = report("{outdir}{file}_dedup_fastqc.zip", category="QC")
        log:    "LOGS/{outdir}{file}_fastqc_dedup.log"
        conda:  "nextsnakes/envs/"+QCENV+".yaml"
        threads: MAXTHREAD
        params:  qpara = lambda wildcards: ' '.join("{!s} {!s}".format(key,val) for (key,val) in tool_params(SAMPLES[0], None ,config, 'QC', QCENV)['OPTIONS'][0].items())
        shell: "OUT=$(dirname {output.o1});fastqc --quiet -o $OUT -t {threads} --noextract {params.qpara} -f fastq {input.r1} 2> {log}"

    rule multiqc:
        input: expand(rules.qc_raw.output.o1, rawfile=list(SAMPLES)),
		       expand(rules.qc_dedup.output.o1, file=samplecond(SAMPLES,config))
        output: html = report("{moutdir}DEDUP_RAW/{condition}/multiqc_report.html", category="QC"),
                tmp = temp("{moutdir}DEDUP_RAW/{condition}/tmp"),
                lst = "{moutdir}DEDUP_RAW/{condition}/qclist.txt"
        log:    "LOGS/{outdir}{condition}_multiqc_trimmed_raw.log"
        conda:  "nextsnakes/envs/"+QCENV+".yaml"
        threads: 1
        shell:  "OUT=$(dirname {output.html}); for i in {input};do echo $(dirname \"${{i}}\") >> {output.tmp};done; cat {output.tmp} |sort -u > {output.lst};export LC_ALL=en_US.utf8; export LC_ALL=C.UTF-8; multiqc -f --exclude picard --exclude gatk -k json -z -s -o $OUT -l {output.lst} 2> {log}"
