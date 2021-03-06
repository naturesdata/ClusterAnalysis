"""Main module of this repository: Parses the arguments and calls the chosen handler"""

from argparse import ArgumentParser, Namespace
import sys

from handler.debug_datasets import debug_datasets_handler
from handler.combine import combine_handler
from handler.cluster import cluster_handler
from handler.arff import arff_handler
from handler.feat_select import feat_select_handler
from handler.pipeline import pipeline_handler
from handler.best_clustering import best_clustering_handler
from handler.counts import counts_handler
from handler.plot_clustering import plot_clustering_handler
from handler.utils import DEBUG_IDENTIFIER


def add_do_debug_arg(parser: ArgumentParser):
    """Adds the do-debug argument to a parser"""

    parser.add_argument(
        '--do-debug', required=False, action='store_true',
        help='Whether we are currently debugging or not'
    )


def add_cohort_arg(parser: ArgumentParser):
    """Adds the cohort argument to a parser"""

    parser.add_argument(
        '--cohort', type=str, required=True,
        help='Whether the cohort is ADNI or ANM; choices: adni, anm'
    )


def add_iteration_arg(parser: ArgumentParser):
    """Adds the iteration argument to a parser"""

    parser.add_argument(
        '--iteration', type=int, required=True,
        help='The clustering iteration (i.e. how many clusterings have been made so far)'
    )


def add_dataset_arg(parser: ArgumentParser):
    """Adds the target column argument to a parser"""

    parser.add_argument(
        '--dataset', type=str, required=True,
        help='The data set to clean or cluster'
    )


def add_cluster_method_arg(parser: ArgumentParser):
    """Adds the cohort argument to a parser"""

    parser.add_argument(
        '--cluster-method', type=str, required=True,
        help='Which clustering method to use; choices: rbf, nearest_neighbors'
    )


def add_n_kept_feats_arg(parser: ArgumentParser):
    """Adds the number of kept features argument to the parser"""

    parser.add_argument(
        '--n-kept-feats', type=int, required=False,
        help='The number of features that have been kept. Exclude argument to use all the features'
    )


def add_n_clusters_arg(parser: ArgumentParser):
    """Adds the number of clusters argument to the parser"""

    parser.add_argument(
        '--n-clusters', type=int, required=True,
        help='The number of clusters to use'
    )


def add_clustering_path_arg(parser: ArgumentParser):
    """Adds the clustering path argument to the parser"""

    parser.add_argument(
        '--clustering-path', type=str, required=True,
        help='path to a clustering.'
    )


def add_file_path_args(parser: ArgumentParser):
    """Adds the arguments that are used for constructing file paths to data"""

    add_cohort_arg(parser=parser)
    add_iteration_arg(parser=parser)
    add_dataset_arg(parser=parser)
    add_n_kept_feats_arg(parser=parser)
    add_n_clusters_arg(parser=parser)
    add_cluster_method_arg(parser=parser)


def parse_args(argv) -> Namespace:
    """Gets the arguments for this repo"""

    parser: ArgumentParser = ArgumentParser()

    subparsers = parser.add_subparsers(dest='handler_type', title='handler_type')
    subparsers.required = True

    # Configure the debug-datasets handler
    debug_datasets_parser: ArgumentParser = subparsers.add_parser('debug-datasets')
    add_cohort_arg(parser=debug_datasets_parser)
    add_dataset_arg(parser=debug_datasets_parser)

    # Configure the combine handler
    combine_parser: ArgumentParser = subparsers.add_parser('combine')
    add_cohort_arg(parser=combine_parser)
    add_dataset_arg(parser=combine_parser)
    combine_parser.add_argument(
        '--mri-path', type=str, required=True, nargs='?', default=None,
        help='path the feature-selected MRI data to combine with the rest of the data. If not set, takes full data set.'
    )
    add_do_debug_arg(parser=combine_parser)

    # Configure the cluster handler
    cluster_parser: ArgumentParser = subparsers.add_parser('cluster')
    add_file_path_args(parser=cluster_parser)
    add_do_debug_arg(parser=cluster_parser)

    # Configure the arff handler
    arff_parser: ArgumentParser = subparsers.add_parser('arff')
    add_file_path_args(parser=arff_parser)
    add_do_debug_arg(parser=arff_parser)
    arff_parser.add_argument(
        '--clustering-score', type=float, required=True,
        help='The clustering score of the previous clustering'
    )

    # Configure the feat-select handler
    feat_select_parser: ArgumentParser = subparsers.add_parser('feat-select')
    add_file_path_args(parser=feat_select_parser)
    add_do_debug_arg(parser=feat_select_parser)

    # Configure the pipeline handler
    pipeline_parser: ArgumentParser = subparsers.add_parser('pipeline')
    add_cohort_arg(parser=pipeline_parser)
    add_dataset_arg(parser=pipeline_parser)
    add_n_clusters_arg(parser=pipeline_parser)
    add_do_debug_arg(parser=pipeline_parser)
    add_cluster_method_arg(parser=pipeline_parser)
    pipeline_parser.add_argument(
        '--n-iterations', type=int, required=True,
        help='The number of iterations to reduce the features and re-cluster'
    )
    pipeline_parser.add_argument(
        '--do-continue', required=False, action='store_true',
        help='Whether to continue the pipeline from its latest iteration or not'
    )

    # Configure the best-clustering handler
    best_clustering_parser: ArgumentParser = subparsers.add_parser('best-clustering')
    add_cohort_arg(parser=best_clustering_parser)
    add_dataset_arg(parser=best_clustering_parser)

    # Configure the counts handler
    counts_parser: ArgumentParser = subparsers.add_parser('counts')
    add_clustering_path_arg(parser=counts_parser)
    counts_parser.add_argument(
        '--feat-map-path', type=str, required=True,
        help='path to the mapping from PTID to the variant to count.'
    )

    # Configure the plot clustering handler
    plot_clustering_parser: ArgumentParser = subparsers.add_parser('plot-clustering')
    add_clustering_path_arg(parser=plot_clustering_parser)
    plot_clustering_parser.add_argument(
        '--data-path', type=str, required=True,
        help='path to the data for the clustering plot.'
    )

    args: Namespace = parser.parse_args(argv)

    if hasattr(args, 'do_debug') and args.do_debug is True:
        assert hasattr(args, 'dataset')
        args.dataset = DEBUG_IDENTIFIER + args.dataset

    return args


def main(argv: list):
    """Main function of this module"""

    args: Namespace = parse_args(argv)

    if args.handler_type == 'debug-datasets':
        # Create a smaller version (less columns) of a data set for debugging
        debug_datasets_handler(cohort=args.cohort, dataset=args.dataset)
    elif args.handler_type == 'combine':
        # Combine the phenotypes, MRI data, and gene expression data into a single data set
        combine_handler(cohort=args.cohort, dataset=args.dataset, mri_path=args.mri_path, do_debug=args.do_debug)
    elif args.handler_type == 'cluster':
        # Obtain the cluster labels for the ARFF
        cluster_handler(
            cohort=args.cohort, dataset=args.dataset, cluster_method=args.cluster_method, n_clusters=args.n_clusters,
            iteration=args.iteration, n_kept_feats=args.n_kept_feats
        )
    elif args.handler_type == 'arff':
        # Make the ARFF to be used with WEKA
        arff_handler(
            cohort=args.cohort, dataset=args.dataset, cluster_method=args.cluster_method, n_clusters=args.n_clusters,
            iteration=args.iteration, n_kept_feats=args.n_kept_feats, clustering_score=args.clustering_score
        )
    elif args.handler_type == 'feat-select':
        # Select the features from the ARFF using WEKA
        feat_select_handler(
            cohort=args.cohort, dataset=args.dataset, cluster_method=args.cluster_method, n_clusters=args.n_clusters,
            iteration=args.iteration, n_kept_feats=args.n_kept_feats
        )
    elif args.handler_type == 'pipeline':
        pipeline_handler(
            cohort=args.cohort, dataset=args.dataset, cluster_method=args.cluster_method, n_clusters=args.n_clusters,
            n_iterations=args.n_iterations, do_continue=args.do_continue
        )
    elif args.handler_type == 'best-clustering':
        best_clustering_handler(cohort=args.cohort, dataset=args.dataset)
    elif args.handler_type == 'counts':
        counts_handler(clustering_path=args.clustering_path, feat_map_path=args.feat_map_path)
    elif args.handler_type == 'plot-clustering':
        plot_clustering_handler(clustering_path=args.clustering_path, data_path=args.data_path)


if __name__ == '__main__':
    # Pass in the program arguments minus the name of the program
    main(sys.argv[1:])
