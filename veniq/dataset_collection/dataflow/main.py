import os
from argparse import ArgumentParser

import d6tcollect
import d6tflow

from veniq.dataset_collection.dataflow.collectEM import TaskFindEM
from veniq.dataset_collection.dataflow.preprocess import TaskAggregatorJavaFiles

d6tcollect.submit = False

if __name__ == '__main__':
    system_cores_qty = os.cpu_count() or 1
    parser = ArgumentParser()
    parser.add_argument(
        "-d",
        "--dir",
        required=True,
        help="File path to JAVA source code for methods augmentations"
    )
    parser.add_argument(
        "-o", "--output",
        help="Path for file with output results",
        default='augmented_data'
    )
    parser.add_argument(
        "--jobs",
        "-j",
        type=int,
        default=system_cores_qty - 1,
        help="Number of processes to spawn. "
             "By default one less than number of cores. "
             "Be careful to raise it above, machine may stop responding while creating dataset.",
    )
    parser.add_argument(
        "-z", "--zip",
        action='store_true',
        help="To zip input and output files."
    )
    parser.add_argument(
        "-s", "--small_dataset_size",
        help="Number of files in small dataset",
        default=100,
        type=int,
    )

    args = parser.parse_args()
    d6tflow.preview(
        TaskFindEM(
            dir_to_search=args.dir,
            dir_to_save=args.output,
            system_cores_qty=args.jobs))
    d6tflow.run(
        TaskFindEM(
            dir_to_search=args.dir,
            dir_to_save=args.output,
            system_cores_qty=args.jobs
        ))
    data = TaskFindEM(
            dir_to_search=args.dir,
            dir_to_save=args.output,
            system_cores_qty=args.jobs).outputLoad(cached=False)

    print(data)
