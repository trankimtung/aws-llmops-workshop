""" 
MIT No Attribution

Copyright 2023 Amazon.com, Inc. and its affiliates. All Rights Reserved.

Permission is hereby granted, free of charge, to any person obtaining a copy of this
software and associated documentation files (the "Software"), to deal in the Software
without restriction, including without limitation the rights to use, copy, modify,
merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

import os
import json
import logging

import pandas as pd

from pathlib import Path

logger = logging.getLogger("sagemaker")
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())

def save(save_path, results):
    output_path = os.path.join(save_path, "evaluation_report.json")
    with open(output_path, "w") as f:
        json.dump(results, f)
    logger.info(f"Results saved to {output_path}")


if __name__=="__main__":
    data_path = "/opt/ml/processing/input/data/"
    save_path = "/opt/ml/processing/output/data/"
    job_arn = os.environ["JOB_ARN"]
    val_artifact = f"{data_path}model-customization-job-{job_arn.split('/')[-1]}/validation_artifacts/post_fine_tuning_validation/validation/validation_metrics.csv"
    logger.info(f"Reading validation metrics from {val_artifact} ...")
    df = pd.read_csv(val_artifact)
    validation_results = {
        "Loss": df.iloc[-1][-2],
        "Perplexity": df.iloc[-1][-1]
    }
    logger.info(f"Results: {validation_results}")
    logger.info("Saving results ...")
    save(save_path, validation_results)
    logger.info("Done!")