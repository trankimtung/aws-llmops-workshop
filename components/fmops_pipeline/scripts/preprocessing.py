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
# import sys
# os.system("pip install -U 'datasets==2.16.1'")
from datasets import load_dataset, DatasetDict


def load(dataset_name="cnn_dailymail", config="3.0.0"):
    dataset = load_dataset(dataset_name, config)
    return dataset

def process(dataset, input_feature_name='input', output_feature_name='output'):
    dataset = dataset.remove_columns(['id'])
    dataset = dataset.rename_columns({'article': input_feature_name, 'highlights': output_feature_name})
    dataset = dataset.shuffle(seed=123)
    return dataset

def clip_text(dataset):
    def clip(example, feature_name='input', max_char_length=5000):
        example[feature_name] = example[feature_name][:max_char_length]
        return example
    
    return dataset.map(clip)

def sample(dataset, sample_size):
    train = dataset['train'].select(range(sample_size))
    test = dataset['test'].select(range(sample_size))
    validation = dataset['validation'].select(range(sample_size))
    return DatasetDict({
        'train': train,
        'test': test,
        'validation': validation
    })

def save(dataset, path):
    dataset['train'].to_json(os.path.join(path,'train','data.jsonl'))
    dataset['test'].to_json(os.path.join(path,'test','data.jsonl'))
    dataset['validation'].to_json(os.path.join(path,'validation','data.jsonl'))

if __name__ == '__main__':
    output_path = '/opt/ml/processing/output'
    
    dataset = load("cnn_dailymail", "3.0.0")
    dataset = process(dataset,'input','output')
    dataset = sample(dataset, sample_size=1)
    dataset = clip_text(dataset)
    print("Saving datasets to S3 ...")
    save(dataset, output_path)
    print("Done!")
