"""Prepares the data for a machine learning algorithm"""

from pandas import concat, DataFrame, get_dummies, factorize, read_csv, Series
from numpy import concatenate, ndarray, nanmin, nanmax
# noinspection PyUnresolvedReferences
from sklearn.experimental import enable_iterative_imputer
# noinspection PyUnresolvedReferences,PyProtectedMember
from sklearn.impute import IterativeImputer, SimpleImputer


class CleanDataObject:
    """Object containing the data necessary to save a processed data set to disk"""

    def __init__(self, data: DataFrame, col_types: DataFrame, target_col: str):
        self.data: DataFrame = data
        self.col_types: DataFrame = col_types
        self.target_col: str = target_col


def get_cols_by_type(data_set: DataFrame, data_types: DataFrame, col_type: str) -> tuple:
    """Gets the columns and column names of a given type"""

    col_bools: Series = data_types.loc[0] == col_type
    cols: Series = data_types[col_bools.index[col_bools]]
    cols: list = list(cols)
    data: DataFrame = data_set[cols]
    return data, cols


def normalize(df: DataFrame) -> DataFrame:
    """Normalizes numeric columns in a data frame"""

    df: DataFrame = (df - df.min(axis=0)) / (df.max(axis=0) - df.min(axis=0))
    return df


def clean_nominal_data(data_set: DataFrame, data_types: DataFrame):
    """Process the nominal data"""

    nominal_data, nominal_cols = get_cols_by_type(data_set=data_set, data_types=data_types, col_type='nominal')

    # Impute unknown nominal values
    imputer: SimpleImputer = SimpleImputer(strategy='most_frequent', verbose=2)
    # noinspection PyUnresolvedReferences
    nominal_data: ndarray = nominal_data.to_numpy()
    nominal_data: ndarray = imputer.fit_transform(nominal_data)
    nominal_data: DataFrame = DataFrame(nominal_data, columns=nominal_cols)

    # Ordinal encode each column to save space
    for col_name in nominal_cols:
        col: Series = nominal_data[col_name]
        col, _ = factorize(col)
        del nominal_data[col_name]
        nominal_data.insert(loc=0, column=col_name, value=col)

    return nominal_data, nominal_cols


def clean_numeric_data(
    data_set: DataFrame, data_types: DataFrame, nominal_data: DataFrame, nominal_cols: list, targets: DataFrame,
    impute_seed=0, max_iter=1, n_nearest_features=350
) -> DataFrame:
    """Processes the numeric data"""

    # One hot encode the nominal values for the purpose of imputing unknown real values with a more sophisticated method
    one_hot_nominal_data: DataFrame = get_dummies(nominal_data, columns=nominal_cols, dummy_na=False)
    one_hot_targets: DataFrame = get_dummies(targets, columns=list(targets), dummy_na=False)

    # Get the numeric columns and column names
    numeric_data, numeric_cols = get_cols_by_type(data_set=data_set, data_types=data_types, col_type='numeric')

    # Normalize the numeric columns
    numeric_data: DataFrame = normalize(df=numeric_data)

    n_numeric_cols: int = numeric_data.shape[1]

    # Combine the nominal columns with the numeric so the nominal columns can be used in the imputation
    data_to_impute: ndarray = concatenate(
        [numeric_data.to_numpy(), one_hot_nominal_data.to_numpy(), one_hot_targets.to_numpy()], axis=1
    )

    # Impute missing numeric values
    imputer: IterativeImputer = IterativeImputer(
        verbose=2, random_state=impute_seed, max_iter=max_iter, max_value=nanmax(data_to_impute),
        min_value=nanmin(data_to_impute), n_nearest_features=n_nearest_features
    )
    imputed_data: ndarray = imputer.fit_transform(data_to_impute)

    # Separate the imputed numeric columns from the nominal columns that helped impute
    numeric_data: ndarray = imputed_data[:, :n_numeric_cols]

    numeric_data: DataFrame = DataFrame(data=numeric_data, columns=numeric_cols)
    return numeric_data


def clean_data(data_path: str, data_types_path: str) -> CleanDataObject:
    """Main function of this module"""

    target_col: str = 'CDCOMMUN'

    # Load in the raw data set and the table that indicates the data type of each column
    data_set: DataFrame = read_csv(data_path, low_memory=False)
    data_types: DataFrame = read_csv(data_types_path)

    # Remove rows with unknown targets
    data_set: DataFrame = data_set[data_set[target_col].notna()].reset_index()

    # Separate the targets
    targets: Series = data_set.loc[:, target_col].copy()
    del data_set[target_col]
    del data_types[target_col]

    # Combine the highest target category with the second highest category
    max_cat: float = targets.max()
    targets[targets == max_cat] = max_cat - 1

    # Ordinal encode the targets
    targets, _ = factorize(targets)

    targets: DataFrame = DataFrame(targets, columns=[target_col])

    # Process the nominal columns
    nominal_data, nominal_cols = clean_nominal_data(data_set=data_set, data_types=data_types)

    # Process the numeric columns
    numeric_data: DataFrame = clean_numeric_data(
        data_set=data_set, data_types=data_types, nominal_data=nominal_data, nominal_cols=nominal_cols, targets=targets
    )

    # Combine the processed nominal data with the processed numeric data and the targets
    data: DataFrame = concat([numeric_data, nominal_data, targets], axis=1)

    return CleanDataObject(data=data, col_types=data_types, target_col=target_col)
